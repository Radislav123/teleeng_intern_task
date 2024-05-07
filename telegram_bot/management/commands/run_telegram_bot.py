from telegram_bot.bot import Bot
from telegram_bot.management.commands import telegram_bot_command


class Command(telegram_bot_command.TelegramBotCommand):
    help = "Запускает бота"

    def handle(self, *args, **options):
        bot = Bot()
        bot.start_polling()
