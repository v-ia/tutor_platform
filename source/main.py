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
    app['config'].read(Path.cwd().parent / 'config.ini')  # path_to_config_file / config_name
    app['database'] = Database(config=app['config'])
    app['background_tasks'] = set()
    app['controller'] = Controller()
    app['controller'].handler_factories = {'/start': handlers.StartFactory,
                                           '/help': handlers.HelpFactory,
                                           '/register': 0,
                                           '/send_homework': 0,
                                           '/schedule': 0,
                                           '/homework': 0,
                                           '/payments': 0,
                                           '/cancel_lesson': 0,
                                           '/reschedule_lesson': 0,
                                           '/appoint_lesson': 0,
                                           '/alter_profile': 0,
                                           '/checked_homework': 0,
                                           '/lesson_as_paid': 0,
                                           '/confirm_user': 0
                                           }
    app.add_routes([web.post(f'/', app['controller'].save_update)])
    web.run_app(app)
