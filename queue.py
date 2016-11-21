# encoding:utf-8
__author__ = 'wuxian'
__version__ = '0.1'

from Queue import Queue
import sys

reload(sys)
sys.setdefaultencoding('utf8')

__MAX_USER_NUMBER__ = 20

grab_id_queue = Queue(__MAX_USER_NUMBER__)
grab_id_num = 0
grad_id_list = []

# 返回是否加入成功
def add_grabid_to_queue(grab_id):
	global grab_id_num
	global __MAX_USER_NUMBER__
	global grad_id_list
	global grab_id_num
	global grab_id_queue
	if grab_id_num > __MAX_USER_NUMBER__:
		return False
	else:
		grad_id_list.append(grab_id)
		grab_id_queue.put(grab_id)
		grab_id_num = grab_id_num + 1
		return True

def get_grabid_total_number():
	global grad_id_list
	return len(grad_id_list)

def get_grabid_from_queue():
	global grab_id_queue
	return grab_id_queue.get()	

def is_queue_empty():
	global grab_id_queue
	return grab_id_queue.empty()	

def can_add_to_queue(grab_id):
	global grad_id_list
	global __MAX_USER_NUMBER__
	if grab_id not in grad_id_list and get_grabid_total_number() <= __MAX_USER_NUMBER__:
		return True
	else:
		return False

def reset_queue_head(grab_id):
	global grab_id_num
	global __MAX_USER_NUMBER__
	global grad_id_list
	global grab_id_queue	
	grab_id_num = 0
	grad_id_list = []
	grab_id_queue = Queue(__MAX_USER_NUMBER__)
	add_grabid_to_queue(grab_id)
	return 











