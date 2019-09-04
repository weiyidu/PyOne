#-*- coding=utf-8 -*-
from flask import make_response
import json
import requests
import collections
import sys
if sys.version_info[0]==3:
    import urllib.parse as urllib
else:
    import urllib
    reload(sys)
    sys.setdefaultencoding('utf-8')
import os
import re
import time
import shutil
import base64
import humanize
import StringIO
import subprocess
import signal
from dateutil.parser import parse
from Queue import Queue
from threading import Thread,Event
import redis
import traceback
from pymongo import uri_parser,MongoClient,ASCENDING,DESCENDING
from self_config import *
from aria2 import PyAria2
from logmanage import *
from ..extend import *



def GetConfig_pre(key):
    if key=='allow_site':
        value=','.join(allow_site)
    else:
        value=eval(key)
    return value

#######Mongodb & redis
mongo = MongoClient(host=GetConfig_pre('MONGO_HOST'),port=int(GetConfig_pre('MONGO_PORT')),connect=False)
mon_db=eval('mongo.{}'.format(GetConfig_pre('MONGO_DB')))
if GetConfig_pre('MONGO_PASSWORD')!='':
    mon_db.authenticate(GetConfig_pre('MONGO_USER'),GetConfig_pre('MONGO_PASSWORD'))
if GetConfig_pre('REDIS_PASSWORD')!='':
    pool=redis.ConnectionPool(host=GetConfig_pre('REDIS_HOST'),port=int(GetConfig_pre('REDIS_PORT')),db=GetConfig_pre('REDIS_DB'),password=GetConfig_pre('REDIS_PASSWORD'))
    redis_client=redis.Redis(connection_pool=pool)
else:
    pool=redis.ConnectionPool(host=GetConfig_pre('REDIS_HOST'),port=int(GetConfig_pre('REDIS_PORT')),db=GetConfig_pre('REDIS_DB'))
    redis_client=redis.Redis(connection_pool=pool)

#######授权链接
LoginUrl=BaseAuthUrl+'/common/oauth2/v2.0/authorize?response_type=code\
&client_id={client_id}&redirect_uri={redirect_uri}&scope=offline_access%20files.readwrite.all'
OAuthUrl=BaseAuthUrl+'/common/oauth2/v2.0/token'
AuthData='client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}&grant_type=authorization_code'
ReFreshData='client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token'

default_headers={'User-Agent':'ISV|PyOne|PyOne/4.0'}

browser=requests.Session()

#获取参数
def GetConfig(key):
    try:
        if key=='allow_site':
            value=redis_client.get('allow_site') if redis_client.exists('allow_site') else ','.join(allow_site)
        else:
            value=redis_client.get(key) if redis_client.exists(key) else eval(key)
        #这里是为了储存
        if key=='od_users'and isinstance(value,dict):
            config_path=os.path.join(config_dir,'self_config.py')
            with open(config_path,'r') as f:
                text=f.read()
            value=re.findall('od_users=([\w\W]*})',text)[0]
            # value=json.dumps(value)
        if not redis_client.exists(key):
            redis_client.set(key,value)
    except:
        if key=='allow_site':
            value=','.join(allow_site)
        else:
            value=eval(key)
        if key=='od_users'and isinstance(value,dict):
            config_path=os.path.join(config_dir,'self_config.py')
            with open(config_path,'r') as f:
                text=f.read()
            value=re.findall('od_users=([\w\W]*})',text)[0]
    #这里是为了转为字典
    if key=='od_users':
        config_path=os.path.join(config_dir,'self_config.py')
        with open(config_path,'r') as f:
            text=f.read()
        value=re.findall('od_users=([\w\W]*})',text)[0]
        value=json.loads(value)
    return value


############功能函数
def set_config(key,value,user=GetConfig('default_pan')):
    InfoLogger().print_r('set {}:{}'.format(key,value))
    config_path=os.path.join(config_dir,'self_config.py')
    if key in ['client_secret','client_id','share_path','other_name','od_type','app_url']:
        # old_kv=re.findall('"{}":.*{{[\w\W]*}}'.format(user),old_text)[0]
        # new_kv=re.sub('"{}":.*.*?,'.format(key),'"{}":"{}",'.format(key,value),old_kv,1)
        # new_text=old_text.replace(old_kv,new_kv,1)
        od_users[user][key]=value
        config_path=os.path.join(config_dir,'self_config.py')
        with open(config_path,'r') as f:
            old_text=f.read()
        with open(config_path,'w') as f:
            old_od=re.findall('od_users={[\w\W]*}',old_text)[0]
            new_od='od_users='+json.dumps(od_users,indent=4,ensure_ascii=False)
            new_text=old_text.replace(old_od,new_od,1)
            f.write(new_text)
        return
    with open(config_path,'r') as f:
        old_text=f.read()
    with open(config_path,'w') as f:
        if key=='allow_site':
            value=value.split(',')
            new_text=re.sub('{}=.*'.format(key),'{}={}'.format(key,value),old_text)
        elif key in ['tj_code','cssCode','headCode','footCode','robots']:
            new_text=re.sub('{}="""[\w\W]*?"""'.format(key),'{}="""{}"""'.format(key,value),old_text)
        else:
            new_text=re.sub('{}=.*'.format(key),'{}="{}"'.format(key,value),old_text)
        f.write(new_text)



#转字符串
def convert2unicode(string):
    return string.encode('utf-8')

#获取
def get_value(key,user=GetConfig('default_pan')):
    config_path=os.path.join(config_dir,'self_config.py')
    with open(config_path,'r') as f:
        text=f.read()
    kv=re.findall('"{}":.*{{[\w\W]*?}}'.format(user),text)[0]
    try:
        value=re.findall('"{}":.*"(.*?)"'.format(key),kv)[0]
        return value
    except:
        return 'nocn'

def GetName(id):
    key='name:{}'.format(id)
    if redis_client.exists(key):
        return redis_client.get(key)
    else:
        item=mon_db.items.find_one({'id':id})
        redis_client.set(key,item['name'])
        return item['name']

def GetPath(id):
    key='path:{}'.format(id)
    if redis_client.exists(key):
        return redis_client.get(key)
    else:
        item=mon_db.items.find_one({'id':id})
        redis_client.set(key,item['path'])
        return item['path']

def GetThemeList():
    tlist=[]
    theme_dir=os.path.join(config_dir,'app/templates/theme')
    lists=os.listdir(theme_dir)
    for l in lists:
        p=os.path.join(theme_dir,l)
        if os.path.isdir(p):
            tlist.append(l)
    return tlist


def open_json(filepath):
    token=False
    with open(filepath,'r') as f:
        try:
            token=json.load(f)
        except:
            for i in range(1,10):
                try:
                    token=json.loads(f.read()[:-i])
                except:
                    token=False
                if token!=False:
                    return token
    return token

def ReFreshToken(refresh_token,user=GetConfig('default_pan')):
    client_id=get_value('client_id',user)
    client_secret=get_value('client_secret',user)
    od_type=get_value('od_type',user)
    headers={'Content-Type':'application/x-www-form-urlencoded'}
    headers.update(default_headers)
    data=ReFreshData.format(client_id=client_id,redirect_uri=urllib.quote(redirect_uri),client_secret=urllib.quote(client_secret),refresh_token=refresh_token)
    if od_type=='cn':
        data+='&resource={}'.format(GetAppUrl(user))
    url=GetOAuthUrl(od_type)
    r=browser.post(url,data=data,headers=headers,verify=False)
    return json.loads(r.text)


def GetToken(Token_file='token.json',user=GetConfig('default_pan')):
    Token_file='{}_{}'.format(user,Token_file)
    token_path=os.path.join(data_dir,Token_file)
    if os.path.exists(token_path):
        token=open_json(token_path)
        try:
            if time.time()>float(token.get('expires_on')):
                InfoLogger().print_r('token timeout')
                refresh_token=token.get('refresh_token')
                token=ReFreshToken(refresh_token,user)
                if token.get('access_token'):
                    with open(token_path,'w') as f:
                        json.dump(token,f,ensure_ascii=False)
                else:
                    InfoLogger().print_r(token)
        except Exception as e:
            with open(os.path.join(data_dir,'{}_Atoken.json'.format(user)),'r') as f:
                Atoken=json.load(f)
            refresh_token=Atoken.get('refresh_token')
            token=ReFreshToken(refresh_token,user)
            token['expires_on']=str(time.time()+3599)
            if token.get('access_token'):
                with open(token_path,'w') as f:
                    json.dump(token,f,ensure_ascii=False)
            else:
                return False
        return token.get('access_token')
    else:
        return False

def GetAppUrl(user):
    od_type=get_value('od_type',user)
    if od_type=='nocn' or od_type is None or od_type==False:
        return 'https://graph.microsoft.com/'
    else:
        # return 'https://microsoftgraph.chinacloudapi.cn/'
        return get_value('app_url',user)


def GetLoginUrl(client_id,redirect_uri,od_type='nocn'):
    if od_type=='nocn' or od_type is None or od_type==False:
        return 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?response_type=code\
&client_id={client_id}&redirect_uri={redirect_uri}&scope=offline_access%20Files.ReadWrite.All%20Files.ReadWrite'.format(client_id=client_id,redirect_uri=redirect_uri)
    else:
        return 'https://login.partner.microsoftonline.cn/common/oauth2/authorize?response_type=code\
&client_id={client_id}&redirect_uri={redirect_uri}&scope=offline_access%20Files.ReadWrite.All%20Files.ReadWrite'.format(client_id=client_id,redirect_uri=redirect_uri)


def GetOAuthUrl(od_type):
    if od_type=='nocn' or od_type is None or od_type==False:
        return 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    else:
        return 'https://login.partner.microsoftonline.cn/common/oauth2/token'

def GetExt(name):
    try:
        return name.split('.')[-1]
    except:
        return 'file'

def date_to_char(date):
    return date.strftime('%Y/%m/%d')


def RemoveRepeatFile():
    """
    db.mon_db.items.aggregate([
        {
            $group:{_id:{id:'$id'},count:{$sum:1},dups:{$addToSet:'$_id'}}
        },
        {
            $match:{count:{$gt:1}}
        }

        ]).forEach(function(it){

             it.dups.shift();
            db.mon_db.items.remove({_id: {$in: it.dups}});

        });
    """
    deleteData=mon_db.items.aggregate([
    {'$group': {
        '_id': { 'id': "$id"},
        'uniqueIds': { '$addToSet': "$_id" },
        'count': { '$sum': 1 }
      }},
      { '$match': {
        'count': { '$gt': 1 }
      }}
    ]);
    first=True
    try:
        for d in deleteData:
            first=True
            for did in d['uniqueIds']:
                if not first:
                    mon_db.items.delete_one({'_id':did});
                first=False
    except Exception as e:
        exstr = traceback.format_exc()
        ErrorLogger().print_r(exstr)
        return

def get_aria2():
    try:
        p=PyAria2(host=GetConfig('ARIA2_HOST'),
                 port=GetConfig('ARIA2_PORT'),
                 secret=GetConfig('ARIA2_SECRET'),
                 scheme=GetConfig('ARIA2_SCHEME'))
        info=json.loads(p.getSessionInfo())[0]
        if info.get('error'):
            msg=info.get('error').get('message')
            if msg=='Unauthorized':
                msg='Aria2未验证！请检查Aria2信息！'
            return msg,False
        return p,True
    except Exception as e:
        return e,False


def _filesize(path):
    size=os.path.getsize(path)
    # InfoLogger().print_r('{}\'s size {}'.format(path,size))
    return size

def list_all_files(rootdir):
    import os
    _files = []
    if len(re.findall('[:#\|\?]+',rootdir))>0:
        newf=re.sub('[:#\|\?]+','',rootdir)
        shutil.move(rootdir,newf)
        rootdir=newf
    if rootdir.endswith(' '):
        shutil.move(rootdir,rootdir.rstrip())
        rootdir=rootdir.rstrip()
    if len(re.findall('/ ',rootdir))>0:
        newf=re.sub('/ ','/',rootdir)
        shutil.move(rootdir,newf)
        rootdir=newf
    flist = os.listdir(rootdir) #列出文件夹下所有的目录与文件
    for f in flist:
        path = os.path.join(rootdir,f)
        if os.path.isdir(path):
            _files.extend(list_all_files(path))
        if os.path.isfile(path):
            _files.append(path)
    return _files


def _file_content(path,offset,length):
    size=_filesize(path)
    offset,length=map(int,(offset,length))
    if offset>size:
        InfoLogger().print_r('offset must smaller than file size')
        return False
    length=length if offset+length<size else size-offset
    endpos=offset+length-1 if offset+length<size else size-1
    # InfoLogger().print_r("read file {} from {} to {}".format(path,offset,endpos))
    with open(path,'rb') as f:
        f.seek(offset)
        content=f.read(length)
    return content



def AddResource(data,user=GetConfig('default_pan')):
    #检查父文件夹是否在数据库，如果不在则获取添加
    grand_path=data.get('parentReference').get('path').replace('/drive/root:','') #空值或者/path
    try:
        grand_path=urllib.unquote(grand_path.encode('utf-8')).decode('utf-8')
    except:
        grand_path=grand_path
    if grand_path=='':
        parent_id=''
    else:
        g=GetItemThread(Queue(),user)
        parent_id=data.get('parentReference').get('id')
        if grand_path.startswith('/'):
            grand_path=grand_path[1:]
        if grand_path!='':
            parent_path='/'
            pid=''
            for idx,p in enumerate(grand_path.split('/')):
                parent=mon_db.items.find_one({'name':p,'grandid':idx,'parent':pid,'user':user})
                InfoLogger().print_r('[*AddResource] check parent path exists? user: {},name:{} ,parent id:{}; exists:{}'.format(user,p,pid,parent is not None))
                if parent is not None:
                    pid=parent['id']
                    parent_path='/'.join([parent_path,parent['name']])
                else:
                    parent_path=('/'.join([parent_path,p])).replace('//','/')
                    fdata=g.GetItemByPath(parent_path)
                    path=user+':/'+parent_path.replace('///','/')
                    path=path.replace('///','/').replace('//','/')
                    path=urllib.unquote(path).decode('utf-8')
                    InfoLogger().print_r('[*AddResource] parent path:{} is not exists; Add data in mongo:{}'.format(parent_path,path))
                    item={}
                    item['type']='folder'
                    item['user']=user
                    item['order']=0
                    item['name']=fdata.get('name')
                    item['id']=fdata.get('id')
                    item['size']=humanize.naturalsize(fdata.get('size'), gnu=True)
                    item['size_order']=fdata.get('size')
                    item['lastModtime']=date_to_char(parse(fdata['lastModifiedDateTime']))
                    item['grandid']=idx
                    item['parent']=pid
                    item['path']=path
                    mon_db.items.insert_one(item)
                    pid=fdata.get('id')
    #插入数据
    item={}
    item['type']=GetExt(data.get('name'))
    item['name']=data.get('name')
    item['user']=user
    item['id']=data.get('id')
    item['size']=humanize.naturalsize(data.get('size'), gnu=True)
    item['size_order']=data.get('size')
    item['lastModtime']=date_to_char(parse(data.get('lastModifiedDateTime')))
    item['parent']=parent_id
    if grand_path=='':
        path=user+':/'+convert2unicode(data['name'])
    else:
        path=user+':/'+grand_path+'/'+convert2unicode(data['name'])
    path=path.replace('//','/')
    path=urllib.unquote(path).decode('utf-8')
    grandid=len(path.split('/'))-2
    item['grandid']=grandid
    item['path']=path
    InfoLogger().print_r('AddResource: name:{};path:{};grandid:{}'.format(data.get('name'),path,grandid))
    if GetExt(data['name']) in ['bmp','jpg','jpeg','png','gif']:
        item['order']=3
    elif data['name']=='.password':
        item['order']=1
    else:
        item['order']=2
    mon_db.items.insert_one(item)


class GetItemThread(Thread):
    def __init__(self,queue,user):
        super(GetItemThread,self).__init__()
        self.insert_items=[]
        self.queue=queue
        self.user=user
        share_path=GetConfig('od_users').get(user).get('share_path')
        if share_path=='/':
            self.share_path=share_path
        else:
            sp=share_path
            if not sp.startswith('/'):
                sp='/'+share_path
            if sp.endswith('/') and sp!='/':
                sp=sp[:-1]
            self.share_path=sp

    def __del__(self):
        mon_db.items.insert_many(self.insert_items)

    def insert_new(self,item):
        self.insert_items.append(item)
        if len(self.insert_items)>=20:
            mon_db.items.insert_many(self.insert_items)
            self.insert_items=[]

    def run(self):
        while not self.queue.empty():
            time.sleep(0.5) #避免过快
            info=self.queue.get()
            url=info['url']
            grandid=info['grandid']
            parent=info['parent']
            trytime=info['trytime']
            self.GetItem(url,grandid,parent,trytime)
            if self.queue.empty():
                break

    def CheckPathSize(self,url):
        app_url=GetAppUrl(self.user)
        token=GetToken(user=self.user)
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        r=browser.get(url,headers=headers,timeout=10,verify=False)
        data=json.loads(r.content)
        if data.get('folder'):
            if data['name']!='root':
                folder=mon_db.items.find_one({'id':data['id'],'user':self.user})
                if folder['size_order']==int(data['size']): #文件夹大小未变化，不更新
                    InfoLogger().print_r(u'path:{},origin size:{},current size:{}--------no change'.format(data['name'],folder['size_order'],data['size']))
                    return

    def GetItem(self,url,grandid=0,parent='',trytime=1):
        app_url=GetAppUrl(self.user)
        od_type=get_value('od_type',self.user)
        token=GetToken(user=self.user)
        InfoLogger().print_r(u'[start] getting files from url {}'.format(url))
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        try:
            self.CheckPathSize(url.replace('children?expand=thumbnails',''))
            r=browser.get(url,headers=headers,timeout=10,verify=False)
            data=json.loads(r.content)
            if data.get('error'):
                InfoLogger().print_r('error:{}! waiting 180s'.format(data.get('error').get('message')))
                time.sleep(180)
                self.queue.put(dict(url=url,grandid=grandid,parent=parent,trytime=trytime))
                return
            values=data.get('value')
            if len(values)>0:
                for value in values:
                    item={}
                    if value.get('folder'):
                        folder=mon_db.items.find_one({'id':value['id'],'user':self.user})
                        if folder is not None:
                            if folder['size_order']==int(value['size']): #文件夹大小未变化，不更新
                                InfoLogger().print_r(u'path:{},origin size:{},current size:{}--------no change'.format(value['name'],folder['size_order'],value['size']))
                            else:
                                mon_db.items.delete_one({'id':value['id']})
                                item['type']='folder'
                                item['user']=self.user
                                item['order']=0
                                item['name']=convert2unicode(value['name'])
                                item['id']=convert2unicode(value['id'])
                                item['size']=humanize.naturalsize(value['size'], gnu=True)
                                item['size_order']=int(value['size'])
                                item['lastModtime']=date_to_char(parse(value['lastModifiedDateTime']))
                                item['grandid']=grandid
                                item['parent']=parent
                                grand_path=value.get('parentReference').get('path').replace('/drive/root:','')
                                if grand_path=='':
                                    path=convert2unicode(value['name'])
                                else:
                                    path=grand_path.replace(self.share_path,'',1)+'/'+convert2unicode(value['name'])
                                if path.startswith('/') and path!='/':
                                    path=path[1:]
                                if path=='':
                                    path=convert2unicode(value['name'])
                                path=urllib.unquote('{}:/{}'.format(self.user,path))
                                item['path']=path
                                # self.insert_new(item)
                                subfodler=mon_db.items.insert_one(item)
                                if value.get('folder').get('childCount')==0:
                                    continue
                                else:
                                    parent_path=value.get('parentReference').get('path').replace('/drive/root:','')
                                    path=convert2unicode(parent_path+'/'+value['name'])
                                    # path=urllib.quote(convert2unicode(parent_path+'/'+value['name']))
                                    if od_type=='nocn' or od_type is None or od_type==False:
                                        url=app_url+'v1.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
                                    else:
                                        url=app_url+'_api/v2.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
                                    self.queue.put(dict(url=url,grandid=grandid+1,parent=item['id'],trytime=1))
                        else:
                            mon_db.items.delete_one({'id':value['id']})
                            item['type']='folder'
                            item['user']=self.user
                            item['order']=0
                            item['name']=convert2unicode(value['name'])
                            item['id']=convert2unicode(value['id'])
                            item['size']=humanize.naturalsize(value['size'], gnu=True)
                            item['size_order']=int(value['size'])
                            item['lastModtime']=date_to_char(parse(value['lastModifiedDateTime']))
                            item['grandid']=grandid
                            item['parent']=parent
                            grand_path=value.get('parentReference').get('path').replace('/drive/root:','')
                            if grand_path=='':
                                path=convert2unicode(value['name'])
                            else:
                                path=grand_path.replace(self.share_path,'',1)+'/'+convert2unicode(value['name'])
                            if path.startswith('/') and path!='/':
                                path=path[1:]
                            if path=='':
                                path=convert2unicode(value['name'])
                            path=urllib.unquote('{}:/{}'.format(self.user,path))
                            item['path']=path
                            # self.insert_new(item)
                            subfodler=mon_db.items.insert_one(item)
                            if value.get('folder').get('childCount')==0:
                                continue
                            else:
                                parent_path=value.get('parentReference').get('path').replace('/drive/root:','')
                                path=convert2unicode(parent_path+'/'+value['name'])
                                # path=urllib.quote(convert2unicode(parent_path+'/'+value['name']))
                                if od_type=='nocn' or od_type is None or od_type==False:
                                    url=app_url+'v1.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
                                else:
                                    url=app_url+'_api/v2.0/me/drive/root:{}:/children?expand=thumbnails'.format(path)
                                self.queue.put(dict(url=url,grandid=grandid+1,parent=item['id'],trytime=1))
                    else:
                        if mon_db.items.find_one({'id':value['id']}) is not None: #文件存在
                            continue
                        else:
                            item['type']=GetExt(value['name'])
                            grand_path=value.get('parentReference').get('path').replace('/drive/root:','')
                            if grand_path=='':
                                path=convert2unicode(value['name'])
                            else:
                                path=grand_path.replace(self.share_path,'',1)+'/'+convert2unicode(value['name'])
                            if path.startswith('/') and path!='/':
                                path=path[1:]
                            if path=='':
                                path=convert2unicode(value['name'])
                            path=urllib.unquote('{}:/{}'.format(self.user,path))
                            item['path']=path
                            item['user']=self.user
                            item['name']=convert2unicode(value['name'])
                            item['id']=convert2unicode(value['id'])
                            item['size']=humanize.naturalsize(value['size'], gnu=True)
                            item['size_order']=int(value['size'])
                            item['lastModtime']=date_to_char(parse(value['lastModifiedDateTime']))
                            item['grandid']=grandid
                            item['parent']=parent
                            if GetExt(value['name']) in ['bmp','jpg','jpeg','png','gif']:
                                item['order']=3
                                key1='name:{}'.format(value['id'])
                                key2='path:{}'.format(value['id'])
                                redis_client.set(key1,value['name'])
                                redis_client.set(key2,path)
                            elif value['name']=='.password':
                                item['order']=1
                            else:
                                item['order']=2
                            # mon_db.items.insert_one(item)
                            self.insert_new(item)
            else:
                InfoLogger().print_r('{}\'s size is zero'.format(url))
            if data.get('@odata.nextLink'):
                self.queue.put(dict(url=data.get('@odata.nextLink'),grandid=grandid,parent=parent,trytime=1))
            InfoLogger().print_r(u'[success] getting files from url {}'.format(url))
        except Exception as e:
            exestr=traceback.format_exc()
            trytime+=1
            ErrorLogger().print_r(u'error to opreate GetItem("{}","{}","{}"),try times :{}, reason: {}'.format(url,grandid,parent,trytime,exestr))
            if trytime<=3:
                self.queue.put(dict(url=url,grandid=grandid,parent=parent,trytime=trytime))


    def GetItemByPath(self,path):
        app_url=GetAppUrl(self.user)
        token=GetToken(user=self.user)
        path=convert2unicode(path)
        od_type=get_value('od_type',self.user)
        if path=='' or path=='/':
            if od_type=='nocn' or od_type is None or od_type==False:
                url=app_url+u'v1.0/me/drive/root/'
            else:
                url=app_url+u'_api/v2.0/me/drive/root/'
        else:
            if od_type=='nocn' or od_type is None or od_type==False:
                url=app_url+u'v1.0/me/drive/root:{}:/'.format(path)
            else:
                url=app_url+u'_api/v2.0/me/drive/root:{}:/'.format(path)
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        r=browser.get(url,headers=headers,verify=False)
        data=json.loads(r.content)
        return data

    def GetItemByUrl(self,url):
        app_url=GetAppUrl(self.user)
        token=GetToken(user=self.user)
        headers={'Authorization': 'Bearer {}'.format(token)}
        headers.update(default_headers)
        r=browser.get(url,headers=headers,verify=False)
        data=json.loads(r.content)
        return data

def clearRedis(user=None):
    if user is not None:
        key_lists=['path:*','name:*','*has_item*','*root*','*:content']
    else:
        key_lists=['has_item*{}*'.format(user),'{}*root*'.format(user)]
    for k in key_lists:
        try:
            redis_client.delete(*redis_client.keys(k))
        except:
            'NoKey'

def CheckServer():
    mongo_cmd='lsof -i:27017 | grep LISTEN'
    redis_cmd='lsof -i:6379 | grep LISTEN'
    p1=subprocess.Popen(mongo_cmd,shell=True,stdout=subprocess.PIPE)
    p2=subprocess.Popen(redis_cmd,shell=True,stdout=subprocess.PIPE)
    r1=len(p1.stdout.readlines())
    r2=len(p2.stdout.readlines())
    msg=''
    if r1==0:
        msg+='<p><B>MongoDB未运行<B></p>'
    if r2==0:
        msg+='<p><B>Redis未运行<B></p>'
    p1.terminate()
    p2.terminate()
    if r1==0 or r2==0:
        return msg,False
    else:
        return msg,True

class TimeCalculator:
    """docstring for SpeedCalculator"""
    def __init__(self):
        self.starttime=time.time()

    def PassNow(self):
        return round(time.time()-self.starttime,3)

def CalcSpeed(length,timecost):
    raw_sp=length/timecost
    info={
        'kb':str(round(raw_sp/1024,1))+'KB/s',
        'mb':str(round(raw_sp/1024/1024,1))+'MB/s',
    }
    return info


def MakeResponse(content):
    resp=make_response(content)
    resp.headers['Cache-Control'] = 'no-cache,max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp
