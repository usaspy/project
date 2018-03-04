import pandas as pd
from pandas import Series,DataFrame
from marketradar.utils.logger import logger
from sqlalchemy import create_engine
from marketradar.config import conf
from marketradar.utils import dbpool
from marketradar.module import analyzer_engine
from marketradar.utils.threadpool import ThreadPool
from marketradar.utils.Exception import FilterError
from datetime import datetime
import numpy as np

engine = create_engine("mysql://%s:%s@%s/%s"% (conf.get('db','user'),conf.get('db','pass'),conf.get('db','host'),conf.get('db','database')))

#获取指定股票一个时间段内的交易数据，由于股票可能会停牌，故不使用starttime—endtime，而使用days(交易天数)
def __getStockDayDatasByPeriod(code,days):
    sql = "select TOPEN,HIGH,LOW,TCLOSE,LCLOSE,CHG,PCHG,VOTURNOVER,TURNOVER,MA5,MA10,MA20,DAY from DAY_DATAS where CODE=%s order by DAY desc limit %d" % (code, days)
    return pd.read_sql_query(sql,engine)

#获取市场上所有股票的日数据(系统默认最多保存近60日的交易记录)
def __getAllDayDatas():
    sql = "select CODE,DAY,TOPEN,HIGH,LOW,TCLOSE,LCLOSE,CHG,PCHG,VOTURNOVER,TURNOVER,MA5,MA10,MA20 from DAY_DATAS order by DAY desc"
    return pd.read_sql_query(sql,engine)

__ALL_DAY_DATAS = __getAllDayDatas()

#很重要
#从集合中切取指定股票的样本数据
def __getData(code,ybts):
    # 从全市交易数据集合中切取指定股票的N天(ybts)的样本数据
    df = __ALL_DAY_DATAS[__ALL_DAY_DATAS['CODE'] == code].iloc[0:ybts,:]
    #检查数据条数是否满足条件 =ybts
    if df.iloc[:, 0].size != ybts:
        return df
    #建立新的索引[1,2,3,4,5,6,7...]
    new_Index = []
    for i in range(0,ybts):
        new_Index.append(i)

    return pd.DataFrame(df.values,index=new_Index,columns=df.columns)

#温和放量
def filter_rule_1001(stock,ybts,fdts,multiple,match_ls,*args):
    try:
        df = __getData(stock.CODE, int(ybts))
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
        df = __getData(stock.CODE, int(ybts))
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