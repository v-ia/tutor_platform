from customconfigparser import CustomConfigParser
from pathlib import Path
from database import Database
from controller import Controller
from aiohttp import web
import logging
from response import *

if __name__ == '__main__':
    app = web.Application()
    app['config'] = CustomConfigParser()
    app['config'].read(Path.cwd().parent / 'config.ini')  # path_to_config_file / config_name
    app['database'] = Database(config=app['config'])
    app['controller'] = Controller()
    app['background_tasks'] = set()
    app.add_routes([web.post(f'/', app['controller'].handle_update)])
    web.run_app(app)
    # keyboard = InlineKeyboardMarkup()
    # keyboard.add_button(InlineKeyboardButton(1, 2))
    # keyboard.add_button(InlineKeyboardButton(3, 4))
    # keyboard.new_line_of_buttons()
    # keyboard.add_button(InlineKeyboardButton(5, 6))
    # keyboard.add_button(InlineKeyboardButton(7, 8))
    # message = SendMessage(1, '123', keyboard)
    # print(message.dict())
