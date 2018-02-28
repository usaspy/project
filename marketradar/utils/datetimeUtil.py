from datetime import datetime

def dateFormat2Format(str,format1,format2):
    dt = datetime.strptime(str, format1)
    return dt.strftime(format2)


if __name__ == '__main__':
    s= "04/01/2018"
    d = datetime.strptime(s, '%m/%d/%Y')
    print(d.strftime('%Y%m%d'))