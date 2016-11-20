# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re
import time
from lxml import html
import os.path
from spider import ZhihuSpider
try:
    from PIL import Image
except:
    pass
from db import ZhihuUserProfile
from queue import __MAX_USER_NUMBER__,reset_queue_head,get_grabid_total_number,is_queue_empty,get_grabid_from_queue

agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
headers = {
    "Host": "www.zhihu.com",
    "Referer": "https://www.zhihu.com/",
    'User-Agent': agent
}

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie 未能加载")


def get_xsrf():
    '''_xsrf 是一个动态变化的参数'''
    index_url = 'http://www.zhihu.com'
    # 获取登录时需要用到的_xsrf
    index_page = session.get(index_url, headers=headers)
    html = index_page.text
    pattern = r'name="_xsrf" value="(.*?)"'
    # 这里的_xsrf 返回的是一个list
    _xsrf = re.findall(pattern, html)
    return _xsrf[0]


# 获取验证码
def get_captcha():
    t = str(int(time.time() * 1000))
    captcha_url = 'http://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
    r = session.get(captcha_url, headers=headers)
    with open('captcha.jpg', 'wb') as f:
        f.write(r.content)
        f.close()
    # 用pillow 的 Image 显示验证码
    # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    captcha = input("please input the captcha\n>")
    return captcha


def is_login():
    # 通过查看用户个人信息来判断是否已经登录
    url = "https://www.zhihu.com/settings/profile"
    login_res = session.get(url, headers=headers, allow_redirects=False)
    print('test is_login %s'%login_res)
    if login_res.status_code == 200:
        return True
    else:
        return False


def login(account,password):
    # 通过输入的用户名判断是否是手机号
    if re.match(r"^1\d{10}$", account):
        print("手机号登录 \n")
        post_url = 'http://www.zhihu.com/login/phone_num'
        postdata = {
            '_xsrf': get_xsrf(),
            'password': password,
            'remember_me': 'true',
            'phone_num': account,
        }
    else:
        if "@" in account:
            print("邮箱登录 \n")
        else:
            print("你的账号输入有问题，请重新登录")
            return 0
        post_url = 'http://www.zhihu.com/login/email'
        postdata = {
            '_xsrf': get_xsrf(),
            'password': password,
            'remember_me': 'true',
            'email': account,
        }
    try:
        # 不需要验证码直接登录成功
        login_page = session.post(post_url, data=postdata, headers=headers)
        login_code = login_page.text
        print('test login_code:%s'%login_page)
        #print(login_page.status_code)
        #print(login_code)
    except:
        # 需要输入验证码后才能登录成功
        postdata["captcha"] = get_captcha()
        login_page = session.post(post_url, data=postdata, headers=headers)
        login_code = eval(login_page.text)
        print(login_code['msg'])
    session.cookies.save()

try:
    input = raw_input
except:
    pass

# 知乎爬虫引擎
class ZhihuSpiderStarter():
    rootid = 'invalid'
    rootid_is_spector = False # TODO:若该用户是spector 则要存入数据库

    def __init__(self,header,cookie):
        self.header = header
        self.cookie = cookie
        if not self.get_self_userid():
            return
        self.topic = input('请输入需要抓取的领域\n>  ')
        self.begin_spider_loop()
        return

    def begin_spider_loop(self):
        while not is_queue_empty() and get_grabid_total_number() < __MAX_USER_NUMBER__:
            userid = get_grabid_from_queue()
            spider = ZhihuSpider(userid,self.topic,self.header,self.cookie)
            spider.do_spider()
        if get_grabid_total_number() == 1:
            userid = input('you are not following any topic:%s spector,you should type in a userid who is a spector\n> '%self.topic)
            reset_queue_head(userid)
            self.begin_spider_loop()
        else:
            self.print_all_grabbed_user()
        return

    def print_all_grabbed_user(self):
        print('we grab user as below:')
        for user in ZhihuUserProfile.objects:
            print('%s, %s, %s, %s, 是否已关注:%s'%(user.user_name,user.user_spector,user.user_followee_num,user.user_agree,user.user_isfollow))
        return

    def get_self_userid(self):
        url = "https://www.zhihu.com/settings/profile"
        try:
            r =  requests.get(url,cookies=self.cookie,headers=self.header,verify=False)
        except:
            print('get setting fail')
            return False
        if r.status_code != 200:
            print('check your internet！')
            return False
        content = r.text
        tree = html.fromstring(content)
        userid = self.process_xpath_source(tree.xpath("//span[@class='token']/text()"))
        reset_queue_head(userid)
        return True

    def process_xpath_source(self,source):
        if source:
            return source[0]
        else:
            return ''

if __name__ == '__main__':
    while (not is_login()):
        print('您未登录')
        account = input('请输入你的用户名\n>  ')
        password = input("请输入你的密码\n>  ")
        login(account, password)
    print('您已登录')

    ZhihuSpiderStarter(headers,session.cookies)
