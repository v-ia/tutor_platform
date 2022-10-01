from customconfigparser import CustomConfigParser
from pathlib import Path
from database import Database
from controller import Controller
from aiohttp import web
import logging
from data import *
import handlers

if __name__ == '__main__':
    app = web.Application()
    app['config'] = CustomConfigParser()
    app['config'].read(Path.cwd() / 'config.ini')  # path_to_config_file / config_name
    app['database'] = Database(config=app['config'])
    app['background_tasks'] = set()
    app['controller'] = Controller()
    app['controller'].handler_factories = {'/start': handlers.StartFactory,
                                           '/help': handlers.HelpFactory,
                                           '/register': handlers.RegisterFactory,
                                           }
    app.add_routes([web.post(f'/', app['controller'].save_update)])
    app.add_routes([web.get(f'/', app['controller'].say_hello)])
    web.run_app(app)
