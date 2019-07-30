#-*- coding=utf-8 -*-
import eventlet
eventlet.monkey_patch()
import os
import traceback
from flask_script import Manager, Shell
from app import create_app
from self_config import *
from config import *
from function import *
from redis import Redis,ConnectionPool

app = create_app()
manager = Manager(app)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


######################系统日志
app.logger.addHandler(ErrorLogger().file_handler)
app.logger.setLevel(logging.DEBUG)

######################初始化变量
if REDIS_PASSWORD!="":
    pool = ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,password=REDIS_PASSWORD)
else:
    pool = ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
tmp_rd=Redis(connection_pool=pool)
try:
    tmp_rd.set("allow_site",','.join(allow_site))
    tmp_rd.set("downloadUrl_timeout",downloadUrl_timeout)
    tmp_rd.set("password",password)
    tmp_rd.set("title",title)
    tmp_rd.set("tj_code",tj_code)
    tmp_rd.set("headCode",headCode)
    tmp_rd.set("footCode",footCode)
    tmp_rd.set("cssCode",cssCode)
    tmp_rd.set("robots",robots)
    tmp_rd.set("theme",theme)
    tmp_rd.set("title_pre",title_pre)
    tmp_rd.set("redirect_uri",redirect_uri)
    tmp_rd.set("BaseAuthUrl",BaseAuthUrl)
    tmp_rd.set("app_url",app_url)
    tmp_rd.set("ARIA2_HOST",ARIA2_HOST)
    tmp_rd.set("ARIA2_PORT",ARIA2_PORT)
    tmp_rd.set("ARIA2_SECRET",ARIA2_SECRET)
    tmp_rd.set("ARIA2_SCHEME",ARIA2_SCHEME)
    tmp_rd.set("MONGO_HOST",MONGO_HOST)
    tmp_rd.set("MONGO_PORT",MONGO_PORT)
    tmp_rd.set("MONGO_USER",MONGO_USER)
    tmp_rd.set("MONGO_PASSWORD",MONGO_PASSWORD)
    tmp_rd.set("MONGO_DB",MONGO_DB)
    tmp_rd.set("REDIS_HOST",REDIS_HOST)
    tmp_rd.set("REDIS_PORT",REDIS_PORT)
    tmp_rd.set("REDIS_PASSWORD",REDIS_PASSWORD)
    tmp_rd.set("REDIS_DB",REDIS_DB)
    tmp_rd.set("show_secret",show_secret)
    tmp_rd.set("default_sort",default_sort)
    tmp_rd.set("order_m",order_m)
    tmp_rd.set("encrypt_file",encrypt_file)
    tmp_rd.set("default_pan",default_pan)
    tmp_rd.set("admin_prefix",admin_prefix)
    tmp_rd.set("balance",balance)
    tmp_rd.set("thread_num",thread_num)
    tmp_rd.set("verify_url",verify_url)
    tmp_rd.set("show_doc",show_doc)
    tmp_rd.set("show_image",show_image)
    tmp_rd.set("show_video",show_video)
    tmp_rd.set("show_dash",show_dash)
    tmp_rd.set("show_audio",show_audio)
    tmp_rd.set("show_code",show_code)
    tmp_rd.set("show_redirect",show_redirect)
    config_path=os.path.join(config_dir,'self_config.py')
    with open(config_path,'r') as f:
        text=f.read()
    tmp_rd.set('users',re.findall('od_users=([\w\W]*})',text)[0])
    key='themelist'
    tmp_rd.delete(key)
except:
    print('\033[31m redis鉴权失败！请注意修改！\033[0m')
######################函数
app.jinja_env.globals['version']=config.version
app.jinja_env.globals['FetchData']=FetchData
app.jinja_env.globals['path_list']=path_list
app.jinja_env.globals['CanEdit']=CanEdit
app.jinja_env.globals['quote']=urllib.quote
app.jinja_env.globals['len']=len
app.jinja_env.globals['enumerate']=enumerate
app.jinja_env.globals['breadCrumb']=breadCrumb
app.jinja_env.globals['list']=list
app.jinja_env.globals['os']=os
app.jinja_env.globals['re']=re
app.jinja_env.globals['file_ico']=file_ico
app.jinja_env.globals['CutText']=CutText
app.jinja_env.globals['GetConfig']=GetConfig
app.jinja_env.globals['config_dir']=config_dir
app.jinja_env.globals['GetThemeList']=GetThemeList
app.jinja_env.globals['GenerateToken']=GenerateToken
app.jinja_env.globals['get_od_user']=get_od_user

################################################################################
#####################################启动#######################################
################################################################################
if __name__ == '__main__':
    manager.run()





