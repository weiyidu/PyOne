#-*- coding=utf-8 -*-
from header import *
from upload import *
from common import *
from offdownload import *
import shutil


def scan_file(path):
    if (not path.endswith(':/')) and path.endswith('/'):
        path=path[:-1]
    files=mon_db.items.find({
        'path':re.compile(path+'/*')
        ,'type':{'$ne':'folder'}
    })
    return files

def Tasks_queue(taskid):
    tasks=mon_db.tasks_detail.find({'taskid':taskid})
    task_queue=Queue()
    for task in tasks:
        if task['status']!='上传成功！':
            info={
                'taskid':taskid,
                'id':task['id'],
                'origin_name':task['origin_name'],
                'origin_id':task['origin_id'],
                'origin_user':task['origin_user'],
                'to_user':task['to_user'],
                'to_path':task['to_path'],
            }
            task_queue.put(info)
    return task_queue


class MoveCls(Thread):
    """docstring for MoveCls"""
    def __init__(self, queue):
        super(MoveCls, self).__init__()
        self.queue = queue

    def run(self):
        while 1:
            info=self.queue.get()
            taskid=info['taskid']
            id=info['id']
            origin_id=info['origin_id']
            origin_user=info['origin_user']
            to_path=info['to_path']
            to_user=info['to_user']
            download_url=GetDownloadUrl(origin_id,origin_user)[0]
            download_and_upload(url=download_url,remote_dir=to_path,user=to_user,outerid=id)
            task=mon_db.tasks_detail.find_one({'id':id})
            parent_task=mon_db.tasks.find_one({'taskid':taskid})
            if task['status']=='上传成功！':
                new_info={'complete_num':parent_task['complete_num']+1}
                mon_db.tasks.find_one_and_update({'taskid':taskid},{'$set':new_info})
            if self.queue.empty():
                break


def StartMove(taskid,thread_num=5):
    tasks=[]
    queue=Tasks_queue(taskid)
    for i in range(thread_num):
        t=MoveCls(queue)
        t.start()
        tasks.append(t)
    for t in tasks:
        t.join()
    RemoveRepeatFile()


def ReStartMove(taskid,thread_num=5):
    task=mon_db.tasks.find_one({'taskid':taskid})
    pan_to=task['pan_to']
    files=scan_file(task['pan_from'])
    old_num=task['total_num']
    total_num=task['total_num']
    for idx,file in enumerate(files):
        id=taskid+'{}{}'.format(str(int(time.time()*1000))[-5:],idx)
        from_path_prefix=file['path'].split(':/')[-1]
        to_path=pan_to+"/"+from_path_prefix
        to_path=to_path.replace('//','/').split(':')[-1].replace('/'+file['name'],'')
        if mon_db.tasks_detail.find({'to_path':to_path}).count()==0:
            total_num+=1
            info={
                'taskid':taskid,
                'id':id,
                'origin_name':file['name'],
                'origin_id':file['id'],
                'origin_user':file['user'],
                'to_user':task['pan_to'],
                'to_path':to_path,
                'status':''
            }
            mon_db.tasks_detail.insert_one(info)
    mon_db.tasks.find_one_and_update({'taskid':taskid},{'$set':{'total_num':total_num}})
    cmd=u'nohup python {} StartMove {} &'.format(os.path.join(config_dir,'function.py'),taskid)
    subprocess.Popen(cmd,shell=True)


def StartMoveOne(taskid,subid):
    subtask=mon_db.tasks_detail.find_one({'taskid':taskid,'id':subid})
    queue=Queue()
    info={
        'taskid':taskid,
        'id':subid,
        'origin_name':subtask['origin_name'],
        'origin_id':subtask['origin_id'],
        'origin_user':subtask['origin_user'],
        'to_user':subtask['to_user'],
        'to_path':subtask['to_path'],
    }
    queue.put(info)
    t=MoveCls(queue)
    t.start()
    t.join()
