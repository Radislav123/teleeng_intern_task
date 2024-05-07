from typing import Any, Iterable

import telebot
from telebot import types

import logger
from core import models as core_models
from telegram_bot import settings


Subscriptions = dict[int, tuple[str, str]]


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
        types.BotCommand("start", "Регистрация пользователя"),
        types.BotCommand("get_chat_id", "Возвращение идентификатора чата")
    ]

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
            link_preview_options: types.LinkPreviewOptions = None,
            **kwargs
    ) -> types.Message:
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
    ) -> types.Message:
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
    ) -> types.Message:
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

    def set_command_list(self) -> None:
        user_scope = types.BotCommandScopeAllPrivateChats()
        self.set_my_commands(self.commands, user_scope)

    def start_polling(self) -> None:
        self.register_handlers()
        self.set_command_list()

        self.logger.info("Telegram bot is running")
        self.infinity_polling(allowed_updates = telebot.util.update_types)

    @staticmethod
    def get_user(telegram_user: types.User) -> core_models.User | None:
        try:
            user = core_models.User.objects.get(telegram_user_id = telegram_user.id)
        except core_models.User.DoesNotExist:
            user = None
        return user

    def start(self, message: types.Message) -> None:
        try:
            user = core_models.User.objects.get(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id
            )
            text = ["Вы уже были зарегистрированы. Повторная регистрация невозможна."]
        except core_models.User.DoesNotExist:
            user = core_models.User(
                telegram_user_id = message.from_user.id,
                telegram_chat_id = message.chat.id
            )
            user.save()
            text = ["Вы были успешно зарегистрированы."]

        self.send_message(user.telegram_chat_id, text)

    def get_chat_id(self, message: types.Message) -> None:
        self.send_message(message.chat.id, self.Formatter.copyable(message.chat.id))
