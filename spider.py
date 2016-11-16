# encoding:utf-8

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
			print('检查你的网路！')
			return
		r.encoding = 'gbk'
		content = r.text
		tree = html.fromstring(content)
		userid = self.process_xpath_source(tree.xpath("//span[@class='token']/text()"))
		self.grabbed_id.append(userid)
		print('test get_self_userid %s'%userid)
		return

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
		
 	def deal_followee_node(self,node):
 		print('test deal_followee_node node: %s'%node)
 		spector = node.xpath("//span[@class='badge-summary']//a")[0].text.strip()
 		if spector:
 			selfstring = self.topic.strip()+self.spector.strip()
  			if re.search(r'%s'%selfstring,spector.encode('utf-8')): #这里必须要encode成utf-8格式
  				name = node.xpath("//span[@class='author-link-line']//a[@class='zg-link author-link']")[0].text	
 				print('test we find a %s spector,name %s'%(self.topic,name))
 				link = node.xpath("//span[@class='author-link-line']//a/@href")[0]	
 				userid = re.search(r'(?<=people[/]).+',link).group(0)
 				self.grabbed_id.append(userid) # 存入抓取的id		
 		return

	# Todo: 模拟下拉加载更多来拿到所有的关注者
	def get_followees_from(self,html_source):
		print('test get_followees_from %s'%html_source)
		tree = html.fromstring(html_source)
		followee_num = tree.xpath("//div[@class='zu-main-sidebar']//strong")[0].text
		for i in xrange((int(followee_num) - 1) / 20 + 1):
			if i == 0:
				continue
				for node in tree.xpath("//div[@class='zm-list-content-medium']"):
					self.deal_followee_node(node)
			else:
				post_url = "http://www.zhihu.com/node/ProfileFolloweesListV2"
                _xsrf = tree.xpath("//input[@name='_xsrf']/@value")[0]
                print('test _xsrf is %s'%_xsrf)
                offset = i * 20
                hash_id = re.findall("hash_id&quot;: &quot;(.*)&quot;},", html_source)[0]
                print('test hash_id %s'%hash_id)
                params = json.dumps({"offset": offset, "order_by": "created", "hash_id": hash_id})
                data = {
                    '_xsrf': _xsrf,
                    'method': "next",
                    'params': params
                }
                id = self.current_grab_id
                referer_url = self.people_url+'%s'%id+self.followee
                header = {
                	'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0",
                	'Host': "www.zhihu.com",
                	'Referer': referer_url
                }
                r_post = requests.post(post_url,data=data, headers=self.headers,verify=False)
                print('test r_post result %s'%r_post)
                followee_list = r_post.json()["msg"]
                for j in xrange(min(followee_num - i * 20, 20)):
                	self.deal_followee_node(html.fromstring(followee_list[j])) #FIXME: mabi被封了...
		return

	#parse user profile
	def parse_user_profile(self, html_source,first):
		self.get_followees_from(html_source)
        

	# 广度遍历grabbed_id 直到结束
	def grab_topic(self,topic):
		current_index = 0
		while (current_index < len(self.grabbed_id) and current_index < 50):
			self.current_grab_id = self.grabbed_id[current_index]
			if current_index ==0:
				self.grab_from_currentid(True)
			else:
				self.grab_from_currentid(False)
			current_index = current_index+1
		if len(self.grabbed_id) == 1:
			return
			#userid = input('you are not following any topic:%s spector,you should type a userid\n> '%topic)
			#self.grabbed_id[0] = userid
			#self.grab_topic(topic)
		else:
			pass # print or analize the data
		return

	# TODO
	def store_data_to_mongo(self):
		return
