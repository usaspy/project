from marketradar import app
from marketradar import db
from marketradar.model import *
from flask import Flask,render_template,session,request
from marketradar.module.analyzer import  *
from marketradar.module import collector
from marketradar.utils.threadpool import ThreadPool
from marketradar.utils import datetimeUtil
from marketradar.utils import dbpool



#加载所有关联收藏的股票
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
    if request.values.get('action') == '_cal_':
        dayString = request.values.get("day")
        collector.generate_ma(datetimeUtil.dateFormat2Format(dayString,'%m/%d/%Y','%Y-%m-%d'))
        collector.cal_CHANGEHAND(datetimeUtil.dateFormat2Format(dayString,'%m/%d/%Y','%Y-%m-%d'))
        msg = "股票移动平均线MA5、MA10、MA20、当日换手率计算完成！"

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
        slts = int(request.values.get('_slts')) #缩量天数
        multiple = int(request.values.get('multiple')) #放大倍数
        changehand = float(request.values.get('_changehand'))
        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1003, args=(stock, slts,multiple,changehand, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('1003.html')

#[1004-换手率选股]
@app.route('/1004',methods=['GET','POST'])
def _1004():
    if request.values.get('action') == 'query':
        match_ls = []
        ybts = int(request.values.get('ybts')) #样本天数
        changehand = float(request.values.get('_changehand')) #总换手率
        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_1004, args=(stock, ybts,changehand, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)

    return render_template('1004.html')

#============================================================价=================================================================
#[2001-十字启明星]
@app.route('/2001',methods=['GET','POST'])
def _2001():
    if request.values.get('action') == 'query':
        match_ls = []
        tag = request.values.get('tag') # 哪天出现十字星
        throwBaby = request.values.get('throwBaby') #必须是"弃婴"形态
        k3up = request.values.get('k3up') #K3日股价大涨(相较K1形成刺透或吞没形态)
        vol_increase = request.values.get('vol_increase') #成交量显著放大(K3与之前K2、K1相比)

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_2001, args=(stock,tag,throwBaby,k3up,vol_increase, match_ls, (tp)))
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


#[2005-缺口]
@app.route('/2005',methods=['GET','POST'])
def _2005():
    if request.values.get('action') == 'query':
        match_ls = []
        optionsRadios = request.values.get('optionsRadios') # 样本天数

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_2005, args=(stock,optionsRadios, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)
    return render_template('2005.html')


#[2006-上行三法]
@app.route('/2006',methods=['GET','POST'])
def _2006():
    if request.values.get('action') == 'query':
        match_ls = []
        optionsRadios = request.values.get('optionsRadios') # 样本天数

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_2006, args=(stock,optionsRadios, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)
    return render_template('2006.html')


#[4001-底部选股]
@app.route('/4001',methods=['GET','POST'])
def _4001():
    if request.values.get('action') == 'query':
        match_ls = []
        optionsRadios = int(request.values.get('optionsRadios')) # 样本天数

        ls = LISTS.query.all()  # 统计所有股票个数

        tp = ThreadPool(10)  # 30个线程处理
        for stock in ls:
            thread = tp.get_thread()
            t = thread(target=filter_rule_4001, args=(stock,optionsRadios, match_ls, (tp)))
            t.start()
        return render_template('result.html',matchs = match_ls)
    return render_template('4001.html')

#============================================================其他功能=================================================================

#[加入/移出收藏夹]
@app.route('/favorite',methods=['GET'])
def favorite():
    code = request.values.get('code')
    action = request.values.get('action')
    if action == 'cancel':
        #dbpool.executeUpdate(['update __relation set FLAG=0 where CODE=%s'% code])
        db.session.query(RELATION).filter(RELATION.CODE == code).update({RELATION.FLAG : 0-RELATION.FLAG})
        db.session.commit()
        return "<script>alert('取消收藏成功！');window.close();</script>"
    elif action == 'add':
        #RELATION.filter_by(CODE=code).update({RELATION.FLAG: '1'})
        r = RELATION.query.filter_by(CODE=code).first()
        if r == None:
            r = RELATION(CODE=code, FLAG=1, REMARK='',FAVORITE_TIME=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            db.session.add(r)
            db.session.commit()
        else:
            dbpool.executeUpdate(['update __relation set FLAG=abs(FLAG)+1 where CODE=%s'% code])
        return "<script>alert('加入收藏夹成功！');window.close();</script>"
    return None

#[收藏夹]
@app.route('/favorite_list',methods=['GET'])
def favorite_list():
    ls = db.session.query(LISTS,RELATION).filter(RELATION.CODE == LISTS.CODE,RELATION.FLAG > 0)

    return render_template('favorite_list.html',ls = ls)

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

#定义一个全局函数
@app.template_global('show_data_time')
def show_data_time():
    #return time.strftime("%Y-%m-%d %H:%M:%S", l)
    ls = db.session.query(DAY_DATAS.DAY).group_by(DAY_DATAS.DAY).order_by(DAY_DATAS.DAY.desc())
    lss = []
    for i in ls:
        lss.append(i.DAY)
    return lss
