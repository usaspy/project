from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from marketradar.config import conf

__author__  = "zhang hong <11989935@qq.com>"
__status__  = "production"
# The following module attributes are no longer updated.
__version__ = "0.2"
__date__    = "2018/02/05"


app = Flask(__name__,static_folder='webUI/static',template_folder='webUI/templates')
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s/%s"% (conf.get('MYSQL','user'),conf.get('MYSQL','password'),conf.get('MYSQL','host'),conf.get('MYSQL','dbName'))

db = SQLAlchemy(app)

from marketradar.view import *
