from sqlalchemy import select
from db.db_base import db, log_err
from models.utils.utils import get_function
from . import article as aq
from models.article.Round import Round
from models.article.Review import Review
from models.article.Article import Article
from models.article.Questions import QuestionSet, Answer, Question, QuestionA, QuestionSetQuestions

def get_review_by_id(review_id: int) -> Review|None:
    return Review.query.where(Review.id==review_id).first()

def get_review(article_id: int, reviewer_id: int) -> Review|None:
    try:
        review = (
            db.session.query(Review)
            .join(Round, Review.round_id == Round.id)
            .filter(Round.article_id == article_id, Review.reviewer_id == reviewer_id)
            .first()
        )

        return review

    except Exception as err:
        print("error get_review: " + str(err))
        return None


def get_assigned_reviews(article_id: int) -> list[dict[int, str]]:
    try:
        # Pobieramy identyfikator najnowszej rundy dla danego artykułu
        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .subquery()
        )

        # Pobieramy przypisane recenzje dla danej rundy
        reviews = (
            db.session.query(Review)
            .filter(Review.round_id.in_(select(latest_round_subquery)))
            .all()
        )

        # Konwersja wyników na listę obiektów Review
        return [{"review_id": review.id, "reviewer_id": review.reviewer_id} for review in reviews]

    except Exception as err:
        print("error6: " + str(err))
        return []


def check_reviews_and_update_article_status(review_id: int) -> None:
    try:
        round_id = (
            db.session.query(Review.round_id)
            .filter(Review.id == review_id)
            .scalar()
        )

        if round_id is None:
            return

        statuses = (
            db.session.query(Review.status)
            .filter(Review.round_id == round_id)
            .all()
        )

        all_reviewed = all(status[0] == 'Reviewed' for status in statuses)

        if all_reviewed:
            article_id = (
                db.session.query(Round.article_id)
                .filter(Round.id == round_id)
                .scalar()
            )
            if article_id:
                aq.update_article_status(article_id, 4)

    except Exception as err:
        print("exception:", str(err))
        # self.__log_activity(
        #     inspect.currentframe().f_code.co_name,
        #     False,
            # {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
        # )


def get_articles_as_reviewer(reviewer_id: int) -> list[Article, int]:
    try:
        articles = (
            db.session.query(Article, Review.status)
            .join(Round, Round.article_id == Article.id)
            .join(Review, Review.round_id == Round.id)
            .filter(Review.reviewer_id == reviewer_id, Review.status.in_(['Pending confirmation', 'Accepted by reviewer']))
            .all()
        )

        # Konwersja do listy słowników
        return articles

    except Exception as err:
        print("error7: " + str(err))
        return []


def post_review(review: Review) -> bool:
    try:
        # Dodajemy nową recenzję do bazy danych
        db.session.add(review)
        db.session.commit()
        return True
    except Exception as err:
        print("error8: " + str(err))
        db.session.rollback()
        return False


def update_review_status(review_id: int, status: str) -> bool:
    try:
        review = get_review_by_id(review_id)
        if review:
            review.status = status
            db.session.commit()
            return True
        return False
    except Exception as err:
        log_err(get_function(), err)
        db.session.rollback()
        return False



def get_questions_with_answers(q_set_id: int) -> list[dict[int, str]]:
    try:
        questions = (
            db.session.query(Question)
            .join(QuestionSetQuestions, QuestionSetQuestions.question_id == Question.id)
            .filter(QuestionSetQuestions.question_set_id == q_set_id)
            .all()
        )

        result = []
        for question in questions:
            question_data = {
                "id": question.id,
                "text": question.question,
                "is_abc": question.is_abc,
                "answers": []
            }
            if question.is_abc:
                answers = (
                    db.session.query(Answer)
                    .join(QuestionA, Question.question_id == Answer.question_id)
                    .filter(QuestionA.question_id == question.id)
                    .scalars()
                    .all()
                )
                question_data["answers"] = [{"id": ans.id, "answer": ans.answer} for ans in answers]

            result.append(question_data)

        return result

    except Exception as err:
        print("error9: " + str(err))
        return []


def save_review_answers(review_id: int, answers: dict[int, str]) -> bool:
    try:
        for question_id, answer in answers.items():
            new_answer = Answer(review_id=review_id, question_id=question_id, answer=answer)
            db.session.add(new_answer)

        update_review_status(review_id=review_id, status='Reviewed')    # TODO: rollback answer submitting when exception here
        db.session.commit()
        return True
    except Exception as err:
        print("error10: " + str(err))
        db.session.rollback()
        return False


def get_questions_by_article(article_id: int) -> list[dict[str, str]]|None:
    # TODO: finish this
    try:
        questions = (
            db.session.query(Question)
            .join(QuestionSetQuestions, Question.id == QuestionSetQuestions.question_id)
            .join(QuestionSet, QuestionSetQuestions.question_set_id == QuestionSet.id)
            .all()
        )

        return [{"id": q.id, "text": q.question, "is_abc": q.is_abc} for q in questions]

    except Exception as err:
        print(f"Error fetching questions: {err}")
        return None


def get_question_answers(question_id: int) -> list[dict[int, str]]:
    try:
        answers = (
            db.session.query(QuestionA)
            .filter(QuestionA.question_id == question_id)
            .all()
        )

        return [{"id": ans.id, "answer": ans.answer} for ans in answers]

    except Exception as err:
        print(f"Error fetching answers: {err}")
        return []