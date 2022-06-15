from abc import ABC, abstractmethod
import asyncpg
from user import User
import re


# Interface for data types classes

class Data(ABC):
    def __init__(self, value: str):
        self.__value = value

    @property
    def value(self):
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


# Update class that comes from Telegram and contains different types of update (Message, CallbackQuery and so on)

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


# Button class for InlineKeyboardMarkup

class InlineKeyboardButton:
    def __init__(self, button_text: str, command: str):
        self.__text = button_text
        self.__callback_data = command

    @property
    def text(self):
        return self.__text

    @property
    def callback_data(self):
        return self.__callback_data

    def dict(self):
        return {'text': self.text, 'callback_data': self.callback_data}


# Interface for keyboard classes

class ReplyMarkup(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def dict(self):
        pass


# Inline keyboard for responses

class InlineKeyboardMarkup(ReplyMarkup):
    def __init__(self):
        self.__inline_keyboard = [[]]

    @property
    def inline_keyboard(self):
        return self.__inline_keyboard

    def add_button(self, button: InlineKeyboardButton):
        if isinstance(button, InlineKeyboardButton):
            self.__inline_keyboard[-1].append(button)
        else:
            raise TypeError('Button object should be instance of InlineKeyboardButton class')

    def new_line_of_buttons(self):
        self.__inline_keyboard.append([])

    def dict(self):
        inline_keyboard_dict = []
        for num, line in enumerate(self.__inline_keyboard):
            inline_keyboard_dict.append([])
            for button in line:
                inline_keyboard_dict[num].append(button.dict())
        return {'inline_keyboard': inline_keyboard_dict}


# Interface for response classes

class SendData(ABC):
    def __init__(self, chat_id: int, reply_markup: ReplyMarkup = None):
        self.__chat_id = chat_id
        if isinstance(reply_markup, ReplyMarkup) or not reply_markup:
            self.__reply_markup = reply_markup
        else:
            raise TypeError('reply_markup object should be instance of ReplyMarkup class or subclass')

    @property
    def chat_id(self):
        return self.__chat_id

    @property
    def reply_markup(self):
        return self.__reply_markup

    @abstractmethod
    def dict(self):
        pass


# Classes for responses

class SendMessage(SendData):
    def __init__(self, chat_id: int, text: str, reply_markup: ReplyMarkup = None):
        super().__init__(chat_id, reply_markup)
        self.__chat_id = chat_id
        self.__text = text

    @property
    def text(self):
        return self.__text

    def dict(self):
        send_message_dict = {'chat_id': self.chat_id, 'text': self.text}
        if self.reply_markup:
            send_message_dict['reply_markup'] = self.reply_markup.dict()
        return send_message_dict