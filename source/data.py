from abc import ABC, abstractmethod
import asyncpg


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
