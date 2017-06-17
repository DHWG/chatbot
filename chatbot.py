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

message_with_inline_keyboard = None

class chatbot(telepot.helper.ChatHandler):
    	def __init__(self, *args, **kwargs):
	       	super(chatbot, self).__init__(*args, **kwargs)
		
		self.curses = ['dummpiss', 'littleFrenchMan', 'Schlitzi','Kartoffel','Immigrand', 'SchwabenSeggel', 'DU HASHMI', 'NOOB', 'Mettigel', 'u just suck' ]
		self.secure_random = random.SystemRandom()	
 		self.db = DBHelper()
		self.db.setup()
	def on_chat_message(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
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
		elif msg['text'].split()[0] == '/done':
			self._done_shopping(msg)	
		
	def on_callback_query(self,msg):
		query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')	
	 	chat_id = msg['message']['chat']['id']	
		items = self.db.get_items(chat_id)		
		if query_data in items:
			self.db.delete_item(query_data,self.chat_id)
			self.sender.sendMessage('Thanks for buying: ' + query_data)
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
			self.db.add_item(item,chat_id)
	
	def _show_shopping(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		items = self.db.get_items(chat_id)
		self.sender.sendMessage('In Shopping List: ' + ', '.join(items))

	def _done_shopping(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)	
		items = self.db.get_items(chat_id)
		keyboard = self._build_keyboard(items)      	
		global message_with_inline_keyboard 
		message_with_inline_keyboard = bot.sendMessage(chat_id, "Select an item to delete", reply_markup=keyboard)

	def _build_keyboard(self,items):
		mark_up=[] 
		for i in range(len(items)):
			button = InlineKeyboardButton(text=items[i], callback_data=items[i])
			new = []
			new.append(button)
			mark_up.append(new)		
		return  InlineKeyboardMarkup(inline_keyboard=mark_up)	

TOKEN = '398531640:AAHx75eeW3GJJBw0NG37xxGUj4nBfWsESPA'

#bot = telepot.DelegatorBot(TOKEN, [
 #   include_callback_query_chat_id(pave_event_space())(per_chat_id(types=['group']), create_open, chatbot,timeout = 10),
#])

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(types=['group']), create_open,chatbot , timeout=10),
])

MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
