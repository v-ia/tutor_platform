from customconfigparser import CustomConfigParser
from pathlib import Path
from database import Database
from controller import Controller
from aiohttp import web
import logging


if __name__ == '__main__':
    app = web.Application()
    app['config'] = CustomConfigParser()
    app['config'].read(Path.cwd().parent / 'config.ini')  # path_to_config_file / config_name
    app['database'] = Database(config=app['config'])
    app['controller'] = Controller()
    app.add_routes([web.post(f'/', app['controller'].handle_update)])
    web.run_app(app)
