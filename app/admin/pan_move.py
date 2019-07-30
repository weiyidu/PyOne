#-*- coding=utf-8 -*-
from base_view import *
import time

###########################################网盘管理
@admin.route('/panmove',methods=['GET','POST'])
def panmove():
    if request.method=='POST':
        action=request.form.get('action')
        taskid=request.form.get('taskid')
        subid=request.form.get('subid')
        if action=='task':
            cmd=u'nohup python {} ReStartMove {} &'.format(os.path.join(config_dir,'function.py'),taskid)
            subprocess.Popen(cmd,shell=True)
            msg='重启成功'
            retdata={'msg':msg}
            return jsonify(retdata)
        elif action=='subtask':
            cmd=u'nohup python {} StartMoveOne {} {} &'.format(os.path.join(config_dir,'function.py'),taskid,subid)
            subprocess.Popen(cmd,shell=True)
            msg='重启成功'
            retdata={'msg':msg}
            return jsonify(retdata)
        elif action=='ClearHist':
            mon_db.tasks.delete_many({})
            mon_db.tasks_detail.delete_many({})
            retdata={'msg':'清空成功'}
            return jsonify(retdata)
        elif action=='deltask':
            mon_db.tasks.delete_many({'taskid':taskid})
            mon_db.tasks_detail.delete_many({'taskid':taskid})
            retdata={'msg':'删除成功'}
            return jsonify(retdata)
        elif action=='SetSuccessAll':
            task=mon_db.tasks.find_one({'taskid':taskid})
            mon_db.tasks.find_one_and_update({'taskid':taskid},{"$set":{'complete_num':task['total_num']}})
            mon_db.tasks_detail.update_many({'taskid':taskid},{'$set':{'status':'上传成功！'}})
            retdata={'msg':'强制成功'}
            return jsonify(retdata)
        elif action=='SetSuccess':
            task=mon_db.tasks.find_one({'taskid':taskid})
            mon_db.tasks.find_one_and_update({'taskid':taskid},{"$set":{'complete_num':min(task['complete_num']+1,task['total_num'])}})
            mon_db.tasks_detail.update_many({'taskid':taskid,'id':subid},{'$set':{'status':'上传成功！'}})
            retdata={'msg':'强制成功'}
            return jsonify(retdata)
    tasks=mon_db.tasks.find({})
    resp=MakeResponse(render_template('admin/pan_move/pan_move.html',tasks=tasks))
    return resp

@admin.route('/panmove/create',methods=['POST'])
def panmove_create():
    p,status=get_aria2()
    if not status:
        return jsonify({'status':False,'msg':p})
    pan_from=request.form.get('pan_from')
    pan_to=request.form.get('pan_to')
    user_to=request.form.get('user_to')
    if pan_from.endswith(':'):
        pan_from=pan_from+'/'
    if pan_to.endswith(':'):
        pan_to=pan_to+'/'
    if (not pan_from.endswith(':/')) and pan_from.endswith('/'):
        pan_from=pan_from[:-1]
    if (not pan_to.endswith(':/')) and pan_to.endswith('/'):
        pan_to=pan_to[:-1]
    if pan_from==pan_to:
        msg='想咋地？'
        retdata={'msg':msg}
    else:
        taskid=str(int(time.time()*1000))
        files=scan_file(pan_from)
        new_task=dict(
            taskid=taskid,
            pan_from=pan_from,
            pan_to=pan_to,
            complete_num=0,
            total_num=files.count(),
            status=''
            )
        mon_db.tasks.insert_one(new_task)
        retdata={'msg':'添加任务成功'}
        for idx,file in enumerate(files):
            id=taskid+'{}'.format(idx)
            from_path_prefix=file['path'].split(':/')[-1]
            to_path=pan_to+"/"+from_path_prefix
            to_path=to_path.replace('//','/').split(':')[-1].replace('/'+file['name'],'')
            info={
                'taskid':taskid,
                'id':id,
                'origin_name':file['name'],
                'origin_id':file['id'],
                'origin_user':file['user'],
                'to_user':user_to,
                'to_path':to_path,
                'status':''
            }
            mon_db.tasks_detail.insert_one(info)
        cmd=u'nohup python {} StartMove {} &'.format(os.path.join(config_dir,'function.py'),taskid)
        subprocess.Popen(cmd,shell=True)
        # StartMove(taskid)
    return jsonify(retdata)


@admin.route('/panmove/detail/<taskid>',methods=['GET','POST'])
def panmove_detail(taskid):
    tasks=mon_db.tasks_detail.find({'taskid':taskid})
    resp=MakeResponse(render_template('admin/pan_move/pan_detail.html',tasks=tasks,taskid=taskid))
    return resp
