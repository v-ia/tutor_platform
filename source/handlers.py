from abc import ABC, abstractmethod
import view
import data
import asyncpg


class UserHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        pass


class TutorHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        pass


class ParentHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        pass


class StudentHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        pass


class HandlerFactory(ABC):
    @abstractmethod
    def create_tutor_handler(self) -> TutorHandler:
        pass

    @abstractmethod
    def create_student_handler(self) -> StudentHandler:
        pass

    @abstractmethod
    def create_parent_handler(self) -> ParentHandler:
        pass

    @abstractmethod
    def create_user_handler(self) -> UserHandler:
        pass


class UserHelp(UserHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        text = 'Выберите действие:'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class StudentHelp(StudentHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        text = f'{update.user.name}, выберите необходимое действие:'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Отправить домашнее задание', '/send_homework'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Расписание занятий', '/schedule'))
        keyboard.add_button(view.InlineKeyboardButton('Что было задано?', '/homework'))
        keyboard.add_line()
        if not update.user.parents:
            keyboard.add_button(view.InlineKeyboardButton('Оплачены ли занятия?', '/payments'))
            keyboard.add_button(view.InlineKeyboardButton('Отменить занятие', '/cancel_lesson'))
            keyboard.add_line()
            keyboard.add_button(view.InlineKeyboardButton('Перенести занятие', '/reschedule_lesson'))
            keyboard.add_button(view.InlineKeyboardButton('Назначить занятие', '/appoint_lesson'))
            keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Редактировать профиль', '/alter_profile'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class ParentHelp(ParentHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        text = f'{update.user.name}, выберите необходимое действие:'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Оплачены ли занятия?', '/payments'))
        keyboard.add_button(view.InlineKeyboardButton('Что задано ребенку?', '/homework'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Расписание занятий', '/schedule'))
        keyboard.add_button(view.InlineKeyboardButton('Назначить занятие', '/appoint_lesson'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Отменить занятие', '/cancel_lesson'))
        keyboard.add_button(view.InlineKeyboardButton('Перенести занятие', '/reschedule_lesson'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Редактировать профиль', '/alter_profile'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class TutorHelp(TutorHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        text = f'{update.user.name}, choose an action:'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Send new homework', '/send_homework'))
        keyboard.add_button(view.InlineKeyboardButton('Send checked homework', '/checked_homework'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Student\'s homeworks', '/homework'))
        keyboard.add_button(view.InlineKeyboardButton('Tag the lesson as paid', '/lesson_as_paid'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Lesson\'s schedule', '/schedule'))
        keyboard.add_button(view.InlineKeyboardButton('Cancel the lesson', '/cancel_lesson'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Reschedule the lesson', '/reschedule_lesson'))
        keyboard.add_button(view.InlineKeyboardButton('Appoint the lesson', '/appoint_lesson'))
        keyboard.add_line()
        keyboard.add_button(view.InlineKeyboardButton('Confirm new user', '/confirm_user'))
        keyboard.add_button(view.InlineKeyboardButton('Edit profile', '/alter_profile'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class HelpFactory(HandlerFactory):
    def create_tutor_handler(self) -> TutorHelp:
        return TutorHelp()

    def create_student_handler(self) -> StudentHelp:
        return StudentHelp()

    def create_parent_handler(self) -> ParentHelp:
        return ParentHelp()

    def create_user_handler(self) -> UserHelp:
        return UserHelp()


class UserStart(UserHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        text = 'Добро пожаловать! :) С помощью бота ученики всегда будут в курсе расписания, смогут отправлять и ' \
               'получать домашние задания, а родители – отменять и назначать занятия, следить за оплатой и многое ' \
               'другое! Для начала нужно пройти небольшую регистрацию (требуется лишь 1 раз). Регистрация доступна ' \
               'как ученикам, так и их родителям.'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class StartFactory(HandlerFactory):
    def create_tutor_handler(self) -> TutorHelp:
        return TutorHelp()

    def create_student_handler(self) -> StudentHelp:
        return StudentHelp()

    def create_parent_handler(self) -> ParentHelp:
        return ParentHelp()

    def create_user_handler(self) -> UserStart:
        return UserStart()


class UserRegister(UserHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        result = await connection.fetch('SELECT value FROM texts JOIN updates ON texts.text_id = updates.value_id '
                                        'WHERE update_id > (SELECT MAX(update_id) FROM updates '
                                        'WHERE type = $1 AND user_id = $2 AND responded = $3) '
                                        'AND type = $4 AND user_id = $5 AND responded = $6 ORDER BY update_id;',
                                        'command', update.user.user_id, True, 'text', update.user.user_id, True)
        data_for_profile = [record['value'] for record in result]
        steps = len(data_for_profile)
        keyboard = view.InlineKeyboardMarkup()
        if not data_for_profile:
            text = 'Регистрация. Шаг 1 из 4. ' \
                   'Выберите из предложенных вариантов, кем Вы являетесь:'
            keyboard.add_button(view.InlineKeyboardButton('Родитель', 'parent'))
            keyboard.add_button(view.InlineKeyboardButton('Ученик', 'student'))
            keyboard.add_line()
        elif steps == 1:
            text = 'Регистрация. Шаг 2 из 4. ' \
                   'Введите Ваше имя (без фамилии):'
        elif steps == 2:
            text = 'Регистрация. Шаг 3 из 4. ' \
                   'Введите Вашу фамилию:'
        elif steps == 3:
            text = 'Регистрация. Шаг 4 из 4. ' \
                   'Введите Ваш номер телефона без пробелов и тире, начиная с +7 (например, +79219876543):'
        elif steps == 4:
            text = 'Регистрация прошла успешно. Дождитесь подтверждения Вашей учетной записи – Вы получите ' \
                   'уведомление об этом.'
        else:
            text = 'В процессе регистрации что-то пошло не так. ' \
                   'Нажмите кнопку \'Прервать регистрацию\' и попробуйте начать заново.'

        keyboard.add_button(view.InlineKeyboardButton('Прервать регистрацию', '/help'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class StudentRegister(UserHandler):
    async def respond(self, request: object, update: data.Update, connection: asyncpg.connection.Connection):
        text = 'Вы уже прошли ранее регистрацию. Подсказать, какой функционал Вам доступен?'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Показать доступные действия', '/help'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class RegisterFactory(HandlerFactory):
    def create_tutor_handler(self) -> StudentRegister:
        return StudentRegister()

    def create_student_handler(self) -> StudentRegister:
        return StudentRegister()

    def create_parent_handler(self) -> StudentRegister:
        return StudentRegister()

    def create_user_handler(self) -> UserRegister:
        return UserRegister()
