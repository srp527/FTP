# -*- coding:utf-8 -*- 
__author__ = 'SRP'
__date__ = '2018/6/5 16:28'

import socketserver
import json, os,hashlib
import configparser

from conf import settings

STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    258: "md5 verification",

    800: "the file exist,but not enough ,is continue? ",
    801: "the file exist !",
    802: " ready to receive datas",

    900: "md5 valdate success",
    901: "md5 valdate fail",
}


class ServerHandler(socketserver.BaseRequestHandler):

    def handle(self):
        while 1:
            # conn = self.request
            data = self.request.recv(1024).strip()
            if len(data) == 0: break
            data = json.loads(data.decode('utf8'))

            if data.get("action"):
                if hasattr(self, data.get('action')):
                    func = getattr(self, data.get("action"))
                    func(**data)
                else:
                    print('Invalid cmd!')
                    self.send_reponse(251)
            else:
                print('invalid cmd format')
                self.send_reponse(250)

    def send_reponse(self, status_code):
        '''向客户端返回数据'''
        response = {'status_code': status_code, 'status_msg': STATUS_CODE[status_code]}
        self.request.sendall(json.dumps(response).encode('utf8'))

    def auth(self, **data):
        username = data.get('username')
        password = data.get('password')

        user = self.authenticate(username, password)
        if user:
            self.send_reponse(254)
        else:
            self.send_reponse(253)

    def authenticate(self, user, pwd):
        cfg = configparser.ConfigParser()
        cfg.read(settings.ACCOUNT_PATH)

        if user in cfg.sections():  # 判断 客户端发来的用户是否在accounts.cfg 中
            if cfg[user]['Password'] == pwd:
                self.user = user
                self.mainPath = os.path.join(settings.BASE_DIR, 'home', self.user)  # 用户家目录绝对路径
                print('验证通过!')
                return user

    def put(self, **data):
        print('data', data)
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        target_path = data.get('target_path')
        if target_path == 0:
            target_path = 'image'
        abs_path = os.path.join(self.mainPath, target_path, file_name)

        ###############上传可能遇到的几种情况#################
        has_received = 0
        if os.path.exists(abs_path):
            exist_file_size = os.stat(abs_path).st_size  # 已存在的文件大小
            print(exist_file_size)
            if exist_file_size < int(file_size):      # 断点续传
                self.request.sendall('800'.encode('utf8'))
                chioce = self.request.recv(1024).decode('utf8')
                if chioce == 'Y':
                    self.request.sendall(str(exist_file_size).encode('utf8'))
                    has_received = exist_file_size
                    f = open(abs_path, 'ab')
                else:
                    f = open(abs_path, 'wb')

            else:    #已存在完整的文件,不传!
                self.request.sendall('801'.encode('utf8'))
                return

        else:        #服务端不存在该文件
            self.request.sendall("802".encode('utf8'))
            f = open(abs_path, 'wb')
        # if data.get('md5'):
        #     md5_obj = hashlib.md5()
        #     while has_received < int(file_size):
        #         try:
        #             data = self.request.recv(1024)
        #             if not data:
        #                 raise Exception
        #         except Exception as e:
        #             break
        #         f.write(data)
        #         has_received += len(data)
        #         md5_obj.update(data)
        #     else:
        #         self.request.sendall(b'ok') #解决粘包
        #         send_file_md5 = self.request.recv(1024).decode('utf8')
        #         # print(send_file_md5.strip('"'),type(send_file_md5))
        #         # print(md5_obj.hexdigest(),type(md5_obj.hexdigest()))
        #         if send_file_md5.strip('"') == md5_obj.hexdigest():
        #             self.request.sendall('900'.encode('utf8'))
        #         else:
        #             self.request.sendall('901'.encode('utf8'))
            # print('接收完毕!')

        while has_received < file_size:
            try:
                data = self.request.recv(1024)
                if not data:
                    raise Exception
            except Exception:
                break
            f.write(data)
            has_received += len(data)
        f.close()
        print('接收完毕!')
        return

    def ls(self,**data):
        file_list = os.listdir(self.mainPath)
        file_str = '\t'.join(file_list)
        if not len(file_list):
            file_str = "<empty dir>"
        self.request.sendall(file_str.encode('utf8'))

    def cd(self,**data):
        dirname = data.get('dirname')

        if dirname == '..' or dirname == '0':
            # self.mainPath = os.path.join(self.mainPath)
            # print('basename',os.path.basename(self.mainPath))
            # if os.path.basename(os.path.dirname(self.mainPath)) == 'home':
            #     self.mainPath = os.path.join(settings.BASE_DIR, 'home', self.user)
            self.mainPath = os.path.dirname(self.mainPath)
            # print(self.mainPath)
        else:

            self.mainPath = os.path.join(self.mainPath, dirname)
        self.request.sendall(self.mainPath.encode('utf8'))

    def mkdir(self,**data):
        dirname = data.get('dirname')
        path = os.path.join(self.mainPath,dirname)
        if not os.path.exists(path):
            if '/' in dirname:
                os.makedirs(path)
            else:
                os.mkdir(path)
            self.request.sendall('创建成功!'.encode('utf8'))

        else:
            self.request.sendall('目录已存在!'.encode('utf8'))


    def download(self):
        pass
