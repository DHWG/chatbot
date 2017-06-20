import sys
import time
import random
import subprocess
import shlex
from functools import reduce
import telepot
import telepot.helper
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
from dbhelper import DBHelper
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
import redis
import json
import re

message_with_inline_keyboard = None

class chatbot(telepot.helper.ChatHandler):
    	def __init__(self, *args, **kwargs):
	       	super(chatbot, self).__init__(*args, **kwargs)
		self.redis = redis.StrictRedis(host='localhost')
		self.redis_key = 'shopping_list'
		
		self.curses = ['dummpiss', 'littleFrenchMan', 'Schlitzi','Kartoffel','Immigrand', 'SchwabenSeggel', 'DU HASHMI', 'NOOB', 'Mettigel', 'u just suck' ]
		self.secure_random = random.SystemRandom()	
	def on_chat_message(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		if msg['chat']['title'] == 'ZIPUP WG':
			self._message_to_redis(content_type, msg)
		if content_type == 'sticker':
			fileid = msg['sticker']['file_id']
		if msg['text'] == '/test':
			 self.sender.sendMessage('works')
		elif msg['text'] == '/curse':
			self._cursefunc()
		elif msg['text'] == '/on':
			subprocess.call(shlex.split('./monitor_controler.sh on'))
		elif msg['text'] == '/off':
			subprocess.call(shlex.split('./monitor_controler.sh off'))
		elif msg['text'] == '/ahnquiet':
			subprocess.call('for i in {1 .. 10}; do ./reconnect.sh; sleep 10; done', shell = True)
		elif msg['text'].split()[0] == '/add':
			self._add_shopping(msg)
		elif msg['text']=='/list':
			self._show_shopping(msg)
		elif msg['text'] == '/done':
			self._done_shopping(msg)	
		
	def on_callback_query(self,msg):
		query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')	
	 	chat_id = msg['message']['chat']['id']			
		# without following line encoding problems will stop us from finding non-ascii items
		# TODO extract Redis code in its own class, do this everywhere, sort items
		items = map(lambda x: x.decode('utf8'), self.redis.smembers(self.redis_key))
		if query_data in items:
			buyer = msg['from']['first_name']
			self.redis.srem(self.redis_key, query_data)
			self.sender.sendMessage('Thanks '+ buyer +', for buying: ' + query_data)
			self.bot.answerCallbackQuery(query_id,text='Thanks')

		else:
			self.bot.answerCallbackQuery(query_id, text=query_data + ', already bought!', show_alert=True)

		
	def on_close(self, ex):
		#self.sender.sendMessage('on_close called')	
		pass		
	def on__idle(self, event):	
		print('on Idle')

	def _cursefunc(self):
		 self.sender.sendMessage(self.secure_random.choice(self.curses))
	def _add_shopping(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		items = [x.strip() for x in  msg['text'][4:].split(',')]
		self.sender.sendMessage('add to Shopping List: ' + ', '.join(items))			
		for item in items:	
			if len(item) > 0:
				self.redis.sadd(self.redis_key, item)
	
	def _show_shopping(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		items = self.redis.smembers(self.redis_key)
		self.sender.sendMessage('In Shopping List: ' + ', '.join(items))

	def _done_shopping(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)	
		items = self.redis.smembers(self.redis_key)
		
		if len(items) > 0:
			keyboard = self._build_keyboard(items)      	
			global message_with_inline_keyboard 
			message_with_inline_keyboard = bot.sendMessage(chat_id, "Select an item to delete", reply_markup=keyboard)
		else:
			bot.sendMessage(chat_id,"there is nothing in the List that you could have bought!")

	def _build_keyboard(self,items):
		mark_up=[] 
		for item in items:
			button = InlineKeyboardButton(text=item, callback_data=item)
			new = []
			new.append(button)
			mark_up.append(new)		
		return  InlineKeyboardMarkup(inline_keyboard=mark_up)	

	def _message_to_redis(self, content_type, msg):
		def initials(first, last):
			return first[0] + last[0]
		print msg
		payload = {
			'text': msg['text'] if content_type == 'text' else '[Sent a {}].'.format(content_type),
			'name': initials(msg['from'].get('first_name', ' '), msg['from'].get('last_name', ' '))
		}
		self.redis.publish('chat', json.dumps(payload))

TOKEN = '398531640:AAHx75eeW3GJJBw0NG37xxGUj4nBfWsESPA'

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(types=['group']), create_open,chatbot , timeout=10),
])

MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
