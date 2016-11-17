# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

import requests
import re
import json
from lxml import html
from db import ZhihuUserProfile
import sys

reload(sys)
sys.setdefaultencoding('utf8')

try:
    input = raw_input
except:
    pass


class ZhihuSpider():
	people_url = 'https://www.zhihu.com/people/'
	followee = '/followees'
	grabbed_id = []  
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
		self.grabbed_id.append(userid)
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


	# grab https://www.zhihu.com/people/userid/followees page from internet
	# 若是第一个(第三个参数为true) 由于是整个爬虫的root。该root用户的信息不存入数据库
	# 否则存入数据库
	def grab_from_currentid(self,first):
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
		self.parse_user_profile(content,first)
		return 
	
	# from followee node get information such as username,userid,if user is a topic spector	
 	def deal_followee_node(self,node):
 		#name = node.xpath("//span[@class='author-link-line']//a[@class='zg-link author-link']")[0].text	
 		name = node.xpath(".//a[@class='zm-item-link-avatar']/@title")[0]
 		#print('deal_followee_node name %s'%name)
 		badge_summary = node.xpath(".//span[@class='badge-summary']//a")
 		if not badge_summary:
 			return
 		spector = badge_summary[0].text.strip()
 		if spector:
 			#print('find a user who is %s spector'%spector)
 			selfstring = self.topic.strip()+self.spector.strip()
  			if re.search(r'%s'%selfstring,spector.encode('utf-8')): #这里必须要encode成utf-8格式
  				name = node.xpath(".//span[@class='author-link-line']//a[@class='zg-link author-link']")[0].text	
 				print('we find a %s spector,name %s'%(self.topic,name))
 				link = node.xpath(".//span[@class='author-link-line']//a/@href")[0]	
 				people_id = re.search(r'(?<=people[/]).+',link)
 				if not people_id:
 					return
 				userid = people_id.group(0)
 				if not userid in self.grabbed_id:
 					self.grabbed_id.append(userid) # 存入抓取的id
 				else:
 					pass
 			else:
 				pass		
 		return

 	def get_followees_node_from_page(self,index,followee_num,html_source,tree):
 		post_url = "https://www.zhihu.com/node/ProfileFolloweesListV2"
 		hash_id=re.findall("hash_id&quot;: &quot;(.*)&quot;},",html_source)[0]
 		offset = index*20
 		#tree = html.fromstring(html_source)
 		#tree2 = html.fromstring(html_source)
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
				#nodes = tree.xpath("//div[@class='zm-list-content-medium']")
				nodes = tree.xpath("//div[@class='zm-profile-card zm-profile-section-item zg-clear no-hovercard']")
				for index in range(len(nodes)):
					self.deal_followee_node(nodes[index])
			else:
				self.get_followees_node_from_page(i,followee_num,html_source,tree)
		return

	# parse user profile,if 'first' is True we don't save it to db,other wise we should save it
	def parse_user_profile(self, html_source,first):
		self.get_followees_from(html_source)
        

	# grab some topic for eg,Python,数学
	def grab_topic(self,topic):
		current_index = 0
		while (current_index < len(self.grabbed_id) and len(self.grabbed_id) < 20):
			self.current_grab_id = self.grabbed_id[current_index]
			print('begin to grab index:%s user, userid:%s'%(current_index,self.current_grab_id))
			if current_index ==0:
				self.grab_from_currentid(True)
			else:
				self.grab_from_currentid(False)
			current_index = current_index+1
		if len(self.grabbed_id) == 1:
			# we can't find any spector in our followees,so we type in a specific userid,then begin with him
			userid = input('you are not following any topic:%s spector,you should type in a userid who is a spector\n> '%self.topic)
			self.grabbed_id[0] = userid
			self.grab_topic(self.topic)
		else:
			pass 
		return

	# Todo
	def store_data_to_mongo(self):
		return
