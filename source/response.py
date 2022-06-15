from customconfigparser import CustomConfigParser
import asyncpg
import asyncio
import aiohttp
from abc import ABC, abstractmethod


class Response:
    def __init__(self, config: CustomConfigParser):
        self.__response_delay = config.get('Bot', 'response_delay')

    @property
    def response_delay(self):
        return self.__response_delay

    async def find_update_without_response(self, connection: asyncpg.connection.Connection):
        await asyncio.sleep(self.response_delay)
        await connection.fetchval('SELECT COUNT(*) FROM updates WHERE responded = $1;', 'FALSE')


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