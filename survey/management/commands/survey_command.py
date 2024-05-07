import abc

from core.management.commands import core_command
from survey import settings


class SurveyCommand(core_command.CoreCommand, abc.ABC):
    settings = settings.Settings()
