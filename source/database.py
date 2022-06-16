import asyncpg
from customconfigparser import CustomConfigParser


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
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port

    @property
    def user(self) -> str:
        return self.__user

    @property
    def password(self) -> str:
        return self.__password

    @property
    def database(self) -> str:
        return self.__database

    @property
    def pool(self) -> asyncpg.Pool:
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
