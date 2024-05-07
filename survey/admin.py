from core import admin as core_admin
from survey import models as survey_models
from survey.settings import Settings


class SurveyAdmin(core_admin.CoreAdmin):
    model = survey_models.SurveyModel
    settings = Settings()


class QuizAdmin(SurveyAdmin):
    model = survey_models.Quiz


class QuestionAdmin(SurveyAdmin):
    model = survey_models.Question


class PreparedQuestionAdmin(SurveyAdmin):
    model = survey_models.PreparedAnswer


class AnswerAdmin(SurveyAdmin):
    model = survey_models.Answer


model_admins_to_register = [QuizAdmin, QuestionAdmin, PreparedQuestionAdmin, AnswerAdmin]
core_admin.register_models(model_admins_to_register)
