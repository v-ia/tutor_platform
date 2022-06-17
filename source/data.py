from abc import ABC, abstractmethod
from customconfigparser import CustomConfigParser
from user import User
import asyncpg
import re
import asyncio
import aiohttp


# Interface for data types classes

class Data(ABC):
    def __init__(self, value: str, value_id: int):
        self.__value = value
        self.__value_id = value_id

    @property
    def value(self) -> str:
        return self.__value

    @property
    def value_id(self) -> int:
        return self.__value_id

    @value_id.setter
    def value_id(self, value_id):
        self.__value_id = value_id

    @abstractmethod
    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        pass


# Types of data that income and parse via Updates from Telegram

class Command(Data):
    def __init__(self, command: str, value_id: int = None):
        super().__init__(command, value_id)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.value_id = await connection.fetchval('INSERT INTO commands (value) VALUES ($1) RETURNING command_id;',
                                                  self.value)
        await connection.execute('INSERT INTO updates (type, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 'command', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Command({self.value})'


class Text(Data):
    def __init__(self, text: str, value_id: int = None):
        super().__init__(text, value_id)

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.value_id = await connection.fetchval('INSERT INTO texts (value) VALUES ($1) RETURNING text_id;',
                                                  self.value)
        await connection.execute('INSERT INTO updates (type, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 'text', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Text({self.value})'


class Audio(Data):
    def __init__(self, audio_id: str, caption: str = None, value_id: int = None):
        super().__init__(audio_id, value_id)
        self.__caption = caption

    @property
    def caption(self) -> str:
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.value_id = await connection.fetchval('INSERT INTO audios (value, caption) '
                                                  'VALUES ($1, $2) RETURNING audio_id;',
                                                  self.value, self.caption)
        await connection.execute('INSERT INTO updates (type, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 'audio', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Audio({self.value}, {self.caption})'


class Video(Data):
    def __init__(self, video_id: str, caption: str = None, value_id: int = None):
        super().__init__(video_id, value_id)
        self.__caption = caption

    @property
    def caption(self) -> str:
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.value_id = await connection.fetchval('INSERT INTO videos (value, caption) '
                                                  'VALUES ($1, $2) RETURNING video_id;',
                                                  self.value, self.caption)
        await connection.execute('INSERT INTO updates (type, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 'video', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Video({self.value}, {self.caption},)'


class Document(Data):
    def __init__(self, document_id: str, caption: str = None, value_id: int = None):
        super().__init__(document_id, value_id)
        self.__caption = caption

    @property
    def caption(self) -> str:
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.value_id = await connection.fetchval('INSERT INTO documents (value, caption) '
                                                  'VALUES ($1, $2) RETURNING document_id;',
                                                  self.value, self.caption)
        await connection.execute('INSERT INTO updates (type, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 'document', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Document({self.value}, {self.caption})'


class Photo(Data):
    def __init__(self, photo_id: str, caption: str = None, value_id: int = None):
        super().__init__(photo_id, value_id)
        self.__caption = caption

    @property
    def caption(self) -> str:
        return self.__caption

    async def save(self, connection: asyncpg.connection.Connection, user_id: str, update_id: int):
        self.value_id = await connection.fetchval('INSERT INTO photos (value, caption) '
                                                  'VALUES ($1, $2) RETURNING photo_id;',
                                                  self.value, self.caption)
        await connection.execute('INSERT INTO updates (type, user_id, update_id, value_id) VALUES ($1, $2, $3, $4);',
                                 'photo', user_id, update_id, self.value_id)

    def __repr__(self):
        return f'Photo({self.value}, {self.caption})'


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
                                 'WHERE responded = $2 AND update_id < $3 AND user_id = $4;',
                                 True, False, self.update_id, self.user.user_id)

    async def set_responded(self, connection: asyncpg.connection.Connection):
        await connection.execute('UPDATE updates SET responded = $1 WHERE update_id = $2;', True, self.update_id)

    async def fix_order(self, connection: asyncpg.connection.Connection, response_delay: int):
        await asyncio.sleep(response_delay)    # waiting for next updates
        updates_count = await self.count_updates_no_resp(connection)     # how many updates came in wrong order
        while updates_count:
            await asyncio.sleep(response_delay)    # waiting for processing previous updates
            updates_count = await self.count_updates_no_resp(connection)  # how many updates left in wrong order

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
