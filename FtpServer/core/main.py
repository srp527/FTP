# -*- coding:utf-8 -*- 
__author__ = 'SRP'
__date__ = '2018/6/5 15:46'

import optparse  #解析命令行的命令
import socketserver

from conf import settings
from core import server


class ArgvHandler():

    def __init__(self):
        self.op = optparse.OptionParser()
        # self.op.add_option("-s","--server",dest="server")
        # self.op.add_option("-P","--port",dest="port")
        options,args = self.op.parse_args()

        self.verify_args(options,args)   #验证命令参数


    def verify_args(self,options,args):
        cmd = args[0]
        if hasattr(self,cmd):
            func = getattr(self,cmd)
            func()

    def start(self):
        print('启动成功')
        s = socketserver.ThreadingTCPServer((settings.IP,settings.PORT),server.ServerHandler)
        s.serve_forever()


    def help(self):
        pass




