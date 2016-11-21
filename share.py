# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

# 定义了一些共享变量 

import threading

__PEOPLE_URL__ = 'https://www.zhihu.com/people/'
__FOLLOWEE__ = '/followees' 
__SPECTOR__ = '话题优秀回答者'

# 数据存取锁
spector_lock = threading.Lock()

# 是否开始抓取下一个人条件变量
ajaxspider_condition = threading.Condition()