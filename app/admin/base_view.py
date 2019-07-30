#-*- coding=utf-8 -*-
from flask import render_template,redirect,abort,make_response,jsonify,request,url_for,Response,session,flash
from flask_sqlalchemy import Pagination
from self_config import *
from ..utils import *
from ..extend import *
from .. import *
from . import admin
import os
import io
import re
import base64
import subprocess
import random
import string
import math
import urllib
import signal
import time
from shelljob import proc
import urllib3

urllib3.disable_warnings()


##全局_pid
global _pid
_pid=None

############视图函数
@admin.before_request
def before_request():
    if request.endpoint.startswith('admin') and request.endpoint!='admin.login' and session.get('login') is None: #and request.endpoint!='admin.install'
        return redirect(url_for('admin.login'))


########web console
@admin.route('/web_console')
def web_console():
    g = proc.Group()
    action=request.args.get('action')
    allow_action=['UpdateFile','UploadDir','Upload']
    if action not in allow_action:
        return make_response('error')
    if action in ['UploadDir','Upload']:
        local=urllib.unquote(request.args.get('local'))
        remote=urllib.unquote(request.args.get('remote'))
        user=urllib.unquote(request.args.get('user'))
        cmd=["python","-u",os.path.join(config_dir,'function.py'),action,local,remote,user]
    elif action=='UpdateFile':
        type_=request.args.get('type')
        cmd=["python","-u",os.path.join(config_dir,'function.py'),'UpdateFile',type_]
    else:
        cmd=["python","-u",os.path.join(config_dir,'function.py'),action]
    p = g.run(cmd)
    def read_process():
        while g.is_pending():
            lines = g.readlines()
            for proc, line in lines:
                yield "data:" + line + "\n\n"
        yield "data:end\n\n"
    resp=Response(read_process(), mimetype= 'text/event-stream')
    return resp


@admin.route('/stream',methods=["POST","GET"])
def stream():
    cmd_dict={
        'upgrade':"cd {} && git pull origin master && bash update.sh".format(config_dir),
        'running_log':'tail -30f {}/logs/PyOne.{}.log'.format(config_dir,'running'),
        'error_log':'tail -30f {}/logs/PyOne.{}.log'.format(config_dir,'error')
    }
    command=cmd_dict[request.args.get('command')]
    def generate():
        popen=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        global _pid
        tc=TimeCalculator()
        _pid=popen.pid
        while not popen.poll():
            msg=popen.stdout.readline()
            if msg=='end':
                yield "data:end\n\n"
                break
            yield "data:" + msg + "\n\n"
            if tc.PassNow()>=3:
                time.sleep(1)
        yield "data:end\n\n"
    return Response(generate(), mimetype= 'text/event-stream')

@admin.teardown_request
def teardown(exestr):
    global _pid
    if _pid is not None:
        # InfoLogger().print_r('kill pid {}'.format(_pid))
        os.kill(_pid, signal.SIGINT)
        _pid=None
