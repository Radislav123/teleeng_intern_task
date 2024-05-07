from django.contrib.auth import models as auth_models
from django.db import models

from core.settings import Settings
from logger import Logger


class CoreModel(models.Model):
    class Meta:
        abstract = True

    settings = Settings()
    logger = Logger(Meta.__qualname__[:-5])

    @classmethod
    def get_field_verbose_name(cls, field_name: str) -> str:
        return cls._meta.get_field(field_name).verbose_name


class User(CoreModel, auth_models.AbstractUser):
    telegram_user_id = models.BigIntegerField("Telegram user_id", null = True)
    telegram_chat_id = models.BigIntegerField("Telegram chat_id", null = True)

    def get_default_username(self) -> str:
        return f"user_{self.id}"

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if self.username == "" or self.username is None:
            self.username = self.get_default_username()
        # для сохранения username с выданным id (не None)
        super().save()
