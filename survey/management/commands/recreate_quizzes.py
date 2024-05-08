import json

from survey import models
from survey.management.commands import survey_command


class Command(survey_command.SurveyCommand):
    help = "Заполняет БД опросами, удаляя старые"

    def handle(self, *args, **options) -> None:
        self.delete_old()
        self.create_new()

    def delete_old(self) -> None:
        old_quizzes = models.Quiz.objects.all()
        old_quizzes_count = len(models.Quiz.objects.all())
        old_quizzes.delete()
        self.logger.info(f"Deleted old quizzes: {old_quizzes_count}")

    def create_new(self) -> None:
        with open(self.settings.QUIZZES_PATH, 'r', encoding = "utf-8") as file:
            quizzes_json = json.load(file)

        quizzes = []
        questions = []
        prepared_answers = []
        for quiz_json in quizzes_json:
            quiz = models.Quiz(
                name = quiz_json["name"]
            )
            quizzes.append(quiz)
            for question_json in quiz_json["questions"]:
                question = models.Question(
                    quiz = quiz,
                    value = question_json["value"]
                )
                questions.append(question)
                if "prepared_answers" in question_json:
                    question_prepared_answers = [models.PreparedAnswer(
                        question = question,
                        value = value
                    ) for value in question_json["prepared_answers"]]
                    prepared_answers.extend(question_prepared_answers)

        models.Quiz.objects.bulk_create(quizzes)
        models.Question.objects.bulk_create(questions)
        models.PreparedAnswer.objects.bulk_create(prepared_answers)
        self.logger.info(f"Created new quizzes: {len(quizzes)}")
        self.logger.info(f"Created new questions: {len(questions)}")
        self.logger.info(f"Created new prepared answers: {len(prepared_answers)}")
