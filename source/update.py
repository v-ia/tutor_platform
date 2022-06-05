from user import User
from data import Data, Command, Document, Video, Audio, Photo, Text
from abc import ABC, abstractmethod
import asyncpg
import re


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
