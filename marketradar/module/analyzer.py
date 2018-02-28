import pandas as pd
from pandas import Series,DataFrame
from marketradar.utils.logger import logger
from sqlalchemy import create_engine
from marketradar.config import conf
from marketradar.utils import dbpool
from marketradar.module import analyzer_engine
from marketradar.utils.threadpool import ThreadPool
from marketradar.utils.Exception import FilterError

engine = create_engine("mysql://%s:%s@%s/%s"% (conf.get('db','user'),conf.get('db','pass'),conf.get('db','host'),conf.get('db','database')))

#获取指定股票一个时间段内的交易数据，由于股票可能会停牌，故不使用starttime—endtime，而使用days(交易天数)
def __getStockDayDatasByPeriod(code,days):
    sql = "select CODE,TOPEN,HIGH,LOW,TCLOSE,LCLOSE,CHG,PCHG,VOTURNOVER,TURNOVER,VATURNOVER,TCAP,MCAP,MA5,MA10,MA20,DAY from DAY_DATAS where CODE=%s order by DAY desc limit %d" % (code, days)
    return pd.read_sql_query(sql,engine)

#温和放量
def filter_rule_1001(stock,ybts,fdts,multiple,match_ls,*args):
    try:
        df = __getStockDayDatasByPeriod(stock.CODE, int(ybts))
        if analyzer_engine.rule_1001(df, ybts, fdts, multiple):
            match_ls.append(stock)
    except Exception as e:
        logger.exception("对股票[%s-%s]数据进行分析时出错 >> " % (stock.CODE, stock.NAME))
        logger.exception(e)
    finally:
        if args and isinstance(args[0], ThreadPool):  # 如果第一个参数是线程池，则执行添加新线程操作
            args[0].add_thread()

#突放巨量
def filter_rule_1002(stock,ybts,fdts,multiple,match_ls,*args):
    try:
        df = __getStockDayDatasByPeriod(stock.CODE, int(ybts))
        if analyzer_engine.rule_1002(df, ybts, fdts, multiple):
            match_ls.append(stock)
    except Exception as e:
        logger.exception("对股票[%s-%s]数据进行分析时出错 >> " % (stock.CODE, stock.NAME))
        logger.exception(e)
    finally:
        if args and isinstance(args[0], ThreadPool):  # 如果第一个参数是线程池，则执行添加新线程操作
            args[0].add_thread()

if __name__ == "__main__":
   # print(getDayDatasByPeriod('000001',30))
    pass