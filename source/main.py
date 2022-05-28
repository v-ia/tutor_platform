from pathlib import Path
import logging
import configparser
import asyncio
import aiohttp
import asyncpg
from aiohttp import web
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

    async def create_pool(self):
        try:
            self.pool = await asyncpg.create_pool(host=self.auth_data['host'],
                                                  port=self.auth_data['port'],
                                                  user=self.auth_data['user'],
                                                  password=self.auth_data['password'],
                                                  database=self.auth_data['database']
                                                  )
        except ConnectionError:
            print('Can\'t create connection\'s pool for database')

    async def get(self, sql: str, *args):
        await self.create_pool()
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.fetchrow(sql, *args)
                return result

    async def post(self, sql: list, values: list):
        await self.create_pool()
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                for num, sql in enumerate(sql):
                    await connection.execute(sql, *values[num])


class Model:
    def __init__(self, database: Database):
        self.database = database

    # check: does user exist in database?
    async def user_check(self, data: dict):
        if await self.database.get('SELECT COUNT(*) FROM users WHERE chat_id = $1;', data['chat_id']) == 0:
            return False
        else:
            return dict(await self.database.get('SELECT phone, name, surname, role, current_client FROM users '
                                           'WHERE chat_id = $1;', data['chat_id']))

    async def start_registration(self, data: dict):
        user_info = await self.user_check(data)
        if not user_info:
            await self.database.post(['INSERT INTO users (id, current_command) VALUES ($1, $2);'],
                                     [[data['chat_id'], data['value']]])
        else:
            await self.database.post(['UPDATE users SET current_command = $1 WHERE chat_id = $2;'],
                                     [[data['value'], data['chat_id']]])
        return user_info


class ViewBot:
    def __init__(self, config: configparser.ConfigParser):
        self.__bot_token = config.get('Bot', 'bot_token')
        self.__server_url = config.get('Bot', 'server_url')
        self.__request_attempts = config.get('Bot', 'request_attempts')
        self.menu_parent = [[{'text': 'Редактировать мой профиль',
                                'callback_data': '/alter_user_data'}],
                            [{'text': 'График занятий (отменить/перенести/назначить)',
                                'callback_data': '/alter_user_data'}],
                            [{'text': 'Что было задано ребенку?',
                                'callback_data': '/alter_user_data'}],
                            [{'text': 'Отправил ли ребенок домашнее задание?',
                                'callback_data': '/alter_user_data'}],
                            [{'text': 'Отчеты, все ли занятия оплачены',
                                'callback_data': '/alter_user_data'}],
                            ]
        self.menu_student = [[{'text': 'Редактировать мой профиль', 'callback_data': '/alter_user_data'}],
                             [{'text': 'Узнать, что было задано', 'callback_data': '/alter_user_data'},
                              {'text': 'Отправить домашнее задание', 'callback_data': '/alter_user_data'}],
                             [{'text': 'Отменить занятие', 'callback_data': '/alter_user_data'},
                              {'text': 'Перенести занятие', 'callback_data': '/alter_user_data'}]
                            ]
        self.menu_tutor = [[{'text' : 'Редактировать мой профиль', 'callback_data' : '/alter_user_data'}],
                             [{'text' : 'Узнать, что было задано', 'callback_data' : '/alter_user_data'},
                              {'text' : 'Отправить домашнее задание', 'callback_data' : '/alter_user_data'}],
                             [{'text' : 'Отменить занятие', 'callback_data' : '/alter_user_data'},
                              {'text' : 'Перенести занятие', 'callback_data' : '/alter_user_data'}]
                             ]

    @property
    def bot_token(self) -> str:
        return self.__bot_token

    @property
    def server_url(self) -> str:
        return self.__server_url

    @property
    def request_attempts(self) -> int:
        return int(self.__request_attempts)

    async def _send_method(self, data_type: str, method: str, data: dict):
        data_to_send = {'chat_id': data['chat_id'],
                        data_type: data['value']
                        }
        if 'caption' in data.keys():
            data_to_send['caption'] = data['caption']
        if data.get('reply_markup'):
            data_to_send['reply_markup'] = data['reply_markup']
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.request_attempts):
                await asyncio.sleep(1 * attempt)
                async with session.post(f'{self.server_url}bot{self.bot_token}/{method}',
                                        json=data_to_send
                                        ) as request:
                    json_answer = await request.json()
                    if request.status == 200:
                        return json_answer['ok']

    async def send_menu(self, data: dict, menu: list):
        data['value'] = 'Выберите, что необходимо сделать:'
        data['reply_markup'] = {'inline_keyboard': menu}
        await self._send_method('text', 'sendMessage', data)

    async def start(self, data: dict):
        data['value'] = 'Добро пожаловать! :) С моей помощью Вы всегда будете в курсе Вашего расписания, домашних ' \
                        'заданий, сможете отменять и назначать занятия и многое другое! Для начала нужно пройти ' \
                        'небольшую регистрацию (требуется лишь 1 раз).'
        data['reply_markup'] = {
                         'inline_keyboard': [[{'text': 'Начать регистрацию', 'callback_data': '/register'}]]}
        await self._send_method('text', 'sendMessage', data)

    async def user_is_already_registered(self, data: dict):
        data['value'] = 'Ранее Вы уже успешно прошли регистрацию в боте.'
        await self._send_method('text', 'sendMessage', data)

    async def alter_user_data(self, data: dict):
        data['value'] = 'Если хотите изменить введенные при регистрации данные, то выберите, что именно:'
        data['reply_markup'] = {
            'inline_keyboard':  [[{'text': 'Номер телефона', 'callback_data': '/alter_number'},
                                {'text': 'Тип (родитель/ученик)', 'callback_data': '/alter_role'}],
                                [{'text': 'Имя', 'callback_data': '/alter_name'},
                                {'text': 'Фамилия', 'callback_data': '/alter_surname'}]]}
        await self._send_method('text', 'sendMessage', data)


class Controller:
    def __init__(self, config: configparser.ConfigParser):
        self.database = Database(config)
        self.model = Model(self.database)
        self.view = ViewBot(config)
        self.commands_handlers = {'/start': self.view.start,
                                  '/register': self.register,
                                  '/register_scratch': self,
                                  '/alter_user_data': self.view.alter_user_data,
                                  '/navigation': self.navigation
                                  }

    async def _parser_of_update(self, json_update: dict) -> dict:
        update_type = list(json_update)[1]  # message or callback_query
        message_type = list(json_update[update_type])[4]  # photo, document, text, data and so on
        data = {'update_id': json_update['update_id'],
                'chat_id': json_update[update_type]['from']['id'],
                'is_bot': json_update[update_type]['from']['is_bot']}
        if update_type == 'callback_query':
            data['type'] = 'command'
            data['value'] = json_update['callback_query']['data']
        elif update_type == 'message':
            if message_type == 'text':
                text = json_update['message']['text']
                command = list(set(re.findall('/[a-z]+', text)) & set(self.commands_handlers.keys()))
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
        data = await self._parser_of_update(json_update)
        if not data['is_bot']:
            if data['type'] == 'command':
                await self.commands_handlers[data['value']](data)
        return web.json_response()  # 200 (OK) response

    async def register(self, data: dict):
        user_info = await self.model.start_registration(data)
        if None not in user_info.values():
            await self.view.user_is_already_registered(data)
            await self.view.alter_user_data(data)

    async def navigation(self, data: dict):
        user_info = await self.model.user_check(data)
        if user_info:
            if user_info['role'] == 'student':
                await self.view.send_menu(data, self.view.menu_student)
            elif user_info['role'] == 'parent':
                await self.view.send_menu(data, self.view.menu_parent)
            elif user_info['role'] == 'tutor':
                await self.view.send_menu(data, self.view.menu_tutor)
            else:
                await self.register(data)
        else:
            await self.view.start(data)
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
