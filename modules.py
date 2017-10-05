import logging
from commands import CommandType, Command

class HelpModule:
    '''Provides a summary of all available commands.'''

    def __init__(self):
        self._log = logging.getLogger(HelpModule.__name__)

    def command_summary(self, bot, cmd, *args):
        help = ''
        for command_type in CommandType:
            spec = command_type.value
            if not spec.listed:
                continue
            usage = spec.usage.replace('$cmd', '/' + spec.short)
            description = f'{usage}: {spec.description}\n'
            help += description
        bot.sender.sendMessage(help)

class ShoppingListModule:
    '''Simple shopping list.'''

    def __init__(self):
        self._list = []
        self._log = logging.getLogger(ShoppingListModule.__name__)

    def add(self, bot, cmd, *items):
        self._log.debug('Adding: %s', items)
        # TODO connect to Redis
        self._list.extend(items)

    def remove(self, bot, cmd, *items):
        # TODO connect to Redis
        self._log.debug('Removing: %s', items)
        for item in items:
            # TODO connect to Redis
            self._list.remove(item)
        bot.sender.sendMessage('Thanks for buying ' + ' and '.join(items))

    def list(self, bot, cmd, *items):
        # TODO connect to Redis
        msg = 'In shopping list: ' + ', '.join(self._list)
        bot.sender.sendMessage(msg)

    def done_selector(self, bot, cmd, *items):
        # TODO connect to Redis
        options = [(item, CommandType.SHOPPING_LIST_REMOVE.create(item)) for item in self._list]
        bot.send_inline_command_selector('What did you buy?', options)

class ChatToMirrorModule:
    '''Forwards messages from Telegram to the MagicMirror via Redis.'''

    # TODO all Hashmi-mode handling

    def __init__(self):
        self._log = logging.getLogger(ChatToMirrorModule.__name__)
        self._privacy_mode = False

    def _to_redis(self, initials, text):
        self._log.debug('To Redis: %s : %s', initials, text)

    def _sender_initials(self, message):
        first = message['from'].get('first_name', ' ')
        last = message['from'].get('last_name', ' ')
        return first[0] + last[0]

    def on_message(self, bot, content_type, message):
        if not self._privacy_mode:
            text = message['text'] if content_type == 'text' else f'[Sent a {content_type}.]'
            self._to_redis(self._sender_initials(message), text)

    def privacy_mode_on(self, *args):
        self._log.info('Privacy mode on.')
        self._privacy_mode = True

    def privacy_mode_off(self, *args):
        self._log.info('Privacy mode off.')
        self._privacy_mode = False