import urllib.request
import urllib.error
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

from marketradar.utils import dbpool
from marketradar.utils.threadpool import ThreadPool
from marketradar.utils.logger import logger

from retrying import retry

import pandas as pd
from pandas import Series,DataFrame
from sqlalchemy import create_engine
from marketradar.config import conf

# 获取 SZ & SH 所有股票的代码,并存放到数据库 LISTS
# 调用前需手工清空LISTS，truncate table LISTS
def generate_lists():
    #stocks = {}
    sqls = []
    url = "http://quote.eastmoney.com/stocklist.html"
    headers = {'Accept': '*/*',
               'Referer': 'http://www.huawa.com/orders',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
               }

    req = urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('gb18030')
            #print(content.decode('gb18030'))
            soup = BeautifulSoup(content, 'html.parser')
            div_1 = soup.find('div', class_='quotebody')
            for html in div_1.find_all('li',  recursive=True):
                o = html.find('a').get_text().strip()
                if o[-7:-5] == '00'or o[-7:-5] == '60':   #只取上证60和深证00
                    #stocks[o[-7:-1]] = o[:-8]
                    sqls.append("insert into LISTS(CODE,NAME)VALUES('%s','%s')"% (o[-7:-1],o[:-8]))
            dbpool.executeUpdate(sqls)
    except urllib.error.URLError as e:
        logger.exception(">>获取股票清单失败>>")
        if hasattr(e,'reason'):
            logger.exception(e.reason)

#下午3点收盘后人工触发，采集全市所有股票的当日数据
def generate_today(day):
    tp = ThreadPool(10)
    lists = dbpool.executeQuery("select CODE,NAME from LISTS")
    for i in lists:
        thread = tp.get_thread()
        t = thread(target=__collect_One,args=(i[0],i[1],day,day,(tp)))
        t.start()

# 采集失败的代码执行重采，直到所有都采集成功结束
def generate_today_remain(day):
    tp = ThreadPool(5)
    while True:
        lists = dbpool.executeQuery("select CODE,NAME from TMP_FAILED;truncate table TMP_FAILED")
        if len(lists) == 0:
            logger.info("采集完成!")
            break
        logger.info("有%s个股票需要重采"% len(lists))
        for i in lists:
            thread = tp.get_thread()
            t = thread(target=__collect_One, args=(i[0], i[1], day, day, (tp)))
            t.start()

#采集指定交易日的股票交易数据
@retry(stop_max_attempt_number=3)   #这个retry貌似不生效啊？ （采集不成功重试3次）
def __collect_One(code,name,sday,eday,*args):
    data_sqls=[]
    if code[0:2] == '00':
        _code = "1" + code
    if code[0:2] == '60':
        _code = "0" + code
    url = "http://quotes.money.163.com/service/chddata.html?code=%s&start=%s&end=%s&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP"% (_code,sday,eday)
    headers = {'Accept': '*/*',
               'Referer': 'http://www.huawa.com/orders',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
               }

    req = urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=15) as resp:
            content = resp.read().decode('gb18030')
            data = content.split("\r\n")
            data.remove(data[0])
            for i in data:
                if i == '':
                    break
                x = i.split(",")
                if x[6] == '0.0': #开盘价为0.0,代表该股今日停牌
                    break
                data_sqls.append("insert into DAY_DATAS(CODE,NAME,TOPEN,HIGH,LOW,TCLOSE,LCLOSE,CHG,PCHG,VOTURNOVER,TURNOVER,VATURNOVER,TCAP,MCAP,DAY,CREATE_TIME) VALUES"
                                 "('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',now())" %
                                 (code,name,x[6],x[4],x[5],x[3],x[7],x[8],x[9],x[11],x[10],x[12],x[13],x[14],x[0]))

            dbpool.executeUpdate(data_sqls)
    except Exception as e:
        logger.exception("采集股票[%s-%s]交易数据时出错 >> "%(code,name))
        logger.exception(e)
        __failed_one(code,name)
    finally:
        if args and isinstance(args[0],ThreadPool): #如果第一个参数是线程池，则执行添加新线程操作
            args[0].add_thread()

#采集入库时，如果报错，记录该股票代码，后续重采
def __failed_one(code,name):
    dbpool.executeUpdate(["insert into TMP_FAILED(CODE,NAME) VALUES ('%s','%s')"%(code,name)])


def clear_lists():
    try:
        dbpool.executeUpdate(["truncate table LISTS"])
    except Exception as e:
            logger.exception(e)

def clear_day_datas(day):
    try:
        dbpool.executeUpdate(["delete from DAY_DATAS where DAY='%s'"% day])
    except Exception as e:
        logger.exception(e)
#
def clear_tmp_failed():
    try:
        dbpool.executeUpdate(["truncate table TMP_FAILED"])
    except Exception as e:
        logger.exception(e)

#生成当日的MA5，10，20
def generate_ma(day):
    tp = ThreadPool(20)
    lists = dbpool.executeQuery("select CODE,NAME from LISTS")
    for i in lists:
        thread = tp.get_thread()
        t = thread(target=__generate_MA_5_10_20,args=(i[0],day,(tp)))
        t.start()

engine = create_engine("mysql://%s:%s@%s/%s"% (conf.get('db','user'),conf.get('db','pass'),conf.get('db','host'),conf.get('db','database')))

def __generate_MA_5_10_20(code,day,*args):
    try:
        ma5 = 0
        ma10 = 0
        ma20 = 0

        sql = "select TCLOSE,DAY from DAY_DATAS where CODE=%s and DAY <= '%s' order by DAY desc limit %d" % (code,day,20)
        df = pd.read_sql_query(sql, engine)
        series = df["TCLOSE"]

        if len(series) >= 5:
            ma5 = series[0:5].sum() / 5
        if len(series) >= 10:
            ma10 = series[0:10].sum() / 10
        if len(series) == 20:
            ma20 = series[0:20].sum() / 20

        dbpool.executeUpdate(["update DAY_DATAS set MA5=%.2f,MA10=%.2f,MA20=%.2f where CODE=%s and DAY='%s'" % (ma5,ma10,ma20,code,day)])
        #print("update DAY_DATAS set MA5=%.2f,MA10=%.2f,MA20=%.2f where CODE=%s and DAY='%s'" % (ma5,ma10,ma20,code,day))
    except Exception as e:
        logger.exception("生成股票[%s]MA参数时出错 >> "%(code))
        logger.exception(e)
    finally:
        if args and isinstance(args[0],ThreadPool): #如果第一个参数是线程池，则执行添加新线程操作
            args[0].add_thread()


if __name__ == '__main__':
    #collect_theOne('000971','20160808','20160808')
    #generate_lists()
    #generate_history('20180201','20180201')
    #generate_today('20180201')
    generate_today('20180201')