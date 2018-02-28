from marketradar.utils.Exception import FilterError

#[温和放量]
#检查步骤：
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
#检查步骤：
#1.确定fdts放大天数
#2.计算前一段时间（ybts-fdts）的成交量均量
#3.放大天数内每日成交量至少是前期平均量的multiple=5倍
def rule_1002(df, ybts, fdts, multiple):
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