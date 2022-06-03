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
            self.__host = config.get('Database', 'host')
        else:
            self.__host = host
        if not port:
            self.__port = config.get('Database', 'port')
        else:
            self.__port = port
        if not user:
            self.__user = config.get('Database', 'user')
        else:
            self.__user = user
        if not password:
            self.__password = config.get('Database', 'password')
        else:
            self.__password = password
        if not database:
            self.__database = config.get('Database', 'database')
        else:
            self.__database = database
        self.__pool = pool

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    @property
    def user(self):
        return self.__user

    @property
    def password(self):
        return self.__password

    @property
    def database(self):
        return self.__database

    @property
    def pool(self):
        return self.__pool

    async def create_pool_if_not_exist(self):
        try:
            if not self.pool:
                self.__pool = await asyncpg.create_pool(host=self.host,
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
    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        pass


class Command(Data):
    def __init__(self, command: str):
        super().__init__(command)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        await connection.execute('INSERT INTO updates (value, user_id, update_id) VALUES ($1, $2, $3);',
                                 self.value, user_id, update_id)

    def __repr__(self):
        return f'Command({self.value})'


class Text(Data):
    def __init__(self, text: str):
        super().__init__(text)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        value_id = await connection.fetchval('INSERT INTO texts (value, user_id) VALUES ($1, $2) RETURNING text_id;',
                                             self.value, user_id)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/text', user_id, update_id, value_id)

    def __repr__(self):
        return f'Text({self.value})'


class Audio(Data):
    def __init__(self, audio_id: str, caption: str = None):
        super().__init__(audio_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        value_id = await connection.fetchval('INSERT INTO audios (value, user_id, caption) '
                                             'VALUES ($1, $2, $3) RETURNING audio_id;',
                                             self.value, user_id, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/audio', user_id, update_id, value_id)

    def __repr__(self):
        return f'Audio({self.value}, {self.caption})'


class Video(Data):
    def __init__(self, video_id: str, caption: str = None):
        super().__init__(video_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        value_id = await connection.fetchval('INSERT INTO videos (value, user_id, caption) '
                                             'VALUES ($1, $2, $3) RETURNING video_id;',
                                             self.value, user_id, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/video', user_id, update_id, value_id)

    def __repr__(self):
        return f'Video({self.value}, {self.caption})'


class Document(Data):
    def __init__(self, document_id: str, caption: str = None):
        super().__init__(document_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        value_id = await connection.fetchval('INSERT INTO documents (value, user_id, caption) '
                                             'VALUES ($1, $2, $3) RETURNING document_id;',
                                             self.value, user_id, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/document', user_id, update_id, value_id)

    def __repr__(self):
        return f'Document({self.value}, {self.caption})'


class Photo(Data):
    def __init__(self, photo_id: str, caption: str = None):
        super().__init__(photo_id)
        self.__caption = caption

    @property
    def caption(self):
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        value_id = await connection.fetchval('INSERT INTO photos (value, user_id, caption) '
                                             'VALUES ($1, $2, $3) RETURNING photo_id;',
                                             self.value, user_id, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/photo', user_id, update_id, value_id)

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

    async def exist(self, connection: asyncpg.connection.Connection):
        return await connection.fetchval('SELECT COUNT(*) FROM updates WHERE update_id = $1;', self.__update_id)

    @staticmethod
    @abstractmethod
    def _get_data(json_update: dict) -> Data:
        pass

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
                        if not await update.exist(connection):    # repeating update check
                            await update.user.find(connection)
                            await update.data.save(connection, update.user.user_id, update.update_id)
                            print(update)   # Right order of updates (fix table commands)
        return web.json_response()  # 200 (OK) response

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


if __name__ == '__main__':
    app = web.Application()
    app['config'] = CustomConfigParser()
    app['config'].read(Path.cwd().parent / 'config.ini')  # path_to_config_file / config_name
    app['database'] = Database(config=app['config'])
    app['controller'] = Controller()
    app.add_routes([web.post(f'/', app['controller'].handle_update)])
    web.run_app(app)
