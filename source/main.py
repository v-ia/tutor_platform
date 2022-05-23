import json
from pathlib import Path
import logging
import configparser
import asyncio
import aiohttp
import asyncpg
from aiohttp import web
import ast
import re


def empty_values_check(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if not result:
            raise KeyError('Problem when reading config file. Some values are empty')
        else:
            return result
    return wrapper


class CustomConfigParser(configparser.ConfigParser):
    @empty_values_check
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class Database:
    def __init__(self, config: configparser.ConfigParser):
        self.__connection = None
        self.__auth_data = {'host': config.get('Database', 'host'),
                            'port': config.get('Database', 'port'),
                            'user': config.get('Database', 'user'),
                            'password': config.get('Database', 'password'),
                            'database': config.get('Database', 'database')
                            }

    @property
    async def auth_data(self) -> dict:
        return self.__auth_data

    @property
    async def connection(self) -> object:
        if self.connection is not None:
            return self.__connection
        else:
            raise ConnectionError('Connection to database is not established')

    @connection.setter
    async def connection(self, new_connection: object):
        if self.connection is None:
            self.__connection = new_connection

    async def connect(self):
        try:
            self.connection = await asyncpg.connect(host=await self.auth_data['host'],
                                                    port=await self.auth_data['port'],
                                                    user=await self.auth_data['user'],
                                                    password=await self.auth_data['password'],
                                                    database=await self.auth_data['database']
                                                    )
        except ConnectionError:
            print('Can\'t connect to database')
        finally:
            await self.disconnect()

    async def disconnect(self):
        self.connection.close()


class Bot:
    def __init__(self, config: configparser.ConfigParser, database: Database):
        self.__bot_token = config.get('Bot', 'bot_token')
        self.__server_url = config.get('Bot', 'server_url')
        self.__supported_commands = ast.literal_eval(config.get('Bot', 'supported_commands'))
        self.database = database

    @property
    async def supported_commands(self) -> str:
        return self.__supported_commands

    @property
    async def bot_token(self) -> str:
        return self.__bot_token

    @property
    async def server_url(self) -> str:
        return self.__server_url


class Controller:
    def __init__(self, config: configparser.ConfigParser):
        self.database = Database(config)
        self.bot = Bot(config, self.database)

    @staticmethod
    async def parser(json_update: dict) -> dict:
        update_type = list(json_update)[1]  # message or callback_query
        message_type = list(json_update[update_type])[4]  # photo, document, text, data and so on
        data = {'update_id': json_update['update_id'],
                'user_id': json_update[update_type]['from']['id']}
        if update_type == 'callback_query':
            data['type'] = 'command'
            data['value'] = json_update['callback_query']['data']
        elif update_type == 'message':
            if message_type == 'text':
                text = json_update['message']['text']
                command = re.findall('/[a-z]+', text)
                if len(command) == 0:
                    data['type'] = 'text'
                    data['value'] = text
                else:
                    data['type'] = 'command'
                    data['value'] = command[0]
            elif message_type == 'document':
                data['type'] = 'document'
                data['value'] = json_update['message']['document']['file_id']
            elif message_type == 'audio':
                data['type'] = 'audio'
                data['value'] = json_update['message']['audio']['file_id']
            elif message_type == 'photo':
                data['type'] = 'photo'
                data['value'] = json_update['message']['photo'][-1]['file_id']
            if 'caption' in json_update['message'].keys():
                data['caption'] = json_update['message']['caption']
        return data

    async def request_handler(self, request):
        json_update = await request.json()
        data = await self.parser(json_update)
        return web.json_response()  # 200 (OK) response

# async def main():
#     config = configparser.ConfigParser()
#     config.read(CONFIG_PATH / CONFIG_NAME)
#
#     postgres_db = Database(config)
#
#     bot = Bot(config, postgres_db)
#     async with aiohttp.ClientSession() as session:
#         async with session.get(f'{await bot.server_url}bot{await bot.bot_token}/getUpdates') as request:
#             json_answer = await request.json()
#             print(json_answer)
        #         sender, text = await self.parser(await request.json())
        #         answer = {
        #             'chat_id': sender,
        #             'text': 'Выберите пункт меню',
        #             'reply_markup': {
        #                 'keyboard': [[{'text': 'First button'}], [{'text': 'Second button'}], [{'text': 'Third button'}]]
        #             }
        #         }
        #         answer2 = {
        #             'chat_id' : sender,
        #             'text' : 'Выберите пункт меню',
        #             'reply_markup' : {
        #                 'remove_keyboard': True
        #             }
        #         }
        #         answer3 = {
        #             'chat_id' : sender,
        #             'text' : 'Выберите пункт меню',
        #             'reply_markup' : {
        #                 'inline_keyboard' : [[{'text': 'First button', 'callback_data': 1}],
        #                                      [{'text': 'Second button', 'callback_data': 2}],
        #                                      [{'text': 'Third button', 'callback_data': 3}]]
        #             }
        #         }
                # async with session.post(
                #         f'{await self.server_url}bot{await self.bot_token}/sendMessage', json=answer3) as request:
                #     json_answer = await request.json()
                #     print(json_answer)


if __name__ == '__main__':
    config = CustomConfigParser()
    config.read(Path.cwd().parent / 'config.ini')   # path_to_config_file / config_name

    controller = Controller(config)

    app = web.Application()
    app.add_routes([web.post(f'/', controller.request_handler)])
    web.run_app(app)

# if __name__ == '__main__':
#     asyncio.run(main())