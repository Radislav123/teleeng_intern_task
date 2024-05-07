import json

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.settings import Settings


class SecretKeeper:
    class Module:
        name: str
        secrets_path: str
        json: dict
        secret_keeper: "SecretKeeper"

        def get_dict(self) -> dict:
            return self.json

    class Database(Module):
        ENGINE: str
        NAME: str
        USER: str
        PASSWORD: str
        HOST: str
        PORT: str

    class TelegramBot(Module):
        token: str

    class Django(Module):
        secret_key: str

    class User(Module):
        username: str
        email: str
        password: str
        subscribed: str

    database: Database
    telegram_bot: TelegramBot
    django: Django
    admin_user: User

    def __init__(self, settings: "Settings") -> None:
        self.add_module("database", settings.DATABASE_CREDENTIALS_PATH)
        self.add_module("telegram_bot", settings.TELEGRAM_BOT_CREDENTIALS_PATH)
        self.add_module("django", settings.DJANGO_CREDENTIALS_PATH)
        self.add_module("admin_user", settings.ADMIN_USER_CREDENTIALS_PATH)

    @staticmethod
    def read_json(path: str) -> dict:
        with open(path, 'r') as file:
            data = json.load(file)
        return data

    def add_module(self, name: str, secrets_path: str) -> None:
        json_dict = self.read_json(secrets_path)
        module = type(name, (self.Module,), json_dict)()
        module.name = name
        module.secrets_path = secrets_path
        module.json = json_dict
        module.secret_keeper = self
        setattr(self, name, module)
