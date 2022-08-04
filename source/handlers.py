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
        menu = StudentHelp()
        await menu.respond(request, update)


class ParentStart(ParentHandler):
    async def respond(self, request: object, update: data.Update):
        menu = ParentHelp()
        await menu.respond(request, update)


class TutorStart(TutorHandler):
    async def respond(self, request: object, update: data.Update):
        menu = TutorHelp()
        await menu.respond(request, update)


class StartFactory(HandlerFactory):
    def create_tutor_handler(self) -> TutorStart:
        return TutorStart()

    def create_student_handler(self) -> StudentStart:
        return StudentStart()

    def create_parent_handler(self) -> ParentStart:
        return ParentStart()

    def create_user_handler(self) -> UserStart:
        return UserStart()


class UserHelp(UserHandler):
    async def respond(self, request: object, update: data.Update):
        text = 'Выберите действие:'
        keyboard = view.InlineKeyboardMarkup()
        keyboard.add_button(view.InlineKeyboardButton('Начать регистрацию', '/register'))
        data_to_send = data.Text(text)
        response = view.SendMessage(request.app['config'], update.user.chat_id, data_to_send, keyboard)
        await response.send()


class StudentHelp(StudentHandler):
    async def respond(self, request: object, update: data.Update):
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
    async def respond(self, request: object, update: data.Update):
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
    async def respond(self, request: object, update: data.Update):
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
    def create_tutor_handler(self) -> TutorStart:
        return TutorHelp()

    def create_student_handler(self) -> StudentStart:
        return StudentHelp()

    def create_parent_handler(self) -> ParentStart:
        return ParentHelp()

    def create_user_handler(self) -> UserStart:
        return UserHelp()
