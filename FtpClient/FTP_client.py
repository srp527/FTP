# -*- coding:utf-8 -*- 
__author__ = 'SRP'
__date__ = '2018/6/5 15:44'

import optparse
import socket
import configparser,json,os,sys,time,hashlib


STATUS_CODE  = {
    250 : "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251 : "Invalid cmd ",
    252 : "Invalid auth data",
    253 : "Wrong username or password",
    254 : "Passed authentication",
    255 : "Filename doesn't provided",
    256 : "File doesn't exist on server",
    257 : "ready to send file",
    258 : "md5 verification",

    800 : "the file exist,but not enough ,is continue? ",
    801 : "the file exist !",
    802 : " ready to receive datas",

    900 : "md5 valdate success",
    901: "md5 valdate fail",
}


class ClientHandler():

    def __init__(self):
        self.op = optparse.OptionParser()

        self.op.add_option("-s","--server",dest="server")
        self.op.add_option("-P", "--port", dest="port")
        self.op.add_option("-u", "--username", dest="username")
        self.op.add_option("-p", "--password", dest="password")

        self.options,self.args = self.op.parse_args()
        self.verify_args(self.options,self.args)
        self.make_connection()
        self.mainPath = os.path.dirname(os.path.abspath(__file__)) #FTPclient绝对路径
        self.last = 0


    def verify_args(self,options,args):
        '''验证输入的参数'''
        server = options.server
        port = options.port

        if int(port)>0 and int(port)<65535:  #验证(端口)合法性
            return True
        else:
            exit('端口必须在0-65535之间')

    def make_connection(self):
        '''与服务器连接'''
        self.sock = socket.socket()
        self.sock.connect((self.options.server,int(self.options.port)))

    ##################################用户登录验证 && 命令执行结果 区域 start###########################################

    def authenticate(self):
        '''验证输入的用户名,密码   并返回登录结果'''
        if self.options.username is None or self.options.password is None:
            username = input('username:')
            password = input("password:")
            return self.get_auth_result(username, password)
        return self.get_auth_result(self.options.username, self.options.password)

    def response(self):
        '''接受服务端回应信息'''
        data = self.sock.recv(1024).decode('utf8')
        data = json.loads(data)
        return data

    def get_auth_result(self, username, password):
        '''将登录信息发送给服务端  并显示返回结果'''
        data = {
            "action": "auth",
            "username": username,
            "password": password, }

        self.sock.send(json.dumps(data).encode('utf8'))
        response = self.response()
        # print(STATUS_CODE[response['status_code']])
        if response["status_code"] == 254:
            self.username = username
            self.current_dir = username
            return True
        else:
            print(STATUS_CODE[response["status_code"]])

    ###############################用户登录验证 && 命令执行结果 区域 end ###########################################



    #################################用户命令区域 start#########################################

    def interactive(self):
        '''登录成功后 与服务器的交互'''
        print('开始你的操作...')
        if self.authenticate():
            while True:
                cmd_info = input("[%s]" %self.current_dir).strip()
                if len(cmd_info) == 0: continue
                if cmd_info == 'exit':
                    print('已断开连接')
                    break
                cmd_list = cmd_info.split()

                if hasattr(self,cmd_list[0]):
                    func = getattr(self,cmd_list[0])
                    func(*cmd_list)
                else:
                    print("Invalid cmd")


    def send_recv(self,data):
        '''发送,接收 执行函数'''
        self.sock.sendall(json.dumps(data).encode('utf8'))
        return self.sock.recv(1024).decode('utf8')


    def put(self,*cmd_list):
        '''上传   put 11.jpg 目标路径'''
        if len(cmd_list) == 3:
            action,local_path,target_path = cmd_list
        elif len(cmd_list) == 2:
            action, local_path = cmd_list
            target_path = 0
        else:
            action,local_path,target_path,is_md5 = cmd_list

        if '/' in local_path:
            local_path = os.path.join(self.mainPath,local_path.split('/'))
        else:
            local_path = os.path.join(self.mainPath,local_path)
        print('local_path',local_path)
        file_name = os.path.basename(local_path)
        file_size = os.stat(local_path).st_size

        data = {
            'action':'put',
            'file_name':file_name,
            'file_size':file_size,
            'target_path':target_path,
        }
        if self.md5_required(cmd_list):
            data['md5'] = True

        #############################################################
        print(data)
        is_exist = self.send_recv(data)
        has_sent = 0
        if is_exist == '800':
            #文件不完整
            choice = input('文件已存在,但不完整,是否继续?[Y/N]').strip()
            if choice.upper() == 'Y':
                continue_position = self.send_recv("Y")
                has_sent += int(continue_position)
            else:
                self.sock.sendall('N'.encode('utf8'))
                return

        elif is_exist == '801':  #文件存在
            print(STATUS_CODE[801])
            return

        start = time.time()

        with open(local_path,'rb') as f:
            f.seek(has_sent)      #文件断点

            if self.md5_required(cmd_list):
                    md5_obj = hashlib.md5()

                    while has_sent < file_size:
                        data = f.read(1024)
                        self.sock.sendall(data)    #发送数据
                        has_sent += len(data)
                        md5_obj.update(data)
                        # has_sent_md5 = md5_obj.hexdigest()
                        # print(has_sent_md5)
                        # print(type(has_sent_md5))
                        # with open('md5.txt', 'w') as f_md5:
                        #     f_md5.write(has_sent_md5)
                        self.show_progress(has_sent,file_size)
                    else:
                        end = time.time()
                        print('用时: %s s' % int((end - start)))
                        print('put success')
                        md5_val = md5_obj.hexdigest()
                        self.sock.recv(1024)    #解决粘包
                        response = self.send_recv(md5_val)
                        print('response',response)
                        if response == '900':
                            print(STATUS_CODE[900])
                        else:
                            print(STATUS_CODE[901])
            else:
                while has_sent < file_size:
                    data = f.read(1024)
                    self.sock.sendall(data)    #发送数据
                    has_sent += len(data)
                    self.show_progress(has_sent,file_size)
                else:
                    end = time.time()
                    print('用时: %ss' %int(end-start))
                    print('put success!')

    def md5_required(self,cmd_list):
        '''检查是否进行md5验证'''
        if '--md5' in cmd_list:
            return True

    def show_progress(self,has,total):
        '''进度条函数'''
        rate = float(has)/float(total)
        rate_num = int(rate*100)
        sys.stdout.write("%s %s%%\r" %("#"*rate_num,rate_num))

    def ls(self,*cmd_list):
        data = {
            'action':'ls',
        }
        data = self.send_recv(data)
        print(data)

    def cd(self,*cmd_list):
        '''cd 切换目录'''
        if len(cmd_list) == 1:
            self.current_dir = os.path.join(self.username)
        else:
            data = {
                'action': 'cd',
                'dirname': cmd_list[1],
            }
            data = self.send_recv(data)
            self.current_dir = os.path.join(self.username,os.path.basename(data))

    def mkdir(self,*cmd_list):
        data = {
            'action':'mkdir',
            'dirname':cmd_list[1]
        }
        data = self.send_recv(data)
        print(data)


client = ClientHandler()
client.interactive()