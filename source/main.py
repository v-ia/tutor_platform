from pathlib import Path
from aiohttp import web
from abc import ABC, abstractmethod
import logging
import configparser
import asyncio
import aiohttp
import asyncpg
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
    def __init__(self,
                 host: str = None,
                 port: int = None,
                 user: str = None,
                 password: str = None,
                 database: str = None,
                 pool: asyncpg.Pool = None,
                 config: CustomConfigParser = None):

        if not host:
            self.host = config.get('Database', 'host')
        else:
            self.host = host
        if not port:
            self.port = config.get('Database', 'port')
        else:
            self.port = port
        if not user:
            self.user = config.get('Database', 'user')
        else:
            self.user = user
        if not password:
            self.password = config.get('Database', 'password')
        else:
            self.password = password
        if not database:
            self.database = config.get('Database', 'database')
        else:
            self.database = database
        self.pool = pool

    async def create_pool_if_not_exist(self):
        try:
            if not self.pool:
                self.pool = await asyncpg.create_pool(host=self.host,
                                                      port=self.port,
                                                      user=self.user,
                                                      password=self.password,
                                                      database=self.database
                                                      )
        except ConnectionError:
            print('Can\'t create connection\'s pool for database')


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


class User:
    def __init__(self,
                 chat_id: int,
                 is_bot: bool,
                 phone: str = None,
                 name: str = None,
                 surname: str = None,
                 role: str = None,
                 current_client: bool = None,
                 user_id: str = None):
        
        self.__chat_id = chat_id
        self.__is_bot = is_bot
        self.__phone = phone
        self.__name = name
        self.__surname = surname
        self.__role = role
        self.__current_client = current_client
        self.__user_id = user_id

    @property
    def chat_id(self):
        return self.__chat_id

    @property
    def is_bot(self):
        return self.__is_bot

    @property
    def phone(self):
        return self.__phone

    @property
    def name(self):
        return self.__name

    @property
    def surname(self):
        return self.__surname

    @property
    def role(self):
        return self.__role

    @property
    def current_client(self):
        return self.__current_client

    @property
    def user_id(self):
        return self.__user_id

    async def find(self, connection: asyncpg.connection.Connection):
        if await connection.fetchval('SELECT COUNT(*) FROM users WHERE chat_id = $1;', self.chat_id) == 0:
            await self.register(connection)
            self.__user_id = await connection.fetchval('SELECT user_id FROM users WHERE chat_id = $1;', self.chat_id)
        else:
            user_info = dict(await connection.fetchrow('SELECT phone, name, surname, role, current_client, user_id '
                                                       'FROM users '
                                                       'WHERE chat_id = $1;',
                                                       self.chat_id))
            self.__phone = user_info['phone']
            self.__name = user_info['name']
            self.__surname = user_info['surname']
            self.__role = user_info['role']
            self.__current_client = user_info['current_client']
            self.__user_id = user_info['user_id']

    async def register(self, connection: asyncpg.connection.Connection):
        await connection.execute('INSERT INTO users (chat_id) VALUES ($1);', self.chat_id)

    def __repr__(self):
        return f'User(' \
               f'{self.chat_id}, ' \
               f'{self.is_bot}, ' \
               f'{self.phone}, ' \
               f'{self.name}, ' \
               f'{self.surname}, ' \
               f'{self.role}, ' \
               f'{self.current_client}, ' \
               f'{self.user_id})'


class Data(ABC):
    def __init__(self, value: str):
        self.__value = value

    @property
    def value(self):
        return self.__value

    @abstractmethod
    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        pass


class Command(Data):
    def __init__(self, command: str):
        super().__init__(command)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        await connection.execute('INSERT INTO commands (value, user_id) VALUES ($1, $2)', self.value, user_id)

    def __repr__(self):
        return f'Command({self.value})'


class Text(Data):
    def __init__(self, text: str):
        super().__init__(text)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        await connection.execute('INSERT INTO texts (value, user_id) VALUES ($1, $2);', self.value, user_id)

    def __repr__(self):
        return f'Text({self.value})'


class Audio(Data):
    def __init__(self, audio_id: str, caption: str = None):
        super().__init__(audio_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        await connection.execute('INSERT INTO audios (value, user_id, caption) VALUES ($1, $2, $3);',
                                 self.value, user_id, self.caption)

    def __repr__(self):
        return f'Audio({self.value}, {self.caption})'


class Video(Data):
    def __init__(self, video_id: str, caption: str = None):
        super().__init__(video_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        await connection.execute('INSERT INTO videos (value, user_id, caption) VALUES ($1, $2, $3);',
                                 self.value, user_id, self.caption)

    def __repr__(self):
        return f'Video({self.value}, {self.caption})'


class Document(Data):
    def __init__(self, document_id: str, caption: str = None):
        super().__init__(document_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        await connection.execute('INSERT INTO documents (value, user_id, caption) VALUES ($1, $2, $3);',
                                 self.value, user_id, self.caption)

    def __repr__(self):
        return f'Document({self.value}, {self.caption})'


class Photo(Data):
    def __init__(self, photo_id: str, caption: str = None):
        super().__init__(photo_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str):
        await connection.execute('INSERT INTO photos (value, user_id, caption) VALUES ($1, $2, $3);',
                                 self.value, user_id, self.caption)

    def __repr__(self):
        return f'Photo({self.value}, {self.caption})'


class Update(ABC):
    def __init__(self, update_id: int = None, data: Data = None, user: User = None, json_update: dict = None):
        if not update_id:
            self.__update_id = json_update['update_id']
        else:
            self.__update_id = update_id
        if not data:
            self.data = self._get_data(json_update)
        else:
            self.data = data
        if not user:
            self.user = User(chat_id=json_update[list(json_update)[1]]['from']['id'],
                             is_bot=json_update[list(json_update)[1]]['from']['is_bot'])
        else:
            self.user = user

    @property
    def update_id(self):
        return self.__update_id

    @staticmethod
    @abstractmethod
    def _get_data(json_update: dict) -> Data:
        pass

    async def save(self, connection: asyncpg.connection.Connection):
        await self.data.save(connection, self.user.user_id)

    def __repr__(self):
        return f'Update({self.update_id}, {self.data}, {self.user})'


class CallbackQuery(Update):
    @staticmethod
    def _get_data(json_update: dict) -> Data:
        message_type = list(json_update['callback_query'])[4]
        if message_type == 'data':
            return Command(json_update['callback_query']['data'])


class Message(Update):
    @staticmethod
    def _get_data(json_update: dict) -> Data:
        message_type = list(json_update['message'])[4]  # photo, document, text and so on
        if message_type == 'text':
            command = re.findall('/[a-z]+', json_update['message']['text'])
            if len(command) == 0:
                return Text(text=json_update['message']['text'])
            else:
                return Command(command=command[0])
        if message_type == 'document':
            return Document(document_id=json_update['message']['document']['file_id'],
                            caption=json_update['message'].get('caption'))
        elif message_type == 'audio':
            return Audio(audio_id=json_update['message']['audio']['file_id'],
                         caption=json_update['message'].get('caption'))
        elif message_type == 'video':
            return Video(video_id=json_update['message']['video']['file_id'],
                         caption=json_update['message'].get('caption'))
        elif message_type == 'photo':
            return Photo(photo_id=json_update['message']['photo'][-1]['file_id'],
                         caption=json_update['message'].get('caption'))


class Other(Update):
    @staticmethod
    def _get_data(json_update: dict) -> Data:
        pass


class Controller:
    def __init__(self):
        self.handle_command = {'/start': 123
                               # '/register': self.register,
                               # '/register_scratch': self,
                               # '/alter_user_data': self.view.alter_user_data,
                               # '/navigation': self.navigation
                               }

    @staticmethod
    async def handle_update(request: object):
        json_update = await request.json()
        update_type = list(json_update)[1]  # message or callback_query
        if update_type == 'callback_query':
            update = CallbackQuery(json_update=json_update)
        elif update_type == 'message':
            update = Message(json_update=json_update)
        else:
            update = Other(json_update=json_update)
        if update.data:     # if data not None (i.e. this update type is supported)
            if not update.user.is_bot:
                await request.app['database'].create_pool_if_not_exist()
                async with request.app['database'].pool.acquire() as connection:
                    async with connection.transaction():
                        await update.user.find(connection)
                        await update.save(connection)
                        print(update)

            # print(1) # add command check

            # if not await update.user.is_bot:
            #     print(await update)
            #     if isinstance(update.data, Command):
            #         await self.handle_command[update.data.value](update)
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


async def init_app():
    app = web.Application()
    app['config'] = CustomConfigParser()
    app['config'].read(Path.cwd().parent / 'config.ini')  # path_to_config_file / config_name
    app['database'] = Database(config=app['config'])
    app['controller'] = Controller()
    app.add_routes([web.post(f'/', app['controller'].handle_update)])
    return app

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app)
