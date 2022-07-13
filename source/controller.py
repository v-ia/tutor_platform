import asyncio
import asyncpg
from data import Message, CallbackQuery, Update, Other
from view import SendMessage, Text, Photo, InlineKeyboardButton, InlineKeyboardMarkup, SendPhoto
from aiohttp import web


class Controller:
    command_handlers = {}

    @staticmethod
    async def start(request: object, update: Update):
        keyboard = InlineKeyboardMarkup()
        if not update.user.role:
            text = 'Добро пожаловать! :) С помощью бота Вы всегда будете в курсе Вашего расписания, домашних ' \
                   'заданий, сможете отменять и назначать занятия и многое другое! Для начала нужно пройти ' \
                   'небольшую регистрацию (требуется лишь 1 раз).'
            keyboard.add_button(InlineKeyboardButton('Начать регистрацию', '/register'))
        elif update.user.role == 'parent':
            pass
        elif update.user.role == 'parent':
            pass
        elif update.user.role == 'parent':
            pass
        data_to_send = Text(text)
        response = SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()

    @staticmethod
    async def respond(request: object, update: Update):
        async with request.app['database'].pool.acquire() as connection:
            try:    # fixing updates order
                await asyncio.wait_for(update.fix_order(connection, int(request.app['config'].get('Bot', 'response_delay'))),
                                       timeout=int(request.app['config'].get('Bot', 'timeout')))
            except asyncio.TimeoutError:
                pass
            finally:
                await update.set_updates_responded(connection)  # setting updates responded that wasn't processed
                await update.set_responded(connection)  # set current update responded
                last_command = await update.user.last_command(connection)
                try:
                    await request.app['controller'].command_handlers[last_command](request, update)
                except KeyError:
                    await request.app['controller'].command_handlers['/start'](request, update)

    @staticmethod
    async def handle_update(request: object):
        json_update = await request.json()
        update_type = list(json_update)[1]  # message or callback_query
        if update_type == 'callback_query':
            update = CallbackQuery(json_update=json_update)
        elif update_type == 'message':
            update = Message(json_update=json_update)
        else:
            update = Other(json_update=json_update)
        if update.data:     # if data not None (i.e. this update type is supported)
            if not update.user.is_bot:
                await request.app['database'].create_pool_if_not_exist()
                async with request.app['database'].pool.acquire() as connection:
                    if not await update.exist(connection):    # repeating update check
                        async with connection.transaction():
                            await update.user.find(connection)
                            await update.data.save(connection, update.user.user_id, update.update_id)
                        # Response for user
                        task = asyncio.create_task(Controller.respond(request, update))
                        request.app['background_tasks'].add(task)
                        task.add_done_callback(request.app['background_tasks'].discard)
        return web.json_response()  # 200 (OK) response

    # async def navigation(self, data: dict):
    #     user_info = await self.model.user_check(data)
    #     if user_info:
    #         if user_info['role'] == 'student':
    #             await self.view.send_menu(data, self.view.menu_student)
    #         elif user_info['role'] == 'parent':
    #             await self.view.send_menu(data, self.view.menu_parent)
    #         elif user_info['role'] == 'tutor':
    #             await self.view.send_menu(data, self.view.menu_tutor)
    #         else:
    #             await self.register(data)
    #     else:
    #         await self.view.start(data)