from marketradar.utils.Exception import FilterError
import numpy as np

#[温和放量]
#规则：
#1.确定fdts放大天数
#2.计算前一段时间（ybts-fdts）的成交量均量
#3.放大天数内每日成交量超过前一日的成交量
#4.放大天数内每日成交量至少是前期平均量的multiple=2倍
def rule_1001(df, ybts, fdts, multiple):
    if df.iloc[:,0].size != ybts:
        return False

    series = df["VOTURNOVER"]
    #step.3
    for i in range(0,fdts):
        if series[i] < series[i+1]:#如果最近几天成交量没有持续放大，则不满足条件，返回False
            return False
    #step.2
    avg_vol = series[fdts:].sum()/(ybts-fdts)
    # step.4
    for i in range(0,fdts):
        if series[i]/avg_vol < multiple:#如果最近几天成交量没有持续放大，则不满足条件，返回False
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
#1.计算前一段时间（ybts-1）的成交量均量avg_vol
#2.过去每一天的成交量都都不会很大，最多只有成交均量avg_vol的2倍
#3.今日的成交量是昨日的multiple=3倍以上
#4.今日的成交量是前期(ybts-1)成交均量的2倍以上
#4.T-3,T-2,T-1,三日的成交量呈典型的持续缩量态势
def rule_1003(df, ybts, multiple, cxsl='true'):
    if df.iloc[:,0].size != ybts:
        return False

    series = df["VOTURNOVER"]
    #step.3
    if series[0]/series[1] < multiple:
        return False
    #step.1
    avg_vol = series[1:].sum()/(ybts-1)
    #step.2
    for i in series[1:]:
        if series[i]/avg_vol > 2:
            return False
    # step.4
    if series[0]/avg_vol < 2:
        return False
    # step.5
    if cxsl == 'true':
        for i in range(1, 4):
            if series[i] > series[i+1]: #若没有持续缩量，则不满足条件
                return False
    return True

#[启明星/十字启明星# ]
#规则：
#满足启明星的几个基本条件:
#1.行情经过多日的下跌，K2日出现十字星线（收/开盘价一致）
#2.K2相对K1的实体必须有向下跳空缺口（另外如果K3相对K2的实体也有向上跳空缺口则更佳）
#3.K1成交量较小，预示下跌势头已经趋缓，K3成交量放大
def rule_2001(df, tag,isStandard,throwBaby,k3up,vol_increase):
    if tag == '2d':
        if df.iloc[:, 0].size != 2:
            return False
        k2 = df.iloc[0] #今天 返回一个series 如果是iloc[0:0]返回的就是dataframe
        k1 = df.iloc[1] #昨天

        # 检查是否有向下跳空缺口
        if (k1['TCLOSE'] > k2['TCLOSE'] and k1['TCLOSE'] > k2['TOPEN'] and k1['TOPEN'] > k2['TCLOSE'] and k1['TOPEN'] > k2['TOPEN']) != True:
            return False

        # 检查是否为标准十字星
        if __isCrissStar(k2) != True:
            return False
        return True

    if tag == '3d':
        if df.iloc[:, 0].size != 3:
            return False
        k3 = df.iloc[0]  # 今天 返回一个series 如果是iloc[0:0]返回的就是dataframe
        k2 = df.iloc[1]  # 昨天 返回一个series 如果是iloc[0:0]返回的就是dataframe
        k1 = df.iloc[2]  # 前天

        # 检查是否有向下跳空缺口
        if (k1['TCLOSE'] > k2['TCLOSE'] and k1['TCLOSE'] > k2['TOPEN'] and k1['TOPEN'] > k2['TCLOSE'] and k1['TOPEN'] > k2['TOPEN']) != True:
            return False
        #k3日股价是上涨的
        if (k3['TCLOSE'] > k2['TCLOSE'] and k3['TCLOSE'] > k2['TOPEN']) != True:
            return False
        #如果k3日的最低价不能低于k2日的最低价
        if k3.LOW < k2.LOW:
            return False
        # 需要检查是否有向上跳空缺口（弃婴形态）
        if throwBaby == 'yes':
            if (k3['TCLOSE'] > k2['TCLOSE'] and k3['TCLOSE'] > k2['TOPEN'] and k3['TOPEN'] > k2['TCLOSE'] and k3['TOPEN'] > k2['TOPEN']) != True:
                return False
        # 需要检查是否为标准十字星
        if isStandard == 'yes':
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
    v = k['TCLOSE'] - k['TOPEN']
    if abs(v) < 1E-2:
        return True
    return False

#检查是否为刺透形态
##通常刺透形态 ka是阴线 kb是阳线， kb刺入越深越好
def __ctxt(ka,kb):
    if ka.TCLOSE > ka.TOPEN:
        p = ka.TOPEN + (ka.TCLOSE-ka.TOPEN)/2
        if kb.TCLOSE > p:
            return True
    if ka.TCLOSE <= ka.TOPEN:
        p = ka.TCLOSE + (ka.TOPEN-ka.TCLOSE)/2
        if kb.TCLOSE > p:
            return True
    return False

#检查是否为看涨吞没形态
#通常看涨吞没 ka是阴线 kb是阳线。
def __kztmxt(ka,kb):
    if ka.PCHG <= 0 and kb.PCHG >=0:
        return kb.TCLOSE > ka.TOPEN
    else:
        return False

if __name__ == '__main__':
    a = 1.1
    b = 1.7
    c = 1.8
    d=1.9
    print(c<a and c>b)
