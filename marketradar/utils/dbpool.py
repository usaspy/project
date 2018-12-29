from marketradar.utils.logger import logger
import MySQLdb
from DBUtils.PooledDB import PooledDB

from marketradar.config import conf

#
# 数据库操作
# 连接池工具
#

#默认连接数 5  关闭事务，需手动提交
dbpool = PooledDB(MySQLdb,5,host=conf.get('MYSQL','host'),user=conf.get('MYSQL','user'),
                  passwd=conf.get('MYSQL','password'),db=conf.get('MYSQL','dbName'),
                  port=conf.getint('MYSQL','port'),charset='gbk',setsession=['SET AUTOCOMMIT = 0'])

#insert delete update  操作
def executeUpdate(sqls):
    conn = dbpool.connection()
    cur = conn.cursor()
    try:
        for sql in sqls:
            logger.debug(sql)
            cur.execute(sql)
        conn.commit()
    except Exception as es:
        logger.exception(es)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

#查询 操作
def executeQuery(sql):
    conn = dbpool.connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        res = cur.fetchall()
        return res
    except Exception as es:
        logger.exception(es)
        return None
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print(query("select * from LISTS"))
    print(execute("insert into LISTS values('asea','b')"))
