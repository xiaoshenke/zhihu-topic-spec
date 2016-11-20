# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

import requests
import re
import json
from lxml import html

#import gevent.monkey
#gevent.monkey.patch_socket()
#gevent.monkey.patch_ssl()
#import gevent

########## FIXME: gvent make @get_followees_from_page return Http:403

from queue import add_grabid_to_queue,can_add_to_queue,get_grabid_total_number,reset_queue_head,__MAX_USER_NUMBER__

from db import ZhihuUserProfile
import sys

reload(sys)
sys.setdefaultencoding('utf8')

try:
    input = raw_input
except:
    pass

__PEOPLE_URL__ = 'https://www.zhihu.com/people/'
__FOLLOWEE__ = '/followees' 
__SPECTOR__ = '话题优秀回答者'

class ZhihuSpider():

	def __init__(self,userid,topic,headers,cookies):
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
		if r.status_code != 200:
			print('check your network！')
			return
		self.html_source = r.text
		self.tree = html.fromstring(self.html_source)
		self.followees_total_num = self.tree.xpath("//div[@class='zu-main-sidebar']//strong")[0].text
		self.parse_followees()
		return

	def parse_followees(self):
		page_num = (int(self.followees_total_num) - 1) / 20 + 1
		for i in range(page_num):
			if i == 0:
				nodes = self.tree.xpath("//div[@class='zm-profile-card zm-profile-section-item zg-clear no-hovercard']")
				for index in range(len(nodes)):
					self.parse_followee_node(nodes[index])
			else:
				self.get_followees_from_page(i)
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
 				if can_add_to_queue(userid):
 					self.save_spector(node)
 					add_grabid_to_queue(userid)
 				else:
 					pass
 			else:
 				pass		
 		return

 	def save_spector(self,node):
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

	def get_followees_from_page(self,index):
 		post_url = "https://www.zhihu.com/node/ProfileFolloweesListV2"
 		hash_id = re.findall("hash_id&quot;: &quot;(.*)&quot;},",self.html_source)[0]
 		offset = index * 20
 		_xsrf = self.tree.xpath("//input[@name='_xsrf']/@value")[0]
 		params = json.dumps({"offset": offset, "order_by": "created", "hash_id": hash_id})
 		data = {
 			'_xsrf': _xsrf,
 			'method': "next",
 			'params': params
 		}
 		referer_url = __PEOPLE_URL__+'%s'%self.userid + __FOLLOWEE__
 		header = {
 			'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
 			'Host': "www.zhihu.com",
 			'Referer': referer_url,
 			'Origin': "https://www.zhihu.com",
 			'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
 			'Content-Length': "132",
 			'Accept-Language': "zh-CN,zh;q=0.8,en;q=0.6",
 			'Accept-Encoding': "gzip, deflate, br"
 		}
 		r_post = requests.post(post_url,cookies=self.cookies,data=data, headers=header,verify=True)
 		if r_post.status_code == 200:
 			followee_list = r_post.json()["msg"]
 			for j in range(min(int(self.followees_total_num) - index * 20, 20)):
 				self.parse_followee_node(html.fromstring(followee_list[j]))
 		else:
 			print('error in get porfileFolloweesListV2 page%s'%index)
