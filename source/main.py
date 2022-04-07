from pathlib import Path
import logging
import configparser
import asyncio
import aiohttp


class Bot:
    def __init__(self, config_filename: str = 'config.ini'):
        config = configparser.ConfigParser()
        config.read(Path.cwd().parent / config_filename)
        self.__bot_token = config.get('DEFAULT', 'bot_token')
        self.__server_url = config.get('DEFAULT', 'server_url')

    @property
    async def bot_token(self) -> str:
        return self.__bot_token

    @property
    async def server_url(self) -> str:
        return self.__server_url


async def main():
    bot = Bot()
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{await bot.server_url}bot{await bot.bot_token}/getUpdates') as request:
            json_answer = await request.json()
            print(json_answer)

if __name__ == '__main__':
    asyncio.run(main())