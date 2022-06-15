import asyncio
from data import Message, CallbackQuery, Other
from aiohttp import web


class Controller:
    def __init__(self):
        self.handle_command = {'/start': 123
                               # '/register': self.register,
                               # '/register_scratch': self,
                               # '/alter_user_data': self.view.alter_user_data,
                               # '/navigation': self.navigation
                               }

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
                    async with connection.transaction():
                        if not await update.exist(connection):    # repeating update check
                            await update.user.find(connection)
                            await update.data.save(connection, update.user.user_id, update.update_id)

                            # task = asyncio.create_task(Controller.test(update))
                            # request.app['background_tasks'].add(task)
                            # task.add_done_callback(request.app['background_tasks'].discard)

                            # response = Response()
                            # await response.send()
                            # print(update)   # Right order of updates (fix table commands)
        return web.json_response()  # 200 (OK) response

    @staticmethod
    async def test(update):
        await asyncio.sleep(10)
        print(update)  # Right order of updates (fix table commands)

    async def navigation(self, data: dict):
        user_info = await self.model.user_check(data)
        if user_info:
            if user_info['role'] == 'student':
                await self.view.send_menu(data, self.view.menu_student)
            elif user_info['role'] == 'parent':
                await self.view.send_menu(data, self.view.menu_parent)
            elif user_info['role'] == 'tutor':
                await self.view.send_menu(data, self.view.menu_tutor)
            else:
                await self.register(data)
        else:
            await self.view.start(data)