import time
import logging
import telepot
import telepot.helper
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
import config
from commands import CommandType, Command
from modules import ShoppingListModule

shopping_list = ShoppingListModule()

handlers = {
    CommandType.SHOPPING_LIST_ADD: shopping_list.add,
    CommandType.SHOPPING_LIST_REMOVE: shopping_list.remove,
    CommandType.SHOPPING_LIST_SHOW: shopping_list.list,
    CommandType.SHOPPING_LIST_DONE: shopping_list.done_selector,
}

class DHBot(telepot.helper.ChatHandler):

    def __init__(self, *args, **kwargs):
        super(DHBot, self).__init__(*args, **kwargs)
        self._log = logging.getLogger(DHBot.__name__)

    def _resolve_command(self, msg_txt):
        if not msg_txt.startswith('/'):
            return None

        parts = msg_txt.split(' ', 1)
        short_name = parts[0][1:] # throw away leading /
        arguments = parts[1] if len(parts) == 2 else ''
        arguments = [argument.strip() for argument in arguments.split(',')]

        command_type = CommandType.for_short_name(short_name)
        if command_type:
            return command_type.create(*arguments)
        else:
            self._log.warning('Got unknown command "%s".', short_name)
            return None

    def _dispatch_command(self, command):
        if not command.type in handlers:
            self._log.warning('Got command "%s" without registered handler.', command.id)
        self._log.debug('Executing command %s.', command)
        handlers.get(command.type)(self, command.id, *command.arguments)

    def on_chat_message(self, message):
        content_type, chat_type, chat_id = telepot.glance(message)
        if content_type == 'text':
            command = self._resolve_command(message['text'])
            if command:
                self._dispatch_command(command)

    def on_callback_query(self, message):
        query_id, from_id, query_data = telepot.glance(message, flavor='callback_query')

        command = Command.from_json(query_data)
        if command:
            self._dispatch_command(command)

    def send_inline_command_selector(self, message, options):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=command.json)] for (label, command) in options
        ])
        self.sender.sendMessage(message, reply_markup=keyboard)


bot = telepot.DelegatorBot(config.telegram_token, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(), create_open, DHBot, timeout=60),
])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    MessageLoop(bot).run_as_thread()
    logging.getLogger(__name__).info('Listening...')

    while 1:
        time.sleep(10)