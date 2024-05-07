from core import settings
from survey.apps import SurveyConfig


class Settings(settings.Settings):
    APP_NAME = SurveyConfig.name
