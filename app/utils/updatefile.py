#-*- coding=utf-8 -*-
from header import *

def Dir(path=u'{}:/'.format(GetConfig('default_pan'))):
    user,n_path=path.split(':')
    od_type=get_value('od_type',user)
    app_url=GetAppUrl(user)
    InfoLogger().print_r('update {}\'s {} file'.format(user,n_path))
    if n_path=='/':
        if od_type=='nocn' or od_type is None or od_type==False:
            BaseUrl=app_url+u'v1.0/me/drive/root/children?expand=thumbnails'
        else:
            BaseUrl=app_url+u'_api/v2.0/me/drive/root/children?expand=thumbnails'
        mon_db.items.remove({'user':user})
        queue=Queue()
        g=GetItemThread(queue,user)
        g.GetItem(BaseUrl)
        queue=g.queue
    else:
        grandid=0
        parent=''
        if n_path.endswith('/'):
            n_path=n_path[:-1]
        if not n_path.startswith('/'):
            n_path='/'+n_path
        if mon_db.items.find_one({'grandid':0,'type':'folder','user':user}):
            parent_id=0
            for idx,p in enumerate(n_path[1:].split('/')):
                if parent_id==0:
                    parent_id=mon_db.items.find_one({'name':p,'grandid':idx,'user':user})['id']
                else:
                    parent_id=mon_db.items.find_one({'name':p,'grandid':idx,'parent':parent_id})['id']
                mon_db.items.delete_many({'parent':parent_id})
            grandid=idx+1
            parent=parent_id
        n_path=urllib.quote(n_path.encode('utf-8'))
        if od_type=='nocn' or od_type is None or od_type==False:
            BaseUrl=app_url+u'v1.0/me/drive/root:{}:/children?expand=thumbnails'.format(n_path)
        else:
            BaseUrl=app_url+u'_api/v2.0/me/drive/root:{}:/children?expand=thumbnails'.format(n_path)
        queue=Queue()
        g=GetItemThread(queue,user)
        g.GetItem(BaseUrl,grandid,parent,1)
        queue=g.queue
    if queue.qsize()==0:
        return
    tasks=[]
    for i in range(min(int(GetConfig('thread_num')),queue.qsize())):
        t=GetItemThread(queue,user)
        t.setDaemon(True)
        t.start()
        tasks.append(t)
    # for t in tasks:
    #     t.join()
    error_status=0
    while 1:
        for t in tasks:
            InfoLogger().print_r('thread {}\'s status {},qsize {}'.format(t.getName(),t.isAlive(),t.queue.qsize()))
            if t.isAlive()==False and t.queue.qsize()==0:
                tasks.pop(tasks.index(t))
            if t.queue.qsize()==0 and t.isAlive()==True:
                error_status+=1
                InfoLogger().print_r('error status times:{}'.format(error_status))
            else:
                error_status=1
            if error_status>=20 and t in tasks:
                InfoLogger().print_r('force kill thread:{}'.format(t.getName()))
                tasks.pop(tasks.index(t))
        if len(tasks)==0:
            InfoLogger().print_r(u'{} all thread stop!'.format(path))
            break
        time.sleep(1)
    # RemoveRepeatFile()


def UpdateFile(renew='all',fresh_user=None):
    tasks=[]
    InfoLogger().print_r('[* UpdateFile] user:{}, method:{}'.format(fresh_user,renew))
    if fresh_user is None or fresh_user=='':
        if renew=='all':
            InfoLogger().print_r('[* UpdateFile] delete local data;check file num:{}'.format(mon_db.items.count()))
            mon_db.items.delete_many({})
            clearRedis()
            for user,item in od_users.items():
                if item.get('client_id')!='':
                    share_path='{}:/'.format(user)
                    # Dir_all(share_path)
                    t=Thread(target=Dir,args=(share_path,))
                    t.start()
                    tasks.append(t)
            for t in tasks:
                t.join()
        else:
            for user,item in od_users.items():
                if item.get('client_id')!='':
                    share_path='{}:/'.format(user)
                    # Dir(share_path)
                    t=Thread(target=Dir,args=(share_path,))
                    t.start()
                    tasks.append(t)
            for t in tasks:
                t.join()
    else:
        if renew=='all':
            a=mon_db.items.delete_many({'user':fresh_user})
            clearRedis(fresh_user)
            share_path='{}:/'.format(fresh_user)
            t=Thread(target=Dir,args=(share_path,))
            t.start()
            t.join()
        else:
            share_path='{}:/'.format(fresh_user)
            t=Thread(target=Dir,args=(share_path,))
            t.start()
            t.join()
    while 1:
        for t in tasks:
            if t.isAlive()==False:
                tasks.pop(tasks.index(t))
        if len(tasks)==0:
            InfoLogger().print_r('all users update status is complete')
            break
        time.sleep(1)
    InfoLogger().print_r('update file success!')
    os.kill(os.getpid(), signal.SIGKILL)


def GetRootid(user=GetConfig('default_pan')):
    key='{}:rootid'.format(user)
    if redis_client.exists(key):
        return redis_client.get(key)
    else:
        app_url=GetAppUrl(user)
        od_type=get_value('od_type',user)
        token=GetToken(user=user)
        if od_type=='nocn' or od_type is None or od_type==False:
            url=app_url+u'v1.0/me/drive/root/'
        else:
            url=app_url+u'_api/v2.0/me/drive/root/'

        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        r=browser.get(url,headers=headers,verify=False)
        data=json.loads(r.content)
        redis_client.set(key,data['id'],3600)
        return data['id']


def FileExists(filename,user=GetConfig('default_pan')):
    app_url=GetAppUrl(user)
    od_type=get_value('od_type',user)
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    headers.update(default_headers)
    if od_type=='nocn' or od_type is None or od_type==False:
        search_url=app_url+"v1.0/me/drive/root/search(q='{}')".format(convert2unicode(filename))
    else:
        search_url=app_url+"_api/v2.0/me/drive/root/search(q='{}')".format(convert2unicode(filename))
    r=browser.get(search_url,headers=headers,verify=False)
    jsondata=json.loads(r.text)
    if len(jsondata['value'])==0:
        return False
    else:
        return True

def FileInfo(fileid,user=GetConfig('default_pan')):
    app_url=GetAppUrl(user)
    od_type=get_value('od_type',user)
    token=GetToken(user=user)
    headers={'Authorization':'bearer {}'.format(token),'Content-Type':'application/json'}
    headers.update(default_headers)
    if od_type=='nocn' or od_type is None or od_type==False:
        search_url=app_url+"v1.0/me/drive/items/{}".format(fileid)
    else:
        search_url=app_url+"_api/v2.0/me/drive/items/{}".format(fileid)
    r=browser.get(search_url,headers=headers,verify=False)
    jsondata=json.loads(r.text)
    return jsondata
