import asyncio
import asyncpg
from data import Message, CallbackQuery, Update, Other
from view import SendMessage, Text, Photo, InlineKeyboardButton, InlineKeyboardMarkup, SendPhoto
from aiohttp import web
from user import User, Tutor, Parent, Student


class Controller:
    handler_factories = {}

    # Acceptation and saving update data
    @staticmethod
    async def save_update(request: object):
        json_update = await request.json()
        update_type = list(json_update)[1]  # message or callback_query
        if update_type == 'callback_query':
            update = CallbackQuery(json_update=json_update)
        elif update_type == 'message':
            update = Message(json_update=json_update)
        else:
            update = Other(json_update=json_update)
        if update.data:     # if data not None (i.e. this update type is supported)
            await request.app['database'].create_pool_if_not_exist()
            async with request.app['database'].pool.acquire() as connection:
                if not await update.exist(connection):    # repeating update check
                    async with connection.transaction():
                        await update.find_user(json_update, connection)
                        if not update.user.is_bot:
                            await update.data.save(connection, update.user.user_id, update.update_id)
                            task = asyncio.create_task(Controller.handle_update(request, update))
                            request.app['background_tasks'].add(task)
                            task.add_done_callback(request.app['background_tasks'].discard)
        return web.json_response()  # 200 (OK) response

    """
    Fixing updates order
    Handling saved information from update
    Creation factory object for generation commands handlers
    Responding to user
    """
    @staticmethod
    async def handle_update(request: object, update: Update):
        async with request.app['database'].pool.acquire() as connection:
            try:  # fixing updates order
                await asyncio.wait_for(
                    update.fix_order(connection, int(request.app['config'].get('Bot', 'response_delay'))),
                    timeout=int(request.app['config'].get('Bot', 'timeout')))
            except asyncio.TimeoutError:
                pass
            finally:
                await update.set_updates_responded(connection)  # setting updates responded that wasn't processed
                await update.set_responded(connection)  # set current update responded
                last_command = await update.user.last_command(connection)
                handler_factory = request.app['controller'].handler_factories.get(
                    last_command,
                    request.app['controller'].handler_factories.get('/help'))()
                if handler_factory:
                    if isinstance(update.user, Tutor) and update.user.current_client:
                        handler = handler_factory.create_tutor_handler()
                    elif isinstance(update.user, Student) and update.user.current_client:
                        handler = handler_factory.create_student_handler()
                    elif isinstance(update.user, Parent) and update.user.current_client:
                        handler = handler_factory.create_parent_handler()
                    else:
                        handler = handler_factory.create_user_handler()
                    await handler.respond(request, update, connection)
