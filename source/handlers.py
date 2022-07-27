from abc import ABC, abstractmethod
import view
import data


class UserHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update):
        pass


class TutorHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update):
        pass


class ParentHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update):
        pass


class StudentHandler(ABC):
    @abstractmethod
    async def respond(self, request: object, update: data.Update):
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


class UserStart(UserHandler):
    async def respond(self, request: object, update: data.Update):
        text = 'Добро пожаловать! :) С помощью бота Вы всегда будете в курсе Вашего расписания, домашних ' \
               'заданий, сможете отменять и назначать занятия и многое другое! Для начала нужно пройти ' \
               'небольшую регистрацию (требуется лишь 1 раз).'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class StudentStart(StudentHandler):
    async def respond(self, request: object, update: data.Update):
        text = 'Добро пожаловать, студент! :) С помощью бота Вы всегда будете в курсе Вашего расписания, домашних ' \
               'заданий, сможете отменять и назначать занятия и многое другое! Для начала нужно пройти ' \
               'небольшую регистрацию (требуется лишь 1 раз).'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class ParentStart(ParentHandler):
    async def respond(self, request: object, update: data.Update):
        text = 'Добро пожаловать, родитель! :) С помощью бота Вы всегда будете в курсе Вашего расписания, домашних ' \
               'заданий, сможете отменять и назначать занятия и многое другое! Для начала нужно пройти ' \
               'небольшую регистрацию (требуется лишь 1 раз).'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class TutorStart(TutorHandler):
    async def respond(self, request: object, update: data.Update):
        text = 'Добро пожаловать, репетитор! :) С помощью бота Вы всегда будете в курсе Вашего расписания, домашних ' \
               'заданий, сможете отменять и назначать занятия и многое другое! Для начала нужно пройти ' \
               'небольшую регистрацию (требуется лишь 1 раз).'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class StartFactory(HandlerFactory):
    def create_tutor_handler(self) -> TutorStart:
        return TutorStart()

    def create_student_handler(self) -> StudentStart:
        return StudentStart()

    def create_parent_handler(self) -> ParentStart:
        return ParentStart()

    def create_user_handler(self) -> UserStart:
        return UserStart()
