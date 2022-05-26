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
        self.__auth_data = {'host': config.get('Database', 'host'),
                            'port': config.get('Database', 'port'),
                            'user': config.get('Database', 'user'),
                            'password': config.get('Database', 'password'),
                            'database': config.get('Database', 'database')
                            }
        self.__pool = None

    @property
    def auth_data(self) -> dict:
        return self.__auth_data

    @property
    def pool(self) -> object:
        return self.__pool

    @pool.setter
    def pool(self, pool: object):
        if not self.__pool:
            self.__pool = pool
        else:
            raise ValueError('Pool is already set')

    async def execute_query(self):
        try:
            self.pool = await asyncpg.create_pool(host=self.auth_data['host'],
                                                  port=self.auth_data['port'],
                                                  user=self.auth_data['user'],
                                                  password=self.auth_data['password'],
                                                  database=self.auth_data['database']
                                                  )
        except ConnectionError:
            print('Can\'t create connection\'s pool for database')

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.fetchval('select 2 * 5')
                print(result)


class Bot:
    def __init__(self, database: Database):
        self.database = database


class ViewBot:
    def __init__(self, config: configparser.ConfigParser):
        self.__bot_token = config.get('Bot', 'bot_token')
        self.__server_url = config.get('Bot', 'server_url')
        self.__request_attempts = config.get('Bot', 'request_attempts')

    @property
    def bot_token(self) -> str:
        return self.__bot_token

    @property
    def server_url(self) -> str:
        return self.__server_url

    @property
    def request_attempts(self) -> str:
        return self.__request_attempts

    async def send_method(self, data_type: str, method: str, data: dict, reply_markup: dict = None):
        data_to_send = {'chat_id': data['user_id'],
                        data_type: data['value']
                        }
        if 'caption' in data.keys():
            data_to_send['caption'] = data['caption']
        if reply_markup:
            data_to_send['reply_markup'] = reply_markup
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.request_attempts):
                await asyncio.sleep(1 * attempt)
                async with session.post(f'{self.server_url}bot{self.bot_token}/{method}',
                                        json=data_to_send
                                        ) as request:
                    json_answer = await request.json()
                    if request.status == 200:
                        return json_answer['ok']


class Controller:
    def __init__(self, config: configparser.ConfigParser):
        self.database = Database(config)
        self.bot = Bot(self.database)
        self.view = ViewBot(config)
        self.__supported_commands = ast.literal_eval(config.get('Bot', 'supported_commands'))

    @property
    def supported_commands(self) -> str:
        return self.__supported_commands

    async def parser_of_update(self, json_update: dict) -> dict:
        update_type = list(json_update)[1]  # message or callback_query
        message_type = list(json_update[update_type])[4]  # photo, document, text, data and so on
        data = {'update_id': json_update['update_id'],
                'user_id': json_update[update_type]['from']['id'],
                'is_bot': json_update[update_type]['from']['is_bot']}
        if update_type == 'callback_query':
            data['type'] = 'command'
            data['value'] = json_update['callback_query']['data']
        elif update_type == 'message':
            if message_type == 'text':
                text = json_update['message']['text']
                command = list(set(re.findall('/[a-z]+', text)) & set(self.supported_commands))
                if len(command) == 0:
                    data['type'] = 'text'
                    data['value'] = text
                else:
                    data['type'] = 'command'
                    data['value'] = command[0]
            elif message_type == 'document' or message_type == 'audio' or message_type == 'video':
                data['type'] = message_type
                data['value'] = json_update['message'][message_type]['file_id']
            elif message_type == 'photo':
                data['type'] = 'photo'
                data['value'] = json_update['message']['photo'][-1]['file_id']
            if 'caption' in json_update['message'].keys():
                data['caption'] = json_update['message']['caption']
        return data

    async def update_handler(self, request):
        json_update = await request.json()
        data = await self.parser_of_update(json_update)
        if not data['is_bot']:
            await self.database.execute_query()
        return web.json_response()  # 200 (OK) response


# async def main():
#     config = CustomConfigParser()
#     config.read(Path.cwd().parent / 'config.ini')   # path_to_config_file / config_name
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
    app.add_routes([web.post(f'/', controller.update_handler)])
    web.run_app(app)

# if __name__ == '__main__':
#     asyncio.run(main())
