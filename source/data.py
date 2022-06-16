from abc import ABC, abstractmethod
from customconfigparser import CustomConfigParser
from user import User
import asyncpg
import re
import asyncio
import aiohttp


# Interface for data types classes

class Data(ABC):
    def __init__(self, value: str):
        self.__value = value

    @property
    def value(self) -> str:
        return self.__value

    @abstractmethod
    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        pass


# Types of data that income and parse via Updates from Telegram

class Command(Data):
    def __init__(self, command: str):
        super().__init__(command)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        await connection.execute('INSERT INTO updates (value, user_id, update_id) VALUES ($1, $2, $3);',
                                 self.value, user_id, update_id)

    def __repr__(self):
        return f'Command({self.value})'


class Text(Data):
    def __init__(self, text: str, value_id: int = None):
        super().__init__(text)
        self.__value_id = value_id

    @property
    def value_id(self) -> int:
        return self.__value_id

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.__value_id = await connection.fetchval('INSERT INTO texts (value) VALUES ($1) RETURNING text_id;',
                                                    self.value)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/text', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Text({self.value}, {self.value_id})'


class Audio(Data):
    def __init__(self, audio_id: str, caption: str = None, value_id: int = None):
        super().__init__(audio_id)
        self.__caption = caption
        self.__value_id = value_id

    @property
    def caption(self) -> str:
        return self.__caption

    @property
    def value_id(self) -> int:
        return self.__value_id

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.__value_id = await connection.fetchval('INSERT INTO audios (value, caption) '
                                                    'VALUES ($1, $2) RETURNING audio_id;',
                                                    self.value, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/audio', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Audio({self.value}, {self.caption}, {self.value_id})'


class Video(Data):
    def __init__(self, video_id: str, caption: str = None, value_id: int = None):
        super().__init__(video_id)
        self.__caption = caption
        self.__value_id = value_id

    @property
    def caption(self) -> str:
        return self.__caption

    @property
    def value_id(self) -> int:
        return self.__value_id

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.__value_id = await connection.fetchval('INSERT INTO videos (value, caption) '
                                                    'VALUES ($1, $2) RETURNING video_id;',
                                                    self.value, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/video', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Video({self.value}, {self.caption}, {self.value_id})'


class Document(Data):
    def __init__(self, document_id: str, caption: str = None, value_id: int = None):
        super().__init__(document_id)
        self.__caption = caption
        self.__value_id = value_id

    @property
    def caption(self) -> str:
        return self.__caption

    @property
    def value_id(self) -> int:
        return self.__value_id

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.__value_id = await connection.fetchval('INSERT INTO documents (value, caption) '
                                                    'VALUES ($1, $2) RETURNING document_id;',
                                                    self.value, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/document', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Document({self.value}, {self.caption}, {self.value_id})'


class Photo(Data):
    def __init__(self, photo_id: str, caption: str = None, value_id: int = None):
        super().__init__(photo_id)
        self.__caption = caption
        self.__value_id = value_id

    @property
    def caption(self) -> str:
        return self.__caption

    @property
    def value_id(self) -> int:
        return self.__value_id

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.__value_id = await connection.fetchval('INSERT INTO photos (value, caption) '
                                                    'VALUES ($1, $2) RETURNING photo_id;',
                                                    self.value, self.caption)
        await connection.execute('INSERT INTO updates (value, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 '/photo', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Photo({self.value}, {self.caption}, {self.value_id})'


# Update class (interface) that comes from Telegram

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
    def update_id(self) -> int:
        return self.__update_id

    async def exist(self, connection: asyncpg.connection.Connection) -> int:
        return await connection.fetchval('SELECT COUNT(*) FROM updates WHERE update_id = $1;', self.update_id)

    async def count_updates_no_resp(self, connection: asyncpg.connection.Connection) -> int:
        return await connection.fetchval('SELECT COUNT(*) FROM updates '
                                         'WHERE responded = $1 AND update_id < $2 AND user_id = $3;',
                                         False, self.update_id, self.user.user_id)

    async def set_updates_responded(self, connection: asyncpg.connection.Connection):
        await connection.execute('UPDATE updates SET responded = $1 '
                                 'WHERE responded = $2 AND update_id < $3 AND user_id = $3;',
                                 True, False, self.update_id, self.user.user_id)

    async def set_responded(self, connection: asyncpg.connection.Connection):
        await connection.execute('UPDATE updates SET responded = $1 WHERE update_id = $2;', True, self.update_id)

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

