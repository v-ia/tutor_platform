import asyncio
from data import Message, CallbackQuery, Update, Other
from view import SendMessage, Text, Photo, InlineKeyboardButton, InlineKeyboardMarkup, SendPhoto
from view import Response
from aiohttp import web


class Controller:
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
                        response = Response(request, update)
                        task = asyncio.create_task(response.respond())
                        request.app['background_tasks'].add(task)
                        task.add_done_callback(request.app['background_tasks'].discard)
                            # keyboard = InlineKeyboardMarkup()
                            # keyboard.add_button(InlineKeyboardButton('Here is button', '/button'))
                            # keyboard.add_button(InlineKeyboardButton('Here is 2 button', '/button2'))
                            # keyboard.add_line()
                            # keyboard.add_button(InlineKeyboardButton('Here is 3 button', '/button3'))
                            # answer = SendPhoto(request.app['config'], update.user.chat_id, Photo('Hello', 'caption'), keyboard)
                            # print(answer.dict())
                            # await answer.send()

                            # task = asyncio.create_task(Controller.test(update))
                            # request.app['background_tasks'].add(task)
                            # task.add_done_callback(request.app['background_tasks'].discard)

                            # response = Response()
                            # await response.send()
                            # print(update)   # Right order of updates (fix table commands)
        return web.json_response()  # 200 (OK) response

    @staticmethod
    async def hello(update):
        print(update)

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