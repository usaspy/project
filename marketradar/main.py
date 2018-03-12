from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask,render_template,session,request
from datetime import datetime
from marketradar.config import conf
from marketradar.module import analyzer
from marketradar.module.analyzer import  filter_rule_1001
from marketradar.module.analyzer import  filter_rule_1002
from marketradar.module.analyzer import  filter_rule_1003
from marketradar.module.analyzer import  filter_rule_2001
from marketradar.module.analyzer import  filter_rule_2003
from marketradar.module.analyzer import  filter_rule_2004
from marketradar.module import collector
from marketradar.utils.threadpool import ThreadPool
from marketradar.utils import datetimeUtil
from marketradar.utils import dbpool

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

class RELATION(db.Model):
    __tablename__ = '__RELATION'
    CODE = db.Column(db.String(50),primary_key=True)
    FLAG = db.Column(db.String(50))
    REMARK = db.Column(db.String(50))


__RELATION_INFO = RELATION.query.all()
print(__RELATION_INFO)

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

#============================================================量=================================================================
#[1001-温和放量]
@app.route('/1001',methods=['GET','POST'])
def _1001():
    if request.values.get('action') == 'query':
        match_ls = []
        tag = request.values.get('tag') #
        ybts = int(request.values.get('ybts')) #放量天数
        ls = LISTS.query.all() #统计所有股票个数

        tp = ThreadPool(10)  #30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1001, args=(stock, tag, ybts, match_ls,(tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('1001.html')

#[1002-突放巨量]
@app.route('/1002',methods=['GET','POST'])
def _1002():
    if request.values.get('action') == 'query':
        match_ls = []
        multiple = int(request.values.get('multiple')) #默认放量倍数
        fdts = int(request.values.get('fdts')) #放量天数
        ls = LISTS.query.all() #统计所有股票个数

        tp = ThreadPool(10)  #30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1002, args=(stock, fdts, multiple, match_ls,(tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('1002.html')

#[1003-持续缩量之后的突然放量]
@app.route('/1003',methods=['GET','POST'])
def _1003():
    if request.values.get('action') == 'query':
        match_ls = []
        ybts = int(request.values.get('ybts')) #样本天数
        multiple = int(request.values.get('multiple')) #放大倍数
        cxsl = request.values.get('cxsl') #是否持续缩量

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1003, args=(stock, ybts,multiple,cxsl, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('1003.html')


#============================================================价=================================================================
#[2001-十字启明星]
@app.route('/2001',methods=['GET','POST'])
def _2001():
    if request.values.get('action') == 'query':
        match_ls = []
        tag = request.values.get('tag') # 哪天出现十字星
        isStandard = request.values.get('isStandard') #必须标准十字星
        throwBaby = request.values.get('throwBaby') #必须是"弃婴"形态
        k3up = request.values.get('k3up') #K3日股价大涨(相较K1形成刺透或吞没形态)
        vol_increase = request.values.get('vol_increase') #成交量显著放大(K3与之前K2、K1相比)

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_2001, args=(stock,tag,isStandard,throwBaby,k3up,vol_increase, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('2001.html')


#[2003-锤子线]
@app.route('/2003',methods=['GET','POST'])
def _2003():
    if request.values.get('action') == 'query':
        match_ls = []
        tag = request.values.get('tag') # 哪天出现锤子
        no_head = request.values.get('no_head') #必须光头

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_2003, args=(stock,tag,no_head, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('2003.html')



#[2004-看涨吞没形态 ]
@app.route('/2004',methods=['GET','POST'])
def _2004():
    if request.values.get('action') == 'query':
        match_ls = []
        ybts = int(request.values.get('ybts')) # 样本天数

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_2004, args=(stock,ybts, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)
    return render_template('2004.html')



#============================================================势=================================================================

#[收藏夹]
@app.route('/favorite',methods=['GET'])
def favorite():
    code = request.values.get('code')
    action = request.values.get('action')
    if action == 'cancel':
        #dbpool.executeUpdate(['update __relation set FLAG=0 where CODE=%s'% code])
        db.session.query(RELATION).filter(RELATION.CODE == code).update({RELATION.FLAG : 0})
        db.session.commit()
        return "<script>alert('取消收藏成功！')</script>"
    elif action == 'add':
        #RELATION.filter_by(CODE=code).update({RELATION.FLAG: '1'})
        r = RELATION.query.filter_by(CODE=code).first()
        if r == None:
            r = RELATION(CODE=code, FLAG=1, REMARK='')
            db.session.add(r)
            db.session.commit()
        else:
            dbpool.executeUpdate(['update __relation set FLAG=1 where CODE=%s'% code])
        return "<script>alert('加入收藏夹成功！')</script>"
    return None

#========================================================COMMON=================================================================
#定义一个过滤器600168->sh600168
@app.template_filter('code_prefix')
def code_prefix(code):
    if code[0:2] == '00':
        _code = "sz" + code
    if code[0:2] == '60':
        _code = "sh" + code
    return _code

#定义一个过滤器 添加收藏
@app.template_filter('in_favorite')
def in_favorite(code):
    for ad in __RELATION_INFO:
        if ad.CODE == code and ad.FLAG == 1:
            return "<a href='/favorite?action=cancel&code=" + code + "' target='_blank'><font color=gray>已收藏</font></a>"
    return "<a href='/favorite?action=add&code=" + code + "' target='_blank'>添加收藏</a>"

if __name__ == '__main__':
    app.run(host=conf.get('web','host'), port=conf.get('web','port'), debug=False)