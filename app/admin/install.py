#-*- coding=utf-8 -*-
from base_view import *


###########################################安装
def check_mongo(host,port,user,password,db):
    try:
        mongo = MongoClient(host=host,port=int(port),connect=False,serverSelectionTimeoutMS=3)
        mon_db=eval('mongo.{}'.format(db))
        if GetConfig_pre('MONGO_PASSWORD')!='':
            try:
                mon_db.authenticate(user,password)
            except:
                return False
        try:
            mon_db.items.remove()
        except:
            return False
    except:
        return False
    return True

def check_redis(host,port,password,db):
    try:
        if password!='':
            pool=redis.ConnectionPool(host=host,port=int(port),db=db,password=password,socket_connect_timeout=3)
            redis_client=redis.Redis(connection_pool=pool)
        else:
            pool=redis.ConnectionPool(host=host,port=int(port),db=db,socket_connect_timeout=3)
            redis_client=redis.Redis(connection_pool=pool)
        try:
            redis_client.exists('test')
            return True
        except:
            return False
    except:
        return False




@admin.route('/install',methods=['POST','GET'])
def install():
    step=request.args.get('step',0,type=int)
    user=request.args.get('user','A')
    if request.method=='POST':
        if step==3:
            od_type=request.form.get('od_type','nocn')
            set_config('od_type',od_type,user)
        elif step==4:
            od_type=request.form.get('od_type','nocn')
            od_prefix=request.form.get('od_prefix')
            client_id=request.form.get('client_id')
            client_secret=request.form.get('client_secret')
            set_config('client_id',client_id,user)
            set_config('client_secret',client_secret,user)
            if od_type=='cn':
                set_config('app_url','https://{}-my.sharepoint.cn/'.format(od_prefix),user)
            login_url=GetLoginUrl(client_id=client_id,redirect_uri=GetConfig('redirect_uri'),od_type=od_type)
        else:
            client_secret=request.form.get('client_secret')
            client_id=request.form.get('client_id')
            code=request.form.get('code')
            od_type=request.form.get('od_type','nocn')
            #授权
            headers={'Content-Type':'application/x-www-form-urlencoded'}
            headers.update(default_headers)
            data=AuthData.format(client_id=client_id,redirect_uri=urllib.quote(GetConfig('redirect_uri')),client_secret=urllib.quote(client_secret),code=code)
            if od_type=='cn':
                data+='&resource=00000003-0000-0ff1-ce00-000000000000'
            url=GetOAuthUrl(od_type)
            r=requests.post(url,data=data,headers=headers,verify=False)
            Atoken=json.loads(r.text)
            if Atoken.get('access_token'):
                with open(os.path.join(config_dir,'data/{}_Atoken.json'.format(user)),'w') as f:
                    json.dump(Atoken,f,ensure_ascii=False)
                refresh_token=Atoken.get('refresh_token')
                token=ReFreshToken(refresh_token,user)
                if token.get('error'):
                    return jsonify(token)
                token['expires_on']=str(time.time()+3599)
                with open(os.path.join(config_dir,'data/{}_token.json'.format(user)),'w') as f:
                    json.dump(token,f,ensure_ascii=False)
                with open(os.path.join(config_dir,'.install'),'w') as f:
                    f.write('4.0')
                config_path=os.path.join(config_dir,'self_config.py')
                with open(config_path,'r') as f:
                    text=f.read()
                redis_client.set('users',re.findall('od_users=([\w\W]*})',text)[0])
                return make_response('<h1>授权成功!<br>请先在<B><a href="/{}/cache" target="_blank">后台-更新列表</a></B>，全量更新数据<br>然后<a href="/?t={}">点击进入首页</a></h1><br>'.format(GetConfig('admin_prefix'),time.time()))
            else:
                return jsonify(Atoken)
    if step==0:
        resp=MakeResponse(render_template('admin/install/install_mongo.html',step=step,cur_user=user))
    elif step==1:
        resp=MakeResponse(render_template('admin/install/install_redis.html',step=step,cur_user=user))
    elif step==2:
        resp=MakeResponse(render_template('admin/install/install_choose_type.html',step=step,cur_user=user))
    elif step==3:
        resp=MakeResponse(render_template('admin/install/install_fetch_key.html',step=step,cur_user=user,od_type=od_type))
    elif step==4:
        resp=render_template('admin/install/install_login.html',client_secret=client_secret,client_id=client_id,login_url=login_url,cur_user=user,od_type=od_type)
    return resp

@admin.route('/install/test_config',methods=['POST'])
def test_config():
    soft=request.form.get('soft')
    host=request.form.get('host')
    port=request.form.get('port')
    user=request.form.get('user')
    password=request.form.get('password')
    db=request.form.get('db')
    resp={}
    if soft=='mongo':
        if check_mongo(host,port,user,password,db):
            set_config('MONGO_HOST',host)
            set_config('MONGO_PORT',port)
            set_config('MONGO_USER',user)
            set_config('MONGO_PASSWORD',password)
            set_config('MONGO_DB',db)
            resp['msg']='MongoDB信息检查正确！'
            resp['code']=1
        else:
            resp['msg']='MongoDB信息错误！'
            resp['code']=0
    else:
        if check_redis(host,port,password,db):
            set_config('REDIS_HOST',host)
            set_config('REDIS_PORT',port)
            set_config('REDIS_PASSWORD',password)
            set_config('REDIS_DB',db)
            resp['msg']='Redis信息检查正确！'
            resp['code']=1
        else:
            resp['msg']='Redis信息错误！'
            resp['code']=0
    return jsonify(resp)

###########################################卸载
@admin.route('/uninstall',methods=['POST'])
def uninstall():
    type_=request.form.get('type')
    if type_=='mongodb':
        mon_db.items.remove()
        mon_db.down_db.remove()
        msg='删除mongodb数据成功'
    elif type_=='redis':
        redis_client.flushdb()
        msg='删除redis数据成功'
    elif type_=='directory':
        subprocess.Popen('rm -rf {}/data/*.json'.format(config_dir),shell=True)
        subprocess.Popen('rm -rf {}/.install'.format(config_dir),shell=True)
        msg='删除网站数据成功'
    else:
        msg='数据已清除！如果需要删除目录请运行:rm -rf {}'.format(config_dir)
    ret={'msg':msg}
    return jsonify(ret)
