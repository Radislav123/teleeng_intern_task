import logging

from core.apps import CoreConfig
from secret_keeper import SecretKeeper


class Settings:
    APP_NAME = CoreConfig.name

    def __init__(self) -> None:
        # Пути секретов
        self.SECRETS_FOLDER = "secrets"

        self.DATABASE_SECRETS_FOLDER = f"{self.SECRETS_FOLDER}/database"
        self.DATABASE_CREDENTIALS_PATH = f"{self.DATABASE_SECRETS_FOLDER}/credentials.json"

        self.TELEGRAM_BOT_SECRETS_FOLDER = f"{self.SECRETS_FOLDER}/telegram_bot"
        self.TELEGRAM_BOT_CREDENTIALS_PATH = f"{self.TELEGRAM_BOT_SECRETS_FOLDER}/credentials.json"

        self.ADMIN_PANEL_SECRETS_FOLDER = f"{self.SECRETS_FOLDER}/admin_panel"
        self.DJANGO_CREDENTIALS_PATH = f"{self.ADMIN_PANEL_SECRETS_FOLDER}/django.json"

        # Настройки логгера
        self.LOG_FORMAT = "[%(asctime)s] - [%(levelname)s] - %(name)s -" \
                          " (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
        self.LOG_FOLDER = "logs"
        self.CONSOLE_LOG_LEVEL = logging.DEBUG
        self.FILE_LOG_LEVEL = logging.DEBUG

        self.secrets = SecretKeeper(self)
