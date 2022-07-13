import asyncpg


class User:
    def __init__(self,
                 chat_id: int,
                 is_bot: bool,
                 phone: str = None,
                 name: str = None,
                 surname: str = None,
                 role: str = None,
                 current_client: bool = None,
                 user_id: str = None) :

        self.__chat_id = chat_id
        self.__is_bot = is_bot
        self.__phone = phone
        self.__name = name
        self.__surname = surname
        self.__role = role
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
    def role(self) -> str:
        return self.__role

    @property
    def current_client(self) -> bool:
        return self.__current_client

    @property
    def user_id(self) -> str:
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
               f'{self.role}, ' \
               f'{self.current_client}, ' \
               f'{self.user_id})'


class Parent(User):
