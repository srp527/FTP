# -*- coding:utf-8 -*- 
__author__ = 'SRP'
__date__ = '2018/6/5 16:09'

import os,sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(BASE_DIR)

IP = "192.168.30.10"
PORT = 8888

ACCOUNT_PATH = os.path.join(BASE_DIR,'conf','accounts.cfg')