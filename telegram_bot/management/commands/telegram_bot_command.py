import abc

from core.management.commands import core_command
from telegram_bot import settings


class TelegramBotCommand(core_command.CoreCommand, abc.ABC):
    settings = settings.Settings()
