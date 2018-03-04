from marketradar.utils.Exception import FilterError

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

#[持续缩量]
#规则：
#1.
#2.计算前一段时间（ybts-fdts）的成交量均量
#3.放大天数内每日成交量至少是前期平均量的multiple=5倍
def rule_1003(df, ybts, fdts, multiple):
    if df.iloc[:,0].size != ybts:
        return False

    series = df["VOTURNOVER"]
    #step.2
    avg_vol = series[fdts:].sum()/(ybts-fdts)
    # step.3
    for i in range(0,fdts):
        if series[i]/avg_vol < multiple:#如果最近几天成交量没有持续放大，则不满足条件，返回False
            return False
    return True