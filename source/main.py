from pathlib import Path
import logging
import configparser
import asyncio
import aiohttp
import asyncpg
from aiohttp import web


class Database(object):
    def __init__(self, config: object):
        self.__connection = None
        self.__auth_data = {'host': config.get('Database', 'host'),
                            'port': config.get('Database', 'port'),
                            'user': config.get('Database', 'user'),
                            'password': config.get('Database', 'password'),
                            'database': config.get('Database', 'database')
                            }
        if None in self.auth_data.values():
            raise KeyError('Some values for database connection are empty. Problem with reading config file')

    @property
    async def auth_data(self) -> dict:
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
    def __init__(self, config: object):
        self.__bot_token = config.get('Telegram', 'bot_token')
        self.__server_url = config.get('Telegram', 'server_url')

    @property
    async def bot_token(self) -> str:
        return self.__bot_token

    @property
    async def server_url(self) -> str:
        return self.__server_url


async def main():
    config = configparser.ConfigParser()
    config.read(Path.cwd().parent / 'config.ini')

    bot = Bot(config)
    print(config.read('Telegram', 'bot_token1'))
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{await bot.server_url}bot{await bot.bot_token}/getUpdates') as request:
            json_answer = await request.json()
            print(json_answer)
            answer = {'chat_id': json_answer['result'][0]['message']['chat']['id'], 'text': 'Hooray!'}
            print(answer)
        # async with session.post(
        #         f'{await bot.server_url}bot{await bot.bot_token}/sendMessage', json=answer) as request:
        #     json_answer = await request.json()
        #     print(json_answer)

    # row = await conn.fetchrow('SELECT 5*5;')
    # print(row)

if __name__ == '__main__':
    asyncio.run(main())


# async def hello(request):
#     return web.Response(text="Hello, world")
# app = web.Application()
# app.add_routes([web.get('/', hello)])
# web.run_app(app)