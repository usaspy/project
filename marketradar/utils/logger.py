import logging
import sys

# 获取logger实例，如果参数为空则返回root logger
logger = logging.getLogger(__name__)
# 指定logger输出格式
formatter = logging.Formatter('%(asctime)s [%(levelname)-8s]: %(message)s')

# 文件日志
file_handler = logging.FileHandler("d:\marketradar.log")
file_handler.setFormatter(formatter)
# 控制台日志
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# 为logger添加的日志处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 指定日志的最低输出级别，默认为WARN级别
logger.setLevel(logging.DEBUG)

# 移除一些日志处理器
#logger.removeHandler(file_handler)
