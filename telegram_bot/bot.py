from collections import defaultdict
from typing import Any, Iterable

import telebot

import logger
from core import models as core_models
from survey import models as survey_models
from telegram_bot import settings


class PrefetchedData:
    def __init__(self) -> None:
        self.QUIZZES_BY_ID: dict[int, survey_models.Quiz] = {x.id: x for x in survey_models.Quiz.objects.all()}

        self.QUESTIONS: dict[survey_models.Quiz, list[survey_models.Question]] = defaultdict(list)
        for question in survey_models.Question.objects.prefetch_related("quiz"):
            self.QUESTIONS[question.quiz].append(question)

        self.PREPARED_ANSWERS: dict[survey_models.Question, list[survey_models.PreparedAnswer]] = defaultdict(list)
        for prepared_answer in survey_models.PreparedAnswer.objects.prefetch_related("question", "question__quiz"):
            self.PREPARED_ANSWERS[prepared_answer.question].append(prepared_answer)

        self.PREPARED_ANSWERS_BY_ID: dict[int, survey_models.PreparedAnswer] = {
            y.id: y for x in self.PREPARED_ANSWERS.values() for y in x
        }


PREFETCHED_DATA = PrefetchedData()


class CallbackData:
    DELIMITER = ":"
    QUIZ = "q"
    PREPARED_ANSWER = "pa"

    def __init__(self) -> None:
        self.QUIZZES = {x: f"{self.QUIZ}{self.DELIMITER}{x}" for x in PREFETCHED_DATA.QUIZZES_BY_ID}
        self.PREPARED_ANSWERS = {}

        for question, prepared_answers in PREFETCHED_DATA.PREPARED_ANSWERS.items():
            for prepared_answer in prepared_answers:
                self.PREPARED_ANSWERS[prepared_answer.id] = (f"{self.PREPARED_ANSWER}{self.DELIMITER}"
                                                             f"{prepared_answer.id}")

    def get_quiz(self, callback_data: str) -> survey_models.Quiz:
        return PREFETCHED_DATA.QUIZZES_BY_ID[int(callback_data.split(self.DELIMITER)[1])]

    def get_prepared_answer(self, callback_data: str) -> survey_models.PreparedAnswer:
        return PREFETCHED_DATA.PREPARED_ANSWERS_BY_ID[int(callback_data.split(self.DELIMITER)[1])]

    def get_question_index(self, callback_data: str) -> int:
        return int(callback_data.split(self.DELIMITER)[2])


CALLBACK_DATA = CallbackData()


class BotTelegramException(Exception):
    pass


class NotEnoughEscapeWallsException(BotTelegramException):
    pass


class WrongNotificationTypeException(BotTelegramException):
    pass


class BotServiceMixin:
    class ParseMode:
        MARKDOWN = "MarkdownV2"

    class Formatter:
        ESCAPE_WALL = "|!&!|"

        @classmethod
        def wall(cls, data: Any) -> str:
            return f"{cls.ESCAPE_WALL}{data}{cls.ESCAPE_WALL}"

        @classmethod
        def remove_walls(cls, data: Any) -> str:
            if isinstance(data, str) and data.startswith(cls.ESCAPE_WALL) and data.endswith(cls.ESCAPE_WALL):
                string = "".join(data.split(cls.ESCAPE_WALL))
            else:
                string = str(data)
            return string

        @classmethod
        def copyable(cls, data: Any) -> str:
            return cls.wall(f"`{str(data)}`")

        @classmethod
        def underline(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.munderline(str(data)))

        @classmethod
        def bold(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mbold(str(data)))

        @classmethod
        def code(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mcode(str(data)))

        @classmethod
        def spoiler(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mspoiler(str(data)))

        @classmethod
        def strikethrough(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mstrikethrough(str(data)))

        @classmethod
        def italic(cls, data: Any) -> str:
            return cls.wall(telebot.formatting.mitalic(str(data)))

        @classmethod
        def link(cls, data: Any, link: str) -> str:
            return cls.wall(f"[{cls.wall(data)}]({link})")

        @classmethod
        def escape(cls, string: str) -> str:
            # текст между cls.ESCAPE_WALL не будет экранирован
            # "escaped text |wall| not escaped text |wall| more escaped text
            chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

            chunks = string.split(cls.ESCAPE_WALL)
            if len(chunks) % 2 == 0:
                raise NotEnoughEscapeWallsException()
            for number in range(len(chunks)):
                if number % 2 == 0:
                    for char in chars_to_escape:
                        chunks[number] = chunks[number].replace(char, '\\' + char)
            return "".join(chunks)

        @staticmethod
        def changes_repr(new: int | float, old: int | float) -> str:
            changing = new - old
            if changing > 0:
                sign = '+'
            else:
                sign = ''
            return f"{sign}{changing}"

        @classmethod
        def join(cls, text: Iterable[str]) -> str:
            return "\n".join([cls.escape(string) for string in text])

    settings = settings.Settings()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logger.Logger(self.settings.APP_NAME)


class Bot(BotServiceMixin, telebot.TeleBot):
    commands = [
        telebot.types.BotCommand("start", "Регистрация пользователя"),
        telebot.types.BotCommand("get_chat_id", "Возвращение идентификатора чата"),
        telebot.types.BotCommand("quiz", "Выбор опроса")
    ]
    _users: dict[int, core_models.User] = {}

    def __init__(self, token: str = None):
        if token is None:
            token = self.settings.secrets.telegram_bot.token

        super().__init__(token)
        self.enable_saving_states()

    def send_message(
            self,
            chat_id: int | str,
            text: Iterable[str] | str,
            parse_mode: str = None,
            reply_markup: telebot.REPLY_MARKUP_TYPES = None,
            link_preview_options: telebot.types.LinkPreviewOptions = None,
            **kwargs
    ) -> telebot.types.Message:
        if isinstance(text, str):
            text = [text]
        if parse_mode is None:
            parse_mode = self.ParseMode.MARKDOWN

        text_chunks = telebot.util.smart_split(self.Formatter.join(text))
        for text_chunk in text_chunks:
            return super().send_message(
                chat_id,
                text_chunk,
                parse_mode,
                reply_markup = reply_markup,
                link_preview_options = link_preview_options,
                **kwargs
            )

    def send_photo(
            self,
            chat_id: int | str,
            photo_or_id: Any | str,
            text: Iterable[str] | str = None,
            parse_mode: str = None,
            reply_markup: telebot.REPLY_MARKUP_TYPES = None,
            **kwargs
    ) -> telebot.types.Message:
        if isinstance(text, str):
            text = [text]
        if parse_mode is None:
            parse_mode = self.ParseMode.MARKDOWN

        return super().send_photo(
            chat_id,
            photo_or_id,
            self.Formatter.join(text) if text is not None else text,
            parse_mode,
            reply_markup = reply_markup,
            **kwargs
        )

    def send_document(
            self,
            chat_id: int | str,
            document_or_id: Any | str,
            text: Iterable[str] | str = None,
            parse_mode: str = None,
            reply_markup: telebot.REPLY_MARKUP_TYPES = None,
            **kwargs
    ) -> telebot.types.Message:
        if isinstance(text, str):
            text = [text]
        if parse_mode is None:
            parse_mode = self.ParseMode.MARKDOWN

        return super().send_document(
            chat_id,
            document_or_id,
            caption = self.Formatter.join(text) if text is not None else text,
            parse_mode = parse_mode,
            reply_markup = reply_markup,
            **kwargs
        )

    copy_message = telebot.TeleBot.copy_message

    def register_handlers(self) -> None:
        for bot_command in self.commands:
            self.message_handler(commands = [bot_command.command])(getattr(self, bot_command.command))

        self.callback_query_handler(lambda callback: callback.data.startswith(CALLBACK_DATA.QUIZ))(
            self.start_quiz
        )
        self.callback_query_handler(lambda callback: callback.data.startswith(CALLBACK_DATA.PREPARED_ANSWER))(
            self.retrieve_prepared_answer
        )

    def set_command_list(self) -> None:
        user_scope = telebot.types.BotCommandScopeAllPrivateChats()
        self.set_my_commands(self.commands, user_scope)

    def start_polling(self) -> None:
        self.register_handlers()
        self.set_command_list()

        self.logger.info("Telegram bot is running")
        self.infinity_polling(allowed_updates = telebot.util.update_types)

    @classmethod
    def get_user(cls, telegram_user: telebot.types.User) -> core_models.User:
        if telegram_user.id not in cls._users:
            cls._users[telegram_user.id] = core_models.User.objects.get(telegram_user_id = telegram_user.id)
        return cls._users[telegram_user.id]

    def start(self, message: telebot.types.Message) -> None:
        try:
            user = self.get_user(message.from_user)
            text = ["Вы уже были зарегистрированы. Повторная регистрация невозможна."]
        except core_models.User.DoesNotExist:
            user = core_models.User(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id
            )
            user.save()
            self._users[user.telegram_user_id] = user
            text = ["Вы были успешно зарегистрированы."]

        self.send_message(user.telegram_chat_id, text)

    def get_chat_id(self, message: telebot.types.Message) -> None:
        self.send_message(message.chat.id, self.Formatter.copyable(message.chat.id))

    def quiz(self, message: telebot.types.Message) -> None:
        user = self.get_user(message.from_user)

        keyboard = [[telebot.types.InlineKeyboardButton(
            value.name,
            callback_data = CALLBACK_DATA.QUIZZES[key]
        )] for key, value in PREFETCHED_DATA.QUIZZES_BY_ID.items()]
        reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
        self.send_message(
            user.telegram_chat_id,
            "Выберите опрос из предложенных.",
            reply_markup = reply_markup
        )

    def start_quiz(self, callback: telebot.types.CallbackQuery) -> None:
        user = self.get_user(callback.from_user)
        quiz = CALLBACK_DATA.get_quiz(callback.data)
        quiz_old_answers = survey_models.Answer.objects.filter(
            user = user,
            question__quiz = quiz
        )
        quiz_old_answers.delete()

        self.delete_message(
            user.telegram_chat_id,
            callback.message.id
        )
        self.send_message(
            user.telegram_chat_id,
            quiz.name
        )

        self.ask_question(user, quiz, 0)

    def ask_question(
            self,
            user: core_models.User,
            quiz: survey_models.Quiz,
            question_index
    ) -> None:
        next_questions = PREFETCHED_DATA.QUESTIONS[quiz][question_index:]
        if len(next_questions) == 0:
            self.end_quiz(user, quiz)
        else:
            question = next_questions[0]
            if question in PREFETCHED_DATA.PREPARED_ANSWERS:
                keyboard = [[telebot.types.InlineKeyboardButton(
                    x.text,
                    callback_data = f"{CALLBACK_DATA.PREPARED_ANSWERS[x.id]}{CALLBACK_DATA.DELIMITER}{question_index}"
                )] for x in PREFETCHED_DATA.PREPARED_ANSWERS[question]]
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                self.send_message(
                    user.telegram_chat_id,
                    [next_questions[0].text, "Выберите ответ."],
                    reply_markup = reply_markup
                )
            else:
                question_message = self.send_message(
                    user.telegram_chat_id,
                    [next_questions[0].text, "Введите ответ."],
                )
                self.register_next_step_handler_by_chat_id(
                    user.telegram_chat_id,
                    self.retrieve_text_answer,
                    user,
                    question,
                    question_message,
                    question_index
                )

    def retrieve_prepared_answer(self, callback: telebot.types.CallbackQuery) -> None:
        user = self.get_user(callback.from_user)
        prepared_answer = CALLBACK_DATA.get_prepared_answer(callback.data)
        question_index = CALLBACK_DATA.get_question_index(callback.data)

        self.delete_message(
            user.telegram_chat_id,
            callback.message.id
        )

        answer = survey_models.Answer(
            user = user,
            question = prepared_answer.question,
            prepared_answer = prepared_answer
        )
        answer.save()
        self.ask_question(user, prepared_answer.question.quiz, question_index + 1)

    def retrieve_text_answer(
            self,
            message: telebot.types.Message,
            user: core_models.User,
            question: survey_models.Question,
            question_message: telebot.types.Message,
            question_index: int
    ) -> None:
        self.delete_message(
            user.telegram_chat_id,
            question_message.id
        )
        self.delete_message(
            user.telegram_chat_id,
            message.id
        )

        answer = survey_models.Answer(
            user = user,
            question = question,
            message_id = message.id
        )
        answer.save()
        self.ask_question(user, question.quiz, question_index + 1)

    def end_quiz(self, user: core_models.User, quiz: survey_models.Quiz) -> None:
        self.send_message(
            user.telegram_chat_id,
            f"Спасибо, что прошли опрос {quiz}."
        )
