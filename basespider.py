# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

import re
from lxml import html
from db import ZhihuUserProfile

import sys
reload(sys)
sys.setdefaultencoding('utf8')

from queue import add_grabid_to_queue,can_add_to_queue

from share import __SPECTOR__,spector_lock

# 有两个子类 AjaxSpider,Spider。两者的区别是一个是首页数据,一个是翻页数据。但是每条item的html是一样的,因此parse_node函数可以共用
# 定义了两个基函数 parse_follwee_node
class BaseSpider():
	def __init__(self,topic):
		self.topic = topic
		return

	def parse_followee_node(self,node):	
 		name = node.xpath(".//a[@class='zm-item-link-avatar']/@title")[0]
 		badge_summary = node.xpath(".//span[@class='badge-summary']//a")
 		if not badge_summary:
 			return
 		spector = badge_summary[0].text.strip()
 		if spector:
 			spector_utf8 = spector.encode('utf-8')
 			if not re.search(r'%s'%__SPECTOR__.strip(),spector_utf8): #有的知乎用户可能有超过一个话题优秀回答者头衔
 				return
  			if re.search(r'%s'%self.topic.strip(),spector_utf8): #这里必须要encode成utf-8格式
  				name = node.xpath(".//span[@class='author-link-line']//a[@class='zg-link author-link']")[0].text	
 				link = node.xpath(".//span[@class='author-link-line']//a/@href")[0]	
 				people_id = re.search(r'(?<=people[/]).+',link)
 				if not people_id:
 					return
 				userid = people_id.group(0)
 				can_add = False
 				spector_lock.acquire()     #加锁
 				can_add = can_add_to_queue(userid)
 				if can_add:
 					add_grabid_to_queue(userid)
 					pass
 				else:
 					pass
 				spector_lock.release() #释放
 				if can_add:
 					self.save_spector(node)
 			else:
 				pass		
 		return

	def save_spector(self,node):
		print('begin save_spector')
		link = node.xpath(".//span[@class='author-link-line']//a/@href")[0]
 		user_id = 'invalid user'
 		people_id = re.search(r'(?<=people[/]).+',link)
 		if people_id:
 			user_id = people_id.group(0)
 		else:
 			pass
 		user_name = node.xpath(".//a[@class='zm-item-link-avatar']/@title")[0]
 		user_isfollow = "False"
	 	if node.xpath(".//button[@class='zg-btn zg-btn-unfollow zm-rich-follow-btn small nth-0']"):
 			user_isfollow = "True"
 		elif node.xpath(".//button[@class='zg-btn zg-btn-unfollow zm-rich-follow-btn small']"):
 			user_isfollow = "True"
 		else:
 			pass
 		user_spector = "not a spector"
 		badge_summary = node.xpath(".//span[@class='badge-summary']//a")
 		if badge_summary:
 			user_spector = badge_summary[0].text.strip()
	 	else:
 			pass
 		user_bio = "no bio"
 		bio = node.xpath(".//span[@class='bio']")
 		if bio:
 			user_bio = bio[0].text #unicode-->utf8??
 		else:
 			pass
 		user_followee_num = "0 关注者"
 		user_ask = "0 提问"
 		user_answer = "0 回答"
 		user_agree = "0 赞同"
	 	details = node.xpath(".//a[@class='zg-link-gray-normal']")
 		if details:
 			user_followee_num = details[0].text
 			user_ask = details[1].text
 			user_answer = details[2].text
 			user_agree = details[3].text
	 	else:
 			pass
 		user = ZhihuUserProfile(
 			user_id=user_id,
 			user_name=user_name,
 			user_isfollow=user_isfollow,
 			user_spector=user_spector,
 			user_bio=user_bio,
 			user_followee_num=user_followee_num,
 			user_ask=user_ask,
 			user_answer=user_answer,
 			user_agree=user_agree)
 		user.save()
 		print('save user:%s'%user_name)
 		return