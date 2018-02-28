from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template,session,request
from datetime import datetime
from marketradar.config import conf
from marketradar.module import analyzer
from marketradar.module.analyzer import  filter_rule_1001
from marketradar.module.analyzer import  filter_rule_1002
from marketradar.module import collector
from marketradar.utils.threadpool import ThreadPool
from marketradar.utils import datetimeUtil

app = Flask(__name__,static_folder='webUI/static',template_folder='webUI/templates')

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://%s:%s@%s/%s"% (conf.get('db','user'),conf.get('db','pass'),conf.get('db','host'),conf.get('db','database'))

db = SQLAlchemy(app)

class DAY_DATAS(db.Model):
    __tablename__='DAY_DATAS'
    ID = db.Column(db.BIGINT,primary_key=True)
    CODE = db.Column(db.String(8)) #代码
    NAME = db.Column(db.String(255)) #股票名称
    TOPEN = db.Column(db.DECIMAL) #开盘价
    HIGH = db.Column(db.DECIMAL) #最高
    LOW = db.Column(db.DECIMAL) #最低
    TCLOSE = db.Column(db.DECIMAL) # 收盘价
    LCLOSE = db.Column(db.DECIMAL) #前日收盘价
    CHG = db.Column(db.DECIMAL)  #涨跌额
    PCHG = db.Column(db.DECIMAL)  #涨跌幅
    VOTURNOVER = db.Column(db.BIGINT)  #成交量(手)
    VATURNOVER = db.Column(db.DECIMAL)  #成交金额
    TCAP = db.Column(db.DECIMAL)  #总市值
    MCAP = db.Column(db.DECIMAL)  #流通市值
    DAY = db.Column(db.Date)  #交易日
    MA5 = db.Column(db.DECIMAL)  #MA5
    MA10 = db.Column(db.DECIMAL)  #MA10
    MA20 = db.Column(db.DECIMAL)  #MA20
    CREATE_TIME = db.Column(db.DateTime) #采集时间

class LISTS(db.Model):
    __tablename__ = 'LISTS'
    CODE = db.Column(db.String(50),primary_key=True)
    NAME = db.Column(db.String(50))

class TMP_FAILED(db.Model):
    __tablename__ = 'TMP_FAILED'
    CODE = db.Column(db.String(50),primary_key=True)
    NAME = db.Column(db.String(50))

#[首页]
@app.route('/',methods=['GET'])
def index():
    return render_template('index.html')

#[同步数据]
@app.route('/sync',methods=['GET','POST'])
def sync():
    msg = ""
    if request.values.get('action') == 'generate_lists':
        collector.clear_lists()
        collector.generate_lists()
        msg = "股票列表更新完成！"
    if request.values.get('action') == 'generate_day_datas':
        dayString = request.values.get("day")
        collector.clear_tmp_failed()
        collector.clear_day_datas(datetimeUtil.dateFormat2Format(dayString,'%m/%d/%Y','%Y-%m-%d'))
        collector.generate_today(datetimeUtil.dateFormat2Format(dayString,'%m/%d/%Y','%Y%m%d'))
        msg = "股票交易数据导入完成！"
    if request.values.get('action') == 'retry_sync':
        dayString = request.values.get("day")
        collector.generate_today_remain(datetimeUtil.dateFormat2Format(dayString,'%m/%d/%Y','%Y%m%d'))
        msg = "补录完成！"
    if request.values.get('action') == 'generate_ma':
        dayString = request.values.get("day")
        collector.generate_ma(datetimeUtil.dateFormat2Format(dayString,'%m/%d/%Y','%Y-%m-%d'))
        msg = "%s的股票移动平均线MA5、MA10、MA20生成完成！"

    ls = LISTS.query.all()  #统计所有股票个数
    session_failed_codes = TMP_FAILED.query.all()  #统计失败股票个数
    return render_template('sync.html',lists_count=len(ls),session_failed_codes=session_failed_codes,msg=msg)


#[1001-温和放量]
@app.route('/1001.html',methods=['GET','POST'])
def _1001():
    match_ls = []
    if request.values.get('action') == 'query':
        multiple = 2  #默认放量倍数
        ybts = int(request.values.get('ybts')) #样本天数
        fdts = int(request.values.get('fdts')) #放量天数
        ls = LISTS.query.all() #统计所有股票个数

        tp = ThreadPool(30)  #30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1001, args=(stock, ybts, fdts, multiple, match_ls,(tp)))
            t.start()

    return render_template('1001.html',matchs = match_ls)

#[1002-突放巨量]
@app.route('/1002.html',methods=['GET','POST'])
def _1002():
    match_ls = []
    if request.values.get('action') == 'query':
        multiple = 5  #默认放量倍数
        ybts = int(request.values.get('ybts')) #样本天数
        fdts = int(request.values.get('fdts')) #放量天数
        ls = LISTS.query.all() #统计所有股票个数

        tp = ThreadPool(30)  #30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1002, args=(stock, ybts, fdts, multiple, match_ls,(tp)))
            t.start()

    return render_template('1002.html',matchs = match_ls)


if __name__ == '__main__':
    app.run(host=conf.get('web','host'), port=conf.get('web','port'), debug=False)