from django.contrib.auth import get_user_model

from core.management.commands import core_command
from secret_keeper import SecretKeeper


class Command(core_command.CoreCommand):
    help = "Создает специальных пользователей"

    def handle(self, *args, **options) -> None:
        users = (
            self.settings.secrets.admin_user,
        )
        for user in users:
            self.create(user)

    def create(self, user: SecretKeeper.User) -> None:
        user_model = get_user_model()
        if not user_model.objects.filter(username = user.username).exists():
            user_model.objects.create_superuser(**user.get_dict())
            self.logger.info(f"The {user.username} was created.")
        else:
            self.logger.info(f"The {user.username} already exists.")
