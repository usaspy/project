#
# 读取系统配置文件
#
import os
import configparser

conf = configparser.ConfigParser()
conf.read("config.ini")

if __name__ == '__main__':
    print(conf.getint('db',"port"))
    print(conf.get("db","host"))
    print(conf.get("db","database"))