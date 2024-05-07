from core import settings
from telegram_bot.apps import TelegramBotConfig


class Settings(settings.Settings):
    APP_NAME = TelegramBotConfig.name
