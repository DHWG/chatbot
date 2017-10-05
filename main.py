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
from modules import HelpModule, ShoppingListModule, ChatToMirrorModule

help_module = HelpModule()
shopping_list = ShoppingListModule()
mirror_chat = ChatToMirrorModule()

# command handlers receive the specific type of commands they are registered for
command_handlers = {
    CommandType.HELP: help_module.command_summary,
    CommandType.SHOPPING_LIST_ADD: shopping_list.add,
    CommandType.SHOPPING_LIST_REMOVE: shopping_list.remove,
    CommandType.SHOPPING_LIST_SHOW: shopping_list.list,
    CommandType.SHOPPING_LIST_DONE: shopping_list.done_selector,
    CommandType.MIRRORCHAT_PRIVACY_ON: mirror_chat.privacy_mode_on,
    CommandType.MIRRORCHAT_PRIVACY_OFF: mirror_chat.privacy_mode_off,
}

# message handlers are passed all messages that are not commands
message_handlers = [
    mirror_chat.on_message
]

class DHBot(telepot.helper.ChatHandler):

    def __init__(self, *args, **kwargs):
        super(DHBot, self).__init__(*args, **kwargs)
        self._log = logging.getLogger(DHBot.__name__)

    def _resolve_command(self, msg_txt):
        '''Tries to resolve a command from message text, returns None if the message is not a command.'''
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
        '''Dispatches a command to the registered handler.'''
        if not command.type in command_handlers:
            self._log.warning('Got command "%s" without registered handler.', command.id)
        self._log.debug('Executing command %s.', command)
        command_handlers.get(command.type)(self, command.id, *command.arguments)

    def on_chat_message(self, message):
        '''Called on regular chat messages.'''
        content_type, chat_type, chat_id = telepot.glance(message)
        if content_type == 'text':
            command = self._resolve_command(message['text'])
            if command:
                self._dispatch_command(command)
                return
        for handler in message_handlers:
            handler(self, content_type, message)

    def on_callback_query(self, message):
        '''Called on callbacks, e.g. from inline keyboards.'''
        query_id, from_id, query_data = telepot.glance(message, flavor='callback_query')

        command = Command.from_json(query_data)
        if command:
            self._dispatch_command(command)

    def send_inline_command_selector(self, message, options):
        '''Sends an inline keyboard where each button represents a command instance.'''
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