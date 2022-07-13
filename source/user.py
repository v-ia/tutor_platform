import asyncpg
import uuid


class User:
    def __init__(self,
                 chat_id: int,
                 is_bot: bool,
                 phone: str = None,
                 name: str = None,
                 surname: str = None,
                 current_client: bool = None,
                 user_id: uuid.UUID = None):

        self.__chat_id = chat_id
        self.__is_bot = is_bot
        self.__phone = phone
        self.__name = name
        self.__surname = surname
        self.__current_client = current_client
        self.__user_id = user_id

    @property
    def chat_id(self) -> int:
        return self.__chat_id

    @property
    def is_bot(self) -> bool:
        return self.__is_bot

    @property
    def phone(self) -> str:
        return self.__phone

    @property
    def name(self) -> str:
        return self.__name

    @property
    def surname(self) -> str:
        return self.__surname

    @property
    def current_client(self) -> bool:
        return self.__current_client

    @property
    def user_id(self) -> uuid.UUID:
        return self.__user_id

    async def register(self, connection: asyncpg.connection.Connection):
        self.__user_id = uuid.UUID(await connection.fetchval('INSERT INTO users (chat_id) VALUES ($1) '
                                                             'RETURNING user_id;',
                                                             self.chat_id))

    async def last_command(self, connection: asyncpg.connection.Connection):
        return await connection.fetchval('SELECT value FROM updates JOIN commands '
                                         'ON updates.value_id = commands.command_id '
                                         'WHERE user_id = $1 AND type = $2 ORDER BY update_id DESC LIMIT 1;',
                                         self.user_id, 'command')

    def __repr__(self):
        return f'User(' \
               f'{self.chat_id}, ' \
               f'{self.is_bot}, ' \
               f'{self.phone}, ' \
               f'{self.name}, ' \
               f'{self.surname}, ' \
               f'{self.current_client}, ' \
               f'{self.user_id})'


class Parent(User):
    def __init__(self,
                 chat_id: int,
                 is_bot: bool,
                 phone: str = None,
                 name: str = None,
                 surname: str = None,
                 current_client: bool = None,
                 user_id: uuid.UUID = None):
        super().__init__(chat_id, is_bot, phone, name, surname, current_client, user_id)
        self.__children = []

    @property
    def children(self):
        return self.__children

    async def find_children(self, connection: asyncpg.connection.Connection):
        res = await connection.fetch('SELECT child_id FROM families WHERE parent_id = $1;', self.user_id)
        self.__children = [record['child_id'] for record in res]
        print(self.__children)

    def __repr__(self):
        return f'Parent(' \
               f'{self.chat_id}, ' \
               f'{self.is_bot}, ' \
               f'{self.phone}, ' \
               f'{self.name}, ' \
               f'{self.surname}, ' \
               f'{self.current_client}, ' \
               f'{self.user_id})'


class Student(User):
    def __init__(self,
                 chat_id: int,
                 is_bot: bool,
                 phone: str = None,
                 name: str = None,
                 surname: str = None,
                 current_client: bool = None,
                 user_id: uuid.UUID = None):
        super().__init__(chat_id, is_bot, phone, name, surname, current_client, user_id)
        self.__parents = []

    @property
    def parents(self):
        return self.__parents

    def __repr__(self):
        return f'Student(' \
               f'{self.chat_id}, ' \
               f'{self.is_bot}, ' \
               f'{self.phone}, ' \
               f'{self.name}, ' \
               f'{self.surname}, ' \
               f'{self.current_client}, ' \
               f'{self.user_id})'


class Tutor(User):
    pass

    def __repr__(self):
        return f'Tutor(' \
               f'{self.chat_id}, ' \
               f'{self.is_bot}, ' \
               f'{self.phone}, ' \
               f'{self.name}, ' \
               f'{self.surname}, ' \
               f'{self.current_client}, ' \
               f'{self.user_id})'
