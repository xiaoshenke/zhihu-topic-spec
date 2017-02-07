# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

import requests
import re
import json
from lxml import html
import threading

import sys
reload(sys)
sys.setdefaultencoding('utf8')

try:
    input = raw_input
except:
    pass

#import gevent.monkey
#gevent.monkey.patch_socket()
#gevent.monkey.patch_ssl()
#import gevent
########## FIXME: gvent make @get_followees_from_page return Http:403

## FIXME: 有很多check your network 错误
## TODO: 确保某个网络请求正常 --> 遇到429错误的时候 放入重试列表

from basespider import BaseSpider 
from queue import add_grabid_to_queue,can_add_to_queue
from ajaxspider import AjaxSpider
from share import __PEOPLE_URL__,__FOLLOWEE__
from db import ZhihuUserProfile

class GetFolloweesThread(threading.Thread):
	def __init__(self,ajaxSpider):
		self.ajaxSpider = ajaxSpider
		threading.Thread.__init__(self)
		return

	def run(self):
		self.ajaxSpider.do_spider()
		return	   

class ZhihuSpider(BaseSpider):

	def __init__(self,userid,topic,headers,cookies):
		BaseSpider.__init__(self,topic)
		self.headers = headers
		self.cookies = cookies
		self.userid = userid
		self.topic = topic

	def do_spider(self):
		url = __PEOPLE_URL__+'%s'%self.userid+__FOLLOWEE__
		try:
			r = requests.get(url,cookies=self.cookies,headers=self.headers,verify=False)
		except:
			print('requests get user:%d profile fail'%self.userid)
			return
		print('do_spider return_code %s'%r.status_code)
		if r.status_code != 200:
			print('check your network')
			return
		self.html_source = r.text
		self.tree = html.fromstring(self.html_source)
		self.parse_followees()
		return

	##老版的ui
	def parse_followees(self):
		strong = self.tree.xpath("//div[@class='zu-main-sidebar']//strong")
		if not strong:
			return False
		self.followees_total_num = strong[0].text
		if not self.followees_total_num:
			return False
		page_num = (int(self.followees_total_num) - 1) / 20 + 1
		nodes = self.tree.xpath("//div[@class='zm-profile-card zm-profile-section-item zg-clear no-hovercard']")
		if not nodes:
			return False
		for index in range(len(nodes)):
			self.parse_followee_node(nodes[index])
		for i in range(1,page_num):
			ajaxSpider = AjaxSpider(self.userid,self.topic,self.html_source,i,self.followees_total_num,self.cookies)
			thread = GetFolloweesThread(ajaxSpider)
			thread.start()
		return True
