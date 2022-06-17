from customconfigparser import CustomConfigParser
from data import Update, Data, Text, Audio, Photo, Video, Document
import asyncpg
import asyncio
import aiohttp
from abc import ABC, abstractmethod


# Button class for InlineKeyboardMarkup

class InlineKeyboardButton:
    def __init__(self, button_text: str, command: str):
        self.__text = button_text
        self.__callback_data = command

    @property
    def text(self) -> str:
        return self.__text

    @property
    def callback_data(self) -> str:
        return self.__callback_data

    def dict(self) -> dict:
        return {'text': self.text, 'callback_data': self.callback_data}


# Interface for keyboard classes

class ReplyMarkup(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def dict(self) -> dict:
        pass


# Inline keyboard for responses

class InlineKeyboardMarkup(ReplyMarkup):
    def __init__(self):
        self.__inline_keyboard = [[]]

    @property
    def inline_keyboard(self) -> list:
        return self.__inline_keyboard

    def add_button(self, button: InlineKeyboardButton):
        if isinstance(button, InlineKeyboardButton):
            self.__inline_keyboard[-1].append(button)
        else:
            raise TypeError('Button object should be instance of InlineKeyboardButton class')

    def add_line(self):
        self.__inline_keyboard.append([])

    def dict(self) -> dict:
        inline_keyboard_dict = []
        for num, line in enumerate(self.__inline_keyboard):
            inline_keyboard_dict.append([])
            for button in line:
                inline_keyboard_dict[num].append(button.dict())
        return {'inline_keyboard': inline_keyboard_dict}


# Interface for response classes

class SendData(ABC):
    def __init__(self, config: CustomConfigParser, chat_id: int, data: Data, reply_markup: ReplyMarkup = None):
        self.__chat_id = chat_id
        self.data = data
        if isinstance(reply_markup, ReplyMarkup) or not reply_markup:
            self.__reply_markup = reply_markup
        else:
            raise TypeError('reply_markup object should be instance of ReplyMarkup class or subclass')
        self.__bot_token = config.get('Bot', 'bot_token')
        self.__server_url = config.get('Bot', 'server_url')
        self.__request_attempts = config.get('Bot', 'request_attempts')

    @property
    def chat_id(self) -> int:
        return self.__chat_id

    @property
    def reply_markup(self) -> ReplyMarkup:
        return self.__reply_markup

    @property
    def bot_token(self) -> str:
        return self.__bot_token

    @property
    def server_url(self) -> str:
        return self.__server_url

    @property
    def request_attempts(self) -> int:
        return int(self.__request_attempts)

    async def send(self) -> int:
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.request_attempts):
                await asyncio.sleep(1 * attempt)
                async with session.post(f'{self.server_url}bot{self.bot_token}/{self.__class__.__name__}',
                                        json=self.dict()
                                        ) as request:
                    json_answer = await request.json()
                    if request.status == 200:
                        return json_answer['ok']

    def dict(self) -> dict:
        data_to_send = {'chat_id': self.chat_id, str.lower(self.data.__class__.__name__): self.data.value}
        try:
            data_to_send['caption'] = self.data.caption
        except AttributeError:
            pass
        finally:
            if self.reply_markup:
                data_to_send['reply_markup'] = self.reply_markup.dict()
            return data_to_send


# Classes for responses

class SendMessage(SendData):
    def __init__(self, config: CustomConfigParser, chat_id: int, data: Text, reply_markup: ReplyMarkup = None):
        super().__init__(config, chat_id, data, reply_markup)


class SendPhoto(SendData):
    def __init__(self, config: CustomConfigParser, chat_id: int, data: Photo, reply_markup: ReplyMarkup = None):
        super().__init__(config, chat_id, data, reply_markup)


class SendVideo(SendData):
    def __init__(self, config: CustomConfigParser, chat_id: int, data: Video, reply_markup: ReplyMarkup = None):
        super().__init__(config, chat_id, data, reply_markup)


class SendDocument(SendData):
    def __init__(self, config: CustomConfigParser, chat_id: int, data: Document, reply_markup: ReplyMarkup = None):
        super().__init__(config, chat_id, data, reply_markup)


class Response:
    def __init__(self, request: object, update: Update):
        self.request = request
        self.update = update
        self.pool = request.app['database'].pool
        self.__response_delay = int(request.app['config'].get('Bot', 'response_delay'))
        self.__timeout = int(request.app['config'].get('Bot', 'timeout'))

    @property
    def response_delay(self):
        return self.__response_delay

    @property
    def timeout(self):
        return self.__timeout

    async def respond(self):
        async with self.pool.acquire() as connection:
            try:    # fixing updates order
                await asyncio.wait_for(self.update.fix_order(connection, self.response_delay), timeout=self.timeout)
            except asyncio.TimeoutError:
                pass
            finally:
                await self.update.set_updates_responded(connection)  # setting updates responded that wasn't processed
                await self.update.set_responded(connection)  # set current update responded
                await self.update.respode()
                last_command = await self.update.user.last_command(connection)
                if last_command:
                    await self.request.app['controller'].hello(self.update)
                else:
                    pass


class ViewBot:
    def __init__(self, config: CustomConfigParser):
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