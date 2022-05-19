from pathlib import Path
import logging
import configparser
import asyncio
import aiohttp
import asyncpg
from aiohttp import web

CONFIG_PATH = Path.cwd().parent
CONFIG_NAME = 'config.ini'
SUPPORTED_UPDATE_TYPES = ('message', 'callback_query')


class Database:
    def __init__(self, config: object):
        self.__connection = None
        self.__auth_data = {'host': config.get('Database', 'host'),
                            'port': config.get('Database', 'port'),
                            'user': config.get('Database', 'user'),
                            'password': config.get('Database', 'password'),
                            'database': config.get('Database', 'database')
                            }

    @property
    async def auth_data(self) -> dict:
        if None in self.__auth_data:
            raise KeyError('Some values for database connection are empty. Problem with config file')
        else:
            return self.__auth_data

    @property
    async def connection(self) -> object:
        return self.__connection

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
    def __init__(self, config: object, database: Database):
        self.__bot_token = config.get('Telegram', 'bot_token')
        self.__server_url = config.get('Telegram', 'server_url')
        self.__database = database

    @property
    async def bot_token(self) -> str:
        if self.__bot_token is None:
            raise KeyError('Bot_token is empty. Problem with config file')
        else:
            return self.__bot_token

    @property
    async def server_url(self) -> str:
        if self.__server_url is None:
            raise KeyError('Server_url is empty. Problem with config file')
        else:
            return self.__server_url

    @staticmethod
    async def parser(json_update: dict) -> dict:
        data = {'update_id': json_update['update_id'],
                'user_id': json_update[list(json_update)[1]]['from']['id'],
                'command': json_update[list(json_update)[1]][list(json_update[list(json_update)[1]])[4]]
                }
        return data

    async def request_handler(self, request):
        json_update = await request.json()
        update_type = list(json_update)[1]
        if update_type in SUPPORTED_UPDATE_TYPES:
            data = await self.parser(json_update)
            return web.json_response(data)

        # async with aiohttp.ClientSession() as session:
        #     async with session.get(f'{await self.server_url}bot{await self.bot_token}/getUpdates') as request:
        #         json_answer = await request.json()
        #         print(json_answer)
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

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH / CONFIG_NAME)

    postgres_db = Database(config)

    bot = Bot(config, postgres_db)

    app = web.Application()
    app.add_routes([web.post(f'/', bot.request_handler)])
    web.run_app(app)
