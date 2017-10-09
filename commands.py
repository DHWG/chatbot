from enum import Enum
from collections import namedtuple
import json

CommandSpec = namedtuple('CommandSpec', ['id', 'short', 'description', 'usage', 'listed'])

class CommandType(Enum):
    HELP = CommandSpec('help/summary',
                       'help',
                       'Describes all available commands.',
                       '$cmd',
                       True)
    SHOPPING_LIST_ADD = CommandSpec('shopping_list/add',
                                    'add',
                                    'Adds something to the shopping list.',
                                    '$cmd item1, ...',
                                    True)
    SHOPPING_LIST_REMOVE = CommandSpec('shopping_list/remove',
                                       'rem',
                                       'Removes something from the shopping list.',
                                       '$cmd item1, ...',
                                       True)
    SHOPPING_LIST_SHOW = CommandSpec('shopping_list/show',
                                     'list',
                                     'Displays the shopping list.',
                                     '$cmd',
                                     True)
    SHOPPING_LIST_DONE = CommandSpec('shopping_list/done',
                                     'done',
                                     'Displays the shopping list with inline keyboard to remove items.',
                                     '$cmd',
                                     True)
    MIRRORCHAT_PRIVACY_ON = CommandSpec('mirror_chat/privacy_on',
                                        'hashmimode',
                                        'Replaces chat messages on mirror with random ones.',
                                        '$cmd',
                                        True)
    MIRRORCHAT_PRIVACY_OFF = CommandSpec('mirror_chat/privacy_off',
                                         'normalmode',
                                         'Turns off privacy mode.',
                                         '$cmd',
                                         True)
    CURSE_ADD = CommandSpec('curses/add',
                            'curseadd',
                            'Adds a curse to the curse list.',
                            '$cmd ZEFIX!',
                            True)
    CURSE_REMOVE = CommandSpec('curses/remove',
                               'curseremove',
                               'Removes a curse from the curse list.',
                               '$cmd ZEFIX!',
                               True)
    CURSE_DO = CommandSpec('curses/do',
                           'curse',
                           'Removes a curse from the curse list.',
                           '$cmd',
                           True)

    def create(self, *arguments):
        return Command(self, arguments)

    @classmethod
    def for_short_name(cls, short_name):
        if short_name in cls._short_name_index:
            return cls._short_name_index[short_name]
        else:
            return None

CommandType._id_index = {e.value.id:e for e in CommandType}
CommandType._short_name_index = {e.value.short:e for e in CommandType}

class Command:

    def __init__(self, type: CommandType, arguments):
        self.type = type
        self.arguments = arguments

    @property
    def id(self):
        return self.type.value.id

    @property
    def json(self):
        return json.dumps(dict(id=self.id, arguments=self.arguments))

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        cmd_type: CommandType = CommandType._id_index[obj['id']]
        return cmd_type.create(*obj['arguments'])

    def __str__(self):
        return f'[Command: {self.id} {self.arguments}]'