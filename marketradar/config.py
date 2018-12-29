#
# 读取系统配置文件
#
import os
import configparser

conf = configparser.ConfigParser()
conf.read("d:/config.ini")

if __name__ == '__main__':
    print(conf.getint('MYSQL',"port"))
    print(conf.get("MYSQL","host"))
    print(conf.get("MYSQL","dbName"))