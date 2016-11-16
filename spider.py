# encoding:utf-8

import requests
from lxml import html
from db import ZhihuUserProfile

try:
    input = raw_input
except:
    pass


class ZhihuSpider():
	''' 计划存入的信息包括 该用户的大学信息 性别 关注者数 被关注者数 获得的赞 分享 收藏等 供后续进行数据分析
	'''
	people_url = 'https://www.zhihu.com/people/'
	followee = '/followees'
	grabbed_id = []  #grabbed userid 

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
		''' 先从followee开始爬某个关注者是否是某个领域的优秀回答者 比如python。然后遍历该用户的关注里的对应
		领域的优秀回答者。广度遍历，人数达到500或者遍历完所有优秀回答者视为成功。
		若你的关注中没有该领域的回答者。让用户输入一个userid，以它作为根开始遍历
		'''
		self.headers = headers
		self.cookies = cookies
		self.rootid = self.get_self_userid()
		topic = input('请输入需要抓取的领域\n>  ')
		self.grab_topic(topic)


	# grab https://www.zhihu.com/people/userid/followees page from internet
	# 若是第一个(第三个参数为true) 由于是整个爬虫的root。该root用户的信息不存入数据库
	# 否则存入数据库
	def grab_from_id(self,id,first):
		url = self.people_url+'%d'%id+self.followee
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

	#parse user profile
	def parse_user_profile(self, html_source):
		self.user_name = ''
        self.fuser_gender = ''
        self.user_location = ''
        self.user_followees = ''
        self.user_be_agreed = ''
        self.user_be_thanked = ''
        self.user_education_school = ''
        self.user_education_subject = ''
        self.user_employment = ''
        self.user_employment_extra = ''
        self.user_info = ''
        self.user_intro = ''
		tree = html.fromstring(html_source)
		# parse the html via lxml
        self.user_name = self.process_xpath_source(
            tree.xpath("//a[@class='name']/text()"))
        self.user_location = self.process_xpath_source(
            tree.xpath("//span[@class='location item']/@title"))
        self.user_gender = self.process_xpath_source(
            tree.xpath("//span[@class='item gender']/i/@class"))
        if "female" in self.user_gender and self.user_gender:
            self.user_gender = "female"
        else:
            self.user_gender = "male"
        self.user_employment = self.process_xpath_source(
            tree.xpath("//span[@class='employment item']/@title"))
        self.user_employment_extra = self.process_xpath_source(
            tree.xpath("//span[@class='position item']/@title"))
        self.user_education_school = self.process_xpath_source(
            tree.xpath("//span[@class='education item']/@title"))
        self.user_education_subject = self.process_xpath_source(
            tree.xpath("//span[@class='education-extra item']/@title"))
        try:
            self.user_followees = tree.xpath(
                "//div[@class='zu-main-sidebar']//strong")[0].text
        except:
            return
        self.user_be_agreed = self.process_xpath_source(tree.xpath(
            "//span[@class='zm-profile-header-user-agree']/strong/text()"))
        self.user_be_thanked = self.process_xpath_source(tree.xpath(
            "//span[@class='zm-profile-header-user-thanks']/strong/text()"))
        self.user_info = self.process_xpath_source(
            tree.xpath("//span[@class='bio']/@title"))
        self.user_intro = self.process_xpath_source(
            tree.xpath("//span[@class='content']/text()"))
        if not first:
        	self.store_data_to_mongo()
		return

	# 广度遍历grabbed_id 直到结束
	def grab_topic(self,topic):
		current_index = 0
		while (current_index < len(self.grabbed_id) and current_index < 50):
			if current_index ==0:
				self.grab_from_id(self.grabbed_id[current_index],true)
			else:
				self.grab_from_id(self.grabbed_id[current_index],false)
			current_index = current_index+1
		if len(self.grabbed_id) == 1:
			userid = input('you are not following any topic:%s spector,you should type a userid\n> '%topic)
			self.grabbed_id[0] = userid
			self.grab_topic(topic)
		else:
			pass # print or analize the data
		return

	# TODO
	def store_data_to_mongo(self):
        '''
        store the data in mongo
        '''
        return
