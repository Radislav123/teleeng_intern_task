from django.db import models

from core import models as core_models


class SurveyModel(core_models.CoreModel):
    class Meta:
        abstract = True


class Quiz(SurveyModel):
    class Meta:
        verbose_name_plural = "Quizzes"


class Question(SurveyModel):
    quiz = models.ForeignKey(Quiz, models.CASCADE)
    value = models.CharField(max_length = 100)


class PreparedAnswer(SurveyModel):
    question = models.ForeignKey(Question, models.CASCADE)
    value = models.CharField(max_length = 100)


class Answer(SurveyModel):
    user = models.ForeignKey(core_models.User, models.CASCADE)
    question = models.ForeignKey(Question, models.CASCADE)
    # https://core.telegram.org/constructor/message
    message_id = models.IntegerField(null = True)
    prepared_answer = models.ForeignKey(PreparedAnswer, models.CASCADE, null = True)
