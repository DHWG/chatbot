import logging
from commands import CommandType, Command

class ShoppingListModule():

    def __init__(self):
        self._list = []
        self._log = logging.getLogger(ShoppingListModule.__name__)

    def add(self, bot, cmd, *items):
        self._log.debug('Adding: %s', items)
        self._list.extend(items)

    def remove(self, bot, cmd, *items):
        self._log.debug('Removing: %s', items)
        for item in items:
            self._list.remove(item)
        bot.sender.sendMessage('Thanks for buying ' + ' and '.join(items))

    def list(self, bot, cmd, *items):
        msg = 'In shopping list: ' + ', '.join(self._list)
        bot.sender.sendMessage(msg)

    def done_selector(self, bot, cmd, *items):
        options = [(item, CommandType.SHOPPING_LIST_REMOVE.create(item)) for item in self._list]
        bot.send_inline_command_selector('What did you buy?', options)