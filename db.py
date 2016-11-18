# encoding:utf-8
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import mongoengine

db=mongoengine.connect('user_data')
db.drop_database('user_data')

class ZhihuUserProfile(mongoengine.Document):
	user_id = mongoengine.StringField(required=True)
	user_name = mongoengine.StringField()
	user_isfollow = mongoengine.StringField()
	user_spector = mongoengine.StringField()
	user_bio = mongoengine.StringField()
	user_followee_num = mongoengine.StringField()
	user_ask = mongoengine.StringField()
	user_answer = mongoengine.StringField()
	user_agree = mongoengine.StringField()
