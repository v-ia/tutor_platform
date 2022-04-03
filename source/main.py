from pathlib import Path
import logging
import configparser
from aiogram import Bot, Dispatcher, executor, types

config = configparser.ConfigParser()
config.read(Path.cwd().parent / 'config.ini')
print(config.get('DEFAULT', 'api_token'))
