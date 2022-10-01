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
