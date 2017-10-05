# DHWG Telegram Chatbot

## Requirements

* Python 3.6

## Setup

Copy `config.dist.py` to `config.py`and enter all necessary configuration parameters.

Then execute with:
    
    python3.6 main.py

## Adding new commands

1. Add a new `CommandSpec` to `CommandType` in `commands.py`.
2. Create a class with appropriate logic, e.g. in `modules.py`.
3. In `main.py` at the top, create an instance of this class and register handlers for the new commands using `command_handlers`.