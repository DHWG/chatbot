import sys
import thread
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
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
import redis
import json
import re

import lightcontroller

message_with_inline_keyboard = None

hashmimode = False



class ChatBot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(ChatBot, self).__init__(*args, **kwargs)
        self.redis = redis.StrictRedis(host='localhost')
        self.redis_key = 'shopping_list'
        self.secure_random = random.SystemRandom()
        self.l_controller = lightcontroller.lightcontroller()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(msg)
        if msg['chat']['type'] == 'group':
            if msg['chat']['id'] == -160834945:
                self.l_controller.notify()
                if not ChatBot.hashmimode:
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
            subprocess.call('for i in {1 .. 10}; do ./reconnect.sh; sleep 10; done', shell=True)
        elif msg['text'].split()[0] == '/add':
            self._add_shopping(msg)
        elif msg['text'] == '/list':
            self._show_shopping(msg)
        elif msg['text'] == '/done':
            self._done_shopping(msg)
        elif msg['text'].split()[0] == '/curseadd':
            self._curseadd(msg)
        elif msg['text'].split()[0] == '/curseremove':
            self._curseremove(msg)
        elif msg['text'] == '/hashmimode':
            ChatBot.hashmimode = True
            self.l_controller.notify()
            thread.start_new_thread(self._hashmifunc, ())
        elif msg['text'] == '/normalmode':
            ChatBot.hashmimode = False
            msg['text'] = 'normalmode enabled'
            self._message_to_redis(content_type, msg)
            self.sender.sendMessage('normalmode enabled')
        elif msg['text'].split()[0] == '/addhashmi':
            self._addhashmi(msg)
        elif msg['text'] == "/notify":
            self.l_controller.notify()

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        chat_id = msg['message']['chat']['id']
        # without following line encoding problems will stop us from finding non-ascii items
        # TODO extract Redis code in its own class, do this everywhere, sort items
        items = map(lambda x: x.decode('utf8'), self.redis.smembers(self.redis_key))
        if query_data in items:
            buyer = msg['from']['first_name']
            self.redis.srem(self.redis_key, query_data)
            self.sender.sendMessage('Thanks ' + buyer + ', for buying: ' + query_data)
            self.bot.answerCallbackQuery(query_id, text='Thanks')

        else:
            self.bot.answerCallbackQuery(query_id, text=query_data + ', already bought!', show_alert=True)

    def on_close(self, ex):
        # self.sender.sendMessage('on_close called')
        pass

    def on__idle(self, event):
        print('on Idle')

    def _curseadd(self, msg):
        curse = msg['text'].split(' ', 1)[-1]
        print(curse)
        self.redis.rpush("curses", curse)

    def _curseremove(self, msg):
        curse = msg['text'].split(' ', 1)[-1]
        print("Remove curse: " + curse)
        self.redis.lrem("curses", -1, curse)

    def _cursefunc(self):
        curses = self.redis.lrange("curses", 0, -1)
        self.sender.sendMessage(self.secure_random.choice(curses))

    def _add_shopping(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        items = [x.strip() for x in msg['text'][4:].split(',')]
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
            bot.sendMessage(chat_id, "there is nothing in the List that you could have bought!")

    def _build_keyboard(self, items):
        mark_up = []
        for item in items:
            button = InlineKeyboardButton(text=item, callback_data=item)
            new = []
            new.append(button)
            mark_up.append(new)
        return InlineKeyboardMarkup(inline_keyboard=mark_up)

    def _message_to_redis(self, content_type, msg):
        def initials(first, last):
            return first[0] + last[0]

        print msg
        payload = {
            'text': msg['text'] if content_type == 'text' else '[Sent a {}].'.format(content_type),
            'name': initials(msg['from'].get('first_name', ' '), msg['from'].get('last_name', ' '))
        }
        self.redis.publish('chat', json.dumps(payload))

    def _addhashmi(self, msg):
        textarray = msg['text'].split(' ')
        if len(textarray[1]) != 2:
            return
        initials = textarray[1]
        text = ' '.join(textarray[2:])
        payload = (text, initials)
        self.redis.rpush("hashmitext", json.dumps(payload))

    def _hashmifunc(self):
        hashmitext = self.redis.lrange("hashmitext", 0, -1)
        payloadlist = []
        texts = [('I love this WG!', 'TC'), ('No Popcorntime!', 'YS'), ('Thanks for cleaning :)', 'JJ'),
                 ('Our Landlord is the best!!!', 'KL'), ('I cleaned the kitchen that was fun!', 'QN'),
                 ('I go to bed early today', 'AD'), ('Best place to study', 'NB'),
                 ('This Place is better than Paris!!!<3', 'AC'), ('Are u fucking kidding me?!', 'GB')]
        texts.extend([tuple(json.loads(x)) for x in hashmitext])
        for text in texts:
            payload = {}
            payload['text'] = text[0]
            payload['name'] = text[1]
            payloadlist.append(payload)
        sent_messages = 0
        lasttexts = []
        while ChatBot.hashmimode:
            text = ''
            while True:
                if (len(lasttexts) > 9):
                    lasttexts.pop(0)
                text = self.secure_random.choice(payloadlist)
                if (text not in lasttexts):
                    lasttexts.append(text)
                    self.redis.publish('chat', json.dumps(text))
                    break
            sent_messages += 1
            if sent_messages >= 20:
                time.sleep(20)


ChatBot.hashmimode = False
TOKEN = '398531640:AAHx75eeW3GJJBw0NG37xxGUj4nBfWsESPA'

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        # pave_event_space())( per_chat_id(types=['group']), create_open,chatbot , timeout=10),])
        pave_event_space())(per_chat_id(), create_open, ChatBot, timeout=10), ])

MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)

