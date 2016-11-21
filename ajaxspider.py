# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

# 如果用户的关注人超过了一页 需要调用新的do_spider函数
from lxml import html
import requests
import re
import json


from basespider import BaseSpider 
from share import __PEOPLE_URL__,__FOLLOWEE__

class AjaxSpider(BaseSpider):
	def __init__(self,userid,topic,html_source,index,total_followee_num,cookie):
		BaseSpider.__init__(self,topic)
		self.userid = userid
		self.html_source = html_source
		self.tree = html.fromstring(self.html_source)
		self.index = index
		self.total_followee_num = total_followee_num
		self.cookies = cookie
		return

	def do_spider(self):
		print('AjaxSpider do_spider index:%s'%self.index)
		post_url = "https://www.zhihu.com/node/ProfileFolloweesListV2"
 		hash_id = re.findall("hash_id&quot;: &quot;(.*)&quot;},",self.html_source)[0]
 		offset = self.index * 20
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
 		print('index:%s ret.status_code %s'%(self.index,r_post.status_code))
 		if r_post.status_code == 200:
 			followee_list = r_post.json()["msg"]
 			for j in range(min(int(self.total_followee_num) - self.index * 20, 20)):
 				self.parse_followee_node(html.fromstring(followee_list[j]))
 		else:
 			print('error in get porfileFolloweesListV2 page%s'%self.index)
		return

