# encoding:utf-8

import requests
#from lxml import html
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
		#tree = html.fromstring(content)
		#print(content)
		return

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


	# TODO: to be finished
	def grab_from_id(id):
		''' grab from id ,then add to @grabbed_id
		'''
		return 

	# 广度遍历grabbed_id 直到结束
	def grab_topic(self,topic):
		current_index = 0
		while (current_index < len(self.grabbed_id) and current_index < 50):
			grab_from_id(self.grabbed_id[current_index])
			current_index = current_index+1
		if len(self.grabbed_id) == 1:
			userid = input('you are not following any topic:%s spector,you should type a userid\n> '%topic)
			self.grabbed_id[0] = userid
			self.grab_topic(topic)
		else:
			pass # print or analize the data
		return
