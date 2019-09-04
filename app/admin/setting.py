#-*- coding=utf-8 -*-
from base_view import *

########admin
@admin.route('/',methods=['GET','POST'])
@admin.route('/setting',methods=['GET','POST'])
def setting():
    if request.method=='POST':
        if request.files.keys()!=[]:
            favicon=request.files['favicon']
            if favicon.content_length!=0:
                favicon.save('./app/static/img/favicon.ico')
        title=request.form.get('title','PyOne')
        theme=request.form.get('theme','material')
        title_pre=request.form.get('title_pre','index of ')

        set_config('title',title)
        set_config('title_pre',title_pre)
        set_config('theme',theme)

        # reload()
        redis_client.set('title',title)
        redis_client.set('title_pre',title_pre)
        redis_client.set('theme',theme)
        flash('更新成功')
        resp=MakeResponse(redirect(url_for('admin.setting')))
        return resp
    resp=MakeResponse(render_template('admin/setting/setting.html'))
    return resp


@admin.route('/sys_setting',methods=['GET','POST'])
def sys_setting():
    if request.method=='POST':
        downloadUrl_timeout=request.form.get('downloadUrl_timeout',5*60)
        allow_site=request.form.get('allow_site','no-referrer')
        #Aria2
        ARIA2_HOST=request.form.get('ARIA2_HOST','localhost').replace('https://','').replace('http://','')
        ARIA2_PORT=request.form.get('ARIA2_PORT',6800)
        ARIA2_SECRET=request.form.get('ARIA2_SECRET','')
        ARIA2_SCHEME=request.form.get('ARIA2_SCHEME','http')

        #MongoDB
        MONGO_HOST=request.form.get('MONGO_HOST','localhost').replace('https://','').replace('http://','')
        MONGO_PORT=request.form.get('MONGO_PORT',27017)
        MONGO_DB=request.form.get('MONGO_DB','three')
        MONGO_USER=request.form.get('MONGO_USER','')
        MONGO_PASSWORD=request.form.get('MONGO_PASSWORD','')
        #Redis
        REDIS_HOST=request.form.get('REDIS_HOST','localhost').replace('https://','').replace('http://','')
        REDIS_PORT=request.form.get('REDIS_PORT',6379)
        REDIS_DB=request.form.get('REDIS_DB','0')
        REDIS_PASSWORD=request.form.get('REDIS_PASSWORD','')

        order_m=request.form.get('order_m','desc')
        default_sort=request.form.get('default_sort','lastModtime')
        admin_prefix=request.form.get('admin_prefix','admin')
        balance=request.form.get('balance','False')
        show_secret=request.form.get('show_secret','no')
        encrypt_file=request.form.get('encrypt_file','no')
        thread_num=request.form.get('thread_num','5')
        verify_url=request.form.get('verify_url','False')

        set_config('downloadUrl_timeout',downloadUrl_timeout)
        set_config('allow_site',allow_site)
        #Aria2
        set_config('ARIA2_HOST',ARIA2_HOST)
        set_config('ARIA2_PORT',ARIA2_PORT)
        set_config('ARIA2_SECRET',ARIA2_SECRET)
        set_config('ARIA2_SCHEME',ARIA2_SCHEME)
        #MongoDB
        set_config('MONGO_HOST',MONGO_HOST)
        set_config('MONGO_PORT',MONGO_PORT)
        set_config('MONGO_DB',MONGO_DB)
        set_config('MONGO_USER',MONGO_USER)
        set_config('MONGO_PASSWORD',MONGO_PASSWORD)
        #Redis
        set_config('REDIS_HOST',REDIS_HOST)
        set_config('REDIS_PORT',REDIS_PORT)
        set_config('REDIS_DB',REDIS_DB)
        set_config('REDIS_PASSWORD',REDIS_PASSWORD)

        set_config('default_sort',default_sort)
        set_config('admin_prefix',admin_prefix)
        set_config('balance',balance)
        set_config('order_m',order_m)
        set_config('show_secret',show_secret)
        set_config('encrypt_file',encrypt_file)
        set_config('thread_num',thread_num)
        set_config('verify_url',verify_url)
        # reload()

        redis_client.set('downloadUrl_timeout',downloadUrl_timeout)
        redis_client.set('allow_site',','.join(allow_site.split(',')))
        #Aria2
        redis_client.set('ARIA2_HOST',ARIA2_HOST)
        redis_client.set('ARIA2_PORT',ARIA2_PORT)
        redis_client.set('ARIA2_SECRET',ARIA2_SECRET)
        redis_client.set('ARIA2_SCHEME',ARIA2_SCHEME)

        #MongoDB
        redis_client.set('MONGO_HOST',MONGO_HOST)
        redis_client.set('MONGO_PORT',MONGO_PORT)
        redis_client.set('MONGO_DB',MONGO_DB)
        redis_client.set('MONGO_USER',MONGO_USER)
        redis_client.set('MONGO_PASSWORD',MONGO_PASSWORD)

        #Redis
        redis_client.set('REDIS_HOST',REDIS_HOST)
        redis_client.set('REDIS_PORT',REDIS_PORT)
        redis_client.set('REDIS_DB',REDIS_DB)
        redis_client.set('REDIS_PASSWORD',REDIS_PASSWORD)

        redis_client.set('default_sort',default_sort)
        redis_client.set('admin_prefix',admin_prefix)
        redis_client.set('balance',balance)
        redis_client.set('order_m',order_m)
        redis_client.set('show_secret',show_secret)
        redis_client.set('encrypt_file',encrypt_file)
        redis_client.set('thread_num',thread_num)
        redis_client.set('verify_url',verify_url)
        flash('更新成功')
        resp=MakeResponse(redirect(url_for('admin.sys_setting')))
        return resp
    resp=MakeResponse(render_template('admin/setting/sys_setting.html'))
    return resp


@admin.route('/setCode',methods=['GET','POST'])
def setCode():
    if request.method=='POST':
        tj_code=request.form.get('tj_code','')
        headCode=request.form.get('headCode','')
        footCode=request.form.get('footCode','')
        cssCode=request.form.get('cssCode','')
        robots=request.form.get('robots','')
        #redis
        set_config('tj_code',tj_code)
        set_config('headCode',headCode)
        set_config('footCode',footCode)
        set_config('cssCode',cssCode)
        set_config('robots',robots)
        # reload()
        redis_client.set('tj_code',tj_code)
        redis_client.set('headCode',headCode)
        redis_client.set('footCode',footCode)
        redis_client.set('cssCode',cssCode)
        redis_client.set('robots',robots)
        flash('更新成功')
        resp=MakeResponse(render_template('admin/setCode/setCode.html'))
        return resp
    resp=MakeResponse(render_template('admin/setCode/setCode.html'))
    return resp


@admin.route('/show_setting',methods=['GET','POST'])
def show_setting():
    if request.method=='POST':
        action=request.form.get('action')
        redirect_file=request.form.get('redirect')
        if action is not None:
            set_config('redirect_file',redirect_file)
            redis_client.set('redirect_file',redirect_file)
            resp={'msg':'设置成功'}
            return jsonify(resp)
        show_redirect=request.form.get('show_redirect')
        set_config('show_redirect',show_redirect)
        redis_client.set('show_redirect',show_redirect)

        show_doc=request.form.get('show_doc')
        set_config('show_doc',show_doc)
        redis_client.set('show_doc',show_doc)

        show_image=request.form.get('show_image')
        set_config('show_image',show_image)
        redis_client.set('show_image',show_image)

        show_video=request.form.get('show_video')
        set_config('show_video',show_video)
        redis_client.set('show_video',show_video)

        show_dash=request.form.get('show_dash')
        set_config('show_dash',show_dash)
        redis_client.set('show_dash',show_dash)

        show_audio=request.form.get('show_audio')
        set_config('show_audio',show_audio)
        redis_client.set('show_audio',show_audio)

        show_code=request.form.get('show_code')
        set_config('show_code',show_code)
        redis_client.set('show_code',show_code)

        flash('更新成功')
        resp=MakeResponse(redirect(url_for('admin.show_setting')))
        return resp
    resp=MakeResponse(render_template('admin/setting/show_setting.html'))
    return resp
