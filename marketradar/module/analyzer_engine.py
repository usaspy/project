from marketradar.utils.Exception import FilterError
import numpy as np

#[温和放量上涨]
#规则：
#1.成交量相对于前一天放大
#2.价格相对于前一天上涨
#3.是否温和：每天的涨幅不能超过3%
#[持续缩量下跌]
#规则：
#1.成交量相对于前一天缩小
#2.价格相对于前一天下跌
def rule_1001(df, tag, ybts):
    if df.iloc[:,0].size != ybts+1:
        return False

    vol_series = df["VOTURNOVER"]  #成交量 列表
    pchg_series = df["PCHG"]  #涨幅 列表

    if tag == "A":
        #step.1
        for i in range(0,ybts):
            if (vol_series[i] / vol_series[i+1] < 1.0) or (vol_series[i] / vol_series[i+1] > 1.7):#如果最近几天成交量没有持续温和放大，则不满足条件，返回False
                return False
        # step.2
        for i in range(0, ybts):
            if pchg_series[i] <= 0:  # 如果最近几天价格涨幅没有持续为正，则不满足条件，返回False
                return False
        # step.3
        for i in range(0, ybts):
            if pchg_series[i] > 3.0:  # 涨幅过大
                return False
    if tag == "B":
        # step.1
        for i in range(0, ybts):
            if vol_series[i] / vol_series[i + 1] >= 1.0:  # 如果最近几天成交量没有持续缩量，则不满足条件，返回False
                return False
        # step.2
        for i in range(0, ybts):
            if pchg_series[i] > 0:  # 如果最近几天价格涨幅没有持续为负，则不满足条件，返回False
                return False

    return True

#[突放巨量]
#规则：
#1.确定fdts放大天数
#2.放大天数内每日成交量至少是放大前一日的multiple=7倍
def rule_1002(df, fdts, multiple):
    if df.iloc[:,0].size != (fdts + 1):
        return False

    series = df["VOTURNOVER"]
    #step.2
    for i in range(0,fdts):
        if series[i]/series[fdts] < multiple:#放大天数内的每一天成交量都是巨量
            return False
    return True

#[持续缩量后首次放量]
#规则：

#1.至少有slts天的换手率不高于2%
#2.今日的成交量是前10天成交均量的multiple=2倍以上
#3.今日的成交量是昨日的3倍以上，且今天收盘价是上涨的
def rule_1003(df, slts, multiple,changehand):
    if df.iloc[:,0].size != 20:
        return False

    series = df["VOTURNOVER"]
    pchg_series = df["PCHG"]  #涨幅 列表
    #step.3
    if series[0]/series[1] < 3:
        return False
    if pchg_series[0] <= 0:
        return False
    #step.2
    avg_vol = series[1:11].sum()/10
    if series[0]/avg_vol < multiple:
        return False
    #step.1
    count = 0
    for i in range(1,20):
        _changehand = df.iloc[i].CHANGEHAND
        if  _changehand <= changehand:  #当日换手率不超过2%
            count += 1
    if count < slts:
        return False

    return True

#[换手率选股]
#规则：
#1.确定fdts放大天数
#2.放大天数内每日成交量至少是放大前一日的multiple=7倍
def rule_1004(df, ybts, changehand):
    if df.iloc[:,0].size != ybts:
        return False

    series = df["CHANGEHAND"]
    #step.2
    if series[0:ybts].sum() < changehand:
        return False
    return True

#[启明星/十字启明星# ]
#规则：
#满足启明星的几个基本条件:
#1.行情经过多日的下跌，K2日出现十字星线（收/开盘价一致）
#2.K2相对K1的实体必须有向下跳空缺口（另外如果K3相对K2的实体也有向上跳空缺口则更佳）
#3.K1成交量较小，预示下跌势头已经趋缓，K3成交量放大
def rule_2001(df, tag,throwBaby,k3up,vol_increase):
    if tag == '2d':
        if df.iloc[:, 0].size != 2:
            return False
        k2 = df.iloc[0] #今天 返回一个series 如果是iloc[0:0]返回的就是dataframe
        k1 = df.iloc[1] #昨天

        # 检查是否K1 K2 实体有向下跳空缺口
        if (k1['TCLOSE'] > k2['TCLOSE'] and k1['TCLOSE'] > k2['TOPEN'] and k1['TOPEN'] > k2['TCLOSE'] and k1['TOPEN'] > k2['TOPEN']) != True:
            return False

        # 检查是否为十字星
        if __isCrissStar(k2) != True:
            return False
        return True

    if tag == '3d':
        if df.iloc[:, 0].size != 3:
            return False
        k3 = df.iloc[0]  # 今天 返回一个series 如果是iloc[0:0]返回的就是dataframe
        k2 = df.iloc[1]  # 昨天 返回一个series 如果是iloc[0:0]返回的就是dataframe
        k1 = df.iloc[2]  # 前天

        # 检查是否K1 K2 实体有向下跳空缺口
        if (k1['TCLOSE'] > k2['TCLOSE'] and k1['TCLOSE'] > k2['TOPEN'] and k1['TOPEN'] > k2['TCLOSE'] and k1['TOPEN'] > k2['TOPEN']) != True:
            return False
        # 检查是否K2 K3 实体有向上跳空缺口
        if (k3['TCLOSE'] > k2['TCLOSE'] and k3['TCLOSE'] > k2['TOPEN'] and k3['TOPEN'] > k2['TCLOSE'] and k3['TOPEN'] > k2['TOPEN']) != True:
            return False
        #如果k3日的最低价不能低于k2日的最低价
        if k3.LOW < k2.LOW:
            return False
        # 需要检查是否有向上跳空缺口（弃婴形态）
        if throwBaby == 'yes':
            if (k3.LOW >=  k2['TCLOSE'] and k3.LOW >= k2['TOPEN']) != True:
                return False
        # 检查是否为十字星
        if __isCrissStar(k2) != True:
            return False
        # 需要检查K3成交量是否放大
        if vol_increase == 'yes':
            if k3.VOTURNOVER < k1.VOTURNOVER + k2.VOTURNOVER:
                return False
        #K3日股价大涨(相较K1形成刺透或看涨吞没形态)
        if k3up == 'yes':
            if __ctxt(k1,k3) != True or __kztmxt(k1,k3) != True:
                return False
    return True

#[锤子线]
#规则：
#满足锤子线的几个基本条件:
#1.行情经过多日的下跌
#2.下影线越长越好
def rule_2003(df, tag, no_head):
    if df.iloc[:, 0].size != 5:
        return False

    if tag == 'A':
        k = df.iloc[0]  # 今日锤子
        # 去掉一字涨跌停的股票
        if k.HIGH == k.LOW:
            return False
        # 实体和上影线长度不超过总的1/3
        if k.TCLOSE >= k.TOPEN:
            if (k.HIGH - k.LOW) / (k.TOPEN - k.LOW + 0.00001) > 1.5:
                return False
        elif k.TCLOSE < k.TOPEN:
            if (k.HIGH - k.LOW) / (k.TCLOSE - k.LOW + 0.00001) > 1.5:
                return False

        # 5天内是否持续下跌
        if __is_continue_fall(df[0:]) != True:
            return False

        # 必须是光头阳线
        if no_head == 'yes':
            if k.TCLOSE != k.HIGH:
                return False
    if tag == 'B':
        k3 = df.iloc[0]  #
        k = df.iloc[1]  # 昨日是锤子

        # 去掉一字涨跌停的股票
        if k.HIGH == k.LOW:
            return False
        # 实体和上影线长度不超过总的1/3
        if k.TCLOSE >= k.TOPEN:
            if (k.HIGH - k.LOW) / (k.TOPEN - k.LOW + 0.00001) > 1.5:
                return False
        elif k.TCLOSE < k.TOPEN:
            if (k.HIGH - k.LOW) / (k.TCLOSE - k.LOW + 0.00001) > 1.5:
                return False
        # 5-1天内是否持续下跌
        if __is_continue_fall(df[1:]) != True:
            return False
        # 必须是光头阳线
        if no_head == 'yes':
            if k.TCLOSE != k.HIGH:
                return False

        #第二天没有创新低
        if k3.LOW < k.LOW:
            return False
        #第二天收盘价高于前日的最高价
        if k3.TCLOSE < k.HIGH:
            return False

    return True


#[看涨吞没形态]
#规则：
#满足锤子线的几个基本条件:
#1.行情经过多日的下跌
#2.相邻的两根K线，一根阴一根阳
#3.K2实体完全吞没K1实体,(如果向前吞没更多则更更好)
#4.K2的成交量比较大
def rule_2004(df, ybts):
    if df.iloc[:, 0].size != ybts:
        return False

    k2 = df.iloc[0]  # 今日
    k1 = df.iloc[1]  # 昨日
    #4
    if k2.VOTURNOVER < k1.VOTURNOVER * 1.5: #成交量放大低于1.5倍
        return False
    #1
    if __is_continue_fall(df[1:]) != True:
        return False

    return __kztmxt(k1,k2)


#[缺口]
def rule_2005(df, optionsRadios):
    if df.iloc[:, 0].size != 20:
        return False

    if optionsRadios == '_A':
        k2 = df.iloc[0]  # 今日
        k1 = df.iloc[1]  # 昨日

        if k2.LOW > k1.HIGH:
            return True
    if optionsRadios == '_B':
        for i in range(0, 20-1):
            if df.iloc[i].LOW > df.iloc[i+1].HIGH and i > 0:
                LOWS = np.array(df.iloc[0:i].LOW)
                print(df.iloc[0].CODE)
                print(df.iloc[i].DAY)
                #print(df.iloc[i].LOW)
                #print(df.iloc[i+1].HIGH)
                print((LOWS.min()))
                if LOWS.min() > df.iloc[i+1].HIGH:
                    if df.iloc[0].LOW  <  df.iloc[i+1].HIGH * 1.01:
                        return True
                return False

    return False


# 检查是否持续下跌
def __is_continue_fall(df):
    LOWS = np.array(df['LOW'])
    if LOWS.min() != df.iloc[0].LOW:  #完美的持续下跌形态中，最近一日LOW值应为最低值
        return False
    # 检查这几日是否持续下跌形态
    offset = 0
    i = 1
    while i < df.iloc[:,0].size:
        if df.iloc[i-1].LOW <= df.iloc[i].LOW:
            offset += 1
        i+=1
    if offset / df.iloc[:, 0].size < 0.57:  # 如果走低天数/总天数>0.57 则认为是持续下跌形态
        return False
    return True


#检查是否标准十字星
def __isCrissStar(k):
    v = k['TCLOSE'] / k['TOPEN']
    if v > 0.997 and v < 1.003:
        return True
    return False

#检查是否为刺透形态
##通常刺透形态 ka是阴线 kb是阳线， kb刺入越深越好
def __ctxt(ka,kb):
    if ka.PCHG <= 0 and kb.PCHG > 0:
        p = ka.TCLOSE + (ka.TOPEN-ka.TCLOSE)/2
        if kb.TCLOSE > p:
            return True
    return False

#检查是否为看涨吞没形态
#通常看涨吞没 ka是阴线 kb是阳线。
def __kztmxt(ka,kb):
    if ka.PCHG <= 0 and kb.PCHG >=0:
        return kb.TCLOSE > ka.TOPEN and kb.TOPEN <= ka.TCLOSE
    else:
        return False

if __name__ == '__main__':
    a = 1.1
    b = 1.7
    c = 1.8
    d=1.9
    print(c<a and c>b)
