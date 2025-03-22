from datetime import datetime, timedelta
from db.db_base import db, log_activity, log_err
from models.article import Article
from models.utils.utils import get_function
from . import article as aq
from models.article.Round import Round
from models.article.Review import Review, ReviewStatus, ReviewStatusEnum
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

    except Exception as e:
        log_err(get_function(), e)
        return None


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
            db.session.query(ReviewStatus.stat)
            .filter(Review.round_id == round_id)
            .all()
        )

        all_reviewed = all(status[0] == ReviewStatusEnum.Reviewed for status in statuses)

        if all_reviewed:
            article_id = (
                db.session.query(Round.article_id)
                .filter(Round.id == round_id)
                .scalar()
            )
            if article_id:
                aq.update_article_status(article_id, 4)

    except Exception as e:
        log_err(get_function(), e)


def get_articles_as_reviewer(reviewer_id: int) -> list[tuple[Article, str]]:
    try:
        articles = (
            db.session.query(Article, ReviewStatus.stat)
            .join(Round, Round.article_id == Article.id)
            .join(Review, Review.round_id == Round.id)
            .join(ReviewStatus, Review.status_id == ReviewStatus.id)
            .filter(Review.reviewer_id == reviewer_id, ReviewStatus.stat.in_([
                ReviewStatusEnum.PendingConfirmation,
                ReviewStatusEnum.AcceptedByReviewer
                ])
            )
            .all()
        )

        return [(row[0], row[1]) for row in articles]


    except Exception as e:
        log_err(get_function(), e)
        return []


def post_review(review: Review) -> bool:
    try:
        # Dodajemy nową recenzję do bazy danych
        db.session.add(review)
        db.session.commit()
        return True
    except Exception as e:
        log_err(get_function(), e)
        return False


def update_review_status(review_id: int, status: ReviewStatusEnum) -> bool:
    try:
        review = get_review_by_id(review_id)
        if review:
            result = review.update_status(new_status=status)
            if result:
                db.session.commit()
                return True
            else:
                return False
        log_activity(get_function(), False, {'err': f'Review with id: {review_id} not found'})
        return False
    except Exception as e:
        log_err(get_function(), e)
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

    except Exception as e:
        log_err(get_function(), e)
        return []


def save_review_answers(review_id: int, answers: dict[int, str]) -> bool:
    try:
        for question_id, answer in answers.items():
            new_answer = Answer(review_id=review_id, question_id=question_id, answer=answer)
            db.session.add(new_answer)

        update_review_status(review_id=review_id, status=4)    # TODO: rollback answer submitting when exception here
        db.session.commit()
        return True
    except Exception as e:
        log_err(get_function(), e)
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

    except Exception as e:
        log_err(get_function(), e)
        return None


def get_question_answers(question_id: int) -> list[dict[int, str]]:
    try:
        answers = (
            db.session.query(QuestionA)
            .filter(QuestionA.question_id == question_id)
            .all()
        )

        return [{"id": ans.id, "answer": ans.answer} for ans in answers]

    except Exception as e:
        log_err(get_function(), e)
        return []
    
def set_expired_status_for_reviews() -> bool:
    try:
        now = datetime.now()
        yesterday_end = datetime(now.year, now.month, now.day) - timedelta(seconds=1)
        reviews = (
            db.session.query(Review)
            .join(Round, Round.id == Review.round_id)
            .join(ReviewStatus, ReviewStatus.id == Review.status_id)
            .where(ReviewStatus.stat == ReviewStatusEnum.PendingConfirmation)
            .where(Round.deadline_confirm <= yesterday_end)
            .all()
        )

        for review in reviews:
            print(f'Zmieniono status review {review.id} na \'{ReviewStatusEnum.Expired}\'')
            log_activity(get_function(), True, {'details': f'Zmieniono status review {review.id} na \'Expired\''})
            review.status.stat = ReviewStatusEnum.Expired

        db.session.commit()
        return True
    except Exception as e:
        log_err(get_function(), e)
        return False
    
def set_not_reviewed_status_for_reviews() -> bool:
    try:
        now = datetime.now()
        yesterday_end = datetime(now.year, now.month, now.day) - timedelta(seconds=1)
        reviews = (
            db.session.query(Review)
            .join(Round, Round.id == Review.round_id)
            .join(ReviewStatus, ReviewStatus.id == Review.status_id)
            .where(ReviewStatus.stat == ReviewStatusEnum.AcceptedByReviewer)
            .where(Round.deadline_confirm <= yesterday_end)
            .all()
        )

        for review in reviews:
            print(f'Zmieniono status review {review.id} na \'{ReviewStatusEnum.NotReviewed}\'')
            log_activity(get_function(), True, {'details': f'Zmieniono status review {review.id} na \'Not Reviewed\''})
            review.status.stat = ReviewStatusEnum.NotReviewed

        db.session.commit()
        return True
    except Exception as e:
        log_err(get_function(), e)
        return False
