# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

import requests
import re
import json
from lxml import html

from queue import add_grabid_to_queue,in_grab_queue,is_queue_empty,get_grabid_total_number,reset_queue_head,__MAX_USER_NUMBER__,get_grabid_from_queue

from db import ZhihuUserProfile
import sys

reload(sys)
sys.setdefaultencoding('utf8')

try:
    input = raw_input
except:
    pass

__max_user_number__ = 20

class ZhihuSpider():
	people_url = 'https://www.zhihu.com/people/'
	followee = '/followees' 
	spector = '话题优秀回答者'
	current_grab_id = -1

	def get_self_userid(self):
		url = "https://www.zhihu.com/settings/profile"
		try:
			r = requests.get(url,cookies=self.cookies,headers=self.headers,verify=False)
		except:
			print('requests get setting/profile fail')
			return
		if r.status_code != 200:
			print('check your internet！')
			return
		#r.encoding = 'gbk'
		content = r.text
		tree = html.fromstring(content)
		userid = self.process_xpath_source(tree.xpath("//span[@class='token']/text()"))
		reset_queue_head(userid)
		return

	# help func to get the first xpath result
	def process_xpath_source(self,source):
		if source:
			return source[0]
		else:
			return ''

	def __init__(self,headers,cookies):
		self.headers = headers
		self.cookies = cookies
		self.rootid = self.get_self_userid()
		self.topic = input('请输入需要抓取的领域\n>  ')
		self.grab_topic(self.topic)


	def grab_from_currentid(self):
		id = self.current_grab_id
		url = self.people_url+'%s'%id+self.followee
		try:
			r = requests.get(url,cookies=self.cookies,headers=self.headers,verify=False)
		except:
			print('requests get user:%d profile fail'%id)
			return
		if r.status_code != 200:
			print('check your network！')
			return
		content = r.text
		self.parse_user_profile(content)
		return 

 	def deal_followee_node(self,node):	
 		name = node.xpath(".//a[@class='zm-item-link-avatar']/@title")[0]
 		badge_summary = node.xpath(".//span[@class='badge-summary']//a")
 		if not badge_summary:
 			return
 		spector = badge_summary[0].text.strip()
 		if spector:
 			spector_utf8 = spector.encode('utf-8')
 			if not re.search(r'%s'%self.spector.strip(),spector_utf8): # 有的知乎用户可能有超过一个话题优秀回答者头衔
 				return
  			if re.search(r'%s'%self.topic.strip(),spector_utf8): #这里必须要encode成utf-8格式
  				name = node.xpath(".//span[@class='author-link-line']//a[@class='zg-link author-link']")[0].text	
 				link = node.xpath(".//span[@class='author-link-line']//a/@href")[0]	
 				people_id = re.search(r'(?<=people[/]).+',link)
 				if not people_id:
 					return
 				userid = people_id.group(0)
 				if in_grab_queue(userid):
 					pass
 				else:
 					if get_grabid_total_number() > __MAX_USER_NUMBER__:
 						return
 					self.save_spector_node(node)
 					if not add_grabid_to_queue(userid):
 						print('add grabid to queue error')
 			else:
 				pass		
 		return

 	# 记录的内容:用户uid,用户id,用户的个人说明,用户的xx话题优秀回答者,是否已关注,被关注数,提问数,回答数,赞同数 
 	def save_spector_node(self,node):
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

 	def get_followees_node_from_page(self,index,followee_num,html_source,tree):
 		post_url = "https://www.zhihu.com/node/ProfileFolloweesListV2"
 		hash_id=re.findall("hash_id&quot;: &quot;(.*)&quot;},",html_source)[0]
 		offset = index*20
 		_xsrf = tree.xpath("//input[@name='_xsrf']/@value")[0]
 		params = json.dumps({"offset": offset, "order_by": "created", "hash_id": hash_id})
 		data = {
 			'_xsrf': _xsrf,
 			'method': "next",
 			'params': params
 		}
 		id = self.current_grab_id
 		referer_url = self.people_url+'%s'%id+self.followee
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
 			for j in range(min(int(followee_num) - index * 20, 20)):
 				self.deal_followee_node(html.fromstring(followee_list[j]))
 		else:
 			print('error in get porfileFolloweesListV2 page%s'%index)


 	# followees page has a 'scroll down to load more' effect,so we have to deal with that to get "followee node" list[]
	def get_followees_from(self,html_source):
		tree = html.fromstring(html_source)
		followee_num = tree.xpath("//div[@class='zu-main-sidebar']//strong")[0].text
		followee_page_num = (int(followee_num) - 1) / 20 + 1
		for i in range(followee_page_num):
			if i == 0:
				nodes = tree.xpath("//div[@class='zm-profile-card zm-profile-section-item zg-clear no-hovercard']")
				for index in range(len(nodes)):
					self.deal_followee_node(nodes[index])
			else:
				self.get_followees_node_from_page(i,followee_num,html_source,tree)
		return

	def parse_user_profile(self, html_source):
		self.get_followees_from(html_source)
        

	# grab some topic for eg,Python,数学
	def grab_topic(self,topic):
		current_index = 0
		while not is_queue_empty() and get_grabid_total_number() < __MAX_USER_NUMBER__:
			self.current_grab_id = get_grabid_from_queue()
			print('begin to grab index:%s user, userid:%s'%(current_index,self.current_grab_id))
			self.grab_from_currentid()
			current_index = current_index+1
		if get_grabid_total_number == 1:
			# we can't find any spector in our followees,so we type in a specific userid,then begin with him
			userid = input('you are not following any topic:%s spector,you should type in a userid who is a spector\n> '%self.topic)
			reset_queue_head(userid)
			self.grab_topic(self.topic)
		else:
			self.print_all_grabbed_user()
		return

	def print_all_grabbed_user(self):
		print('we grab user as below:')
		for user in ZhihuUserProfile.objects:
			print('%s, %s, %s, %s, 是否已关注:%s'%(user.user_name,user.user_spector,user.user_followee_num,user.user_agree,user.user_isfollow))
		return
