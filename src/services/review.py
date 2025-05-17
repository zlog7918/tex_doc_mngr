from . import article as aq
from sqlalchemy import and_, desc
from models.utils import utils as util
from models.article.Round import Round
from datetime import datetime, timedelta
from db.db_base import db, log_err, log_activity
from models.utils.MessageException import MessageException
from models.article.Article import Article, ArticleStatusEnum
from models.article.Review import Review, ReviewStatus, ReviewStatusEnum
from models.article.Questions import QuestionSet, Answer, Question, QuestionA, QuestionSetQuestions

def get_review_by_id(review_id: int) -> Review|None:
    return Review.query.where(Review.id==review_id).first()

def __get_review_status_or_err(review_status: ReviewStatusEnum) -> ReviewStatus:
    r = ReviewStatus.query.where(ReviewStatus.stat==review_status).first()
    if r is None:
        raise ValueError(f'Review status {review_status.value} not found')
    return r

def get_review(article_id: int, reviewer_id: int) -> Review|None:
    try:
        review = (
            db.session.query(Review)
            .join(Round, Review.round_id == Round.id)
            .where(and_(Round.article_id == article_id, Review.reviewer_id == reviewer_id))
            .order_by(desc(Round.round_number))
            .first()
        )

        return review

    except Exception as e:
        return None


def check_reviews_and_update_article_status(review_id: int) -> None:
    round_id = (
        db.session.query(Review.round_id)
        .filter(Review.id == review_id)
        .scalar()
    )

    if round_id is None:
        return

    statuses = (
        db.session.query(ReviewStatus.stat)
        .join(Review, Review.status_id == ReviewStatus.id)
        .where(Review.round_id == round_id)
        .all()
    )

    all_reviewed = all(status[0] == ReviewStatusEnum.Reviewed for status in statuses)

    if all_reviewed:
        article: Article = (
            db.session.query(Article)
            .join(Round, Round.article_id == Article.id)
            .where(Round.id == round_id)
            .scalar()
        )
        if article:
            aq.update_article_status(article, ArticleStatusEnum.Reviewed)
        else:
            raise MessageException(f'Article with round id {round_id} not found.')


def get_articles_as_reviewer(reviewer_id: int) -> list[tuple[Article, ReviewStatusEnum]]:
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
    return [row.tuple() for row in articles]


def post_review(review: Review) -> bool:
    try:
        # Dodajemy nową recenzję do bazy danych
        db.session.add(review)
        db.session.flush()
        return True
    except Exception as e:
        log_err(e)
        return False


def update_review_status(review_id: int, status: ReviewStatusEnum) -> bool:
    try:
        review = get_review_by_id(review_id)
        if review is None:
            log_activity(False, {'err': f'Review with id: {review_id} not found'})
            return False

        if review.status.stat in (ReviewStatusEnum.Reviewed, ReviewStatusEnum.NotReviewed, ReviewStatusEnum.RejectedByReviewer) or aq.is_article_rejected(review.round.article_id):
            log_activity(False, {'err': f'Attempt to access review: {review_id} which should be unavailable'})
            return False

        review.update_status(__get_review_status_or_err(status))
        db.session.flush()
        return True
    except Exception as err:
        raise MessageException.from_exception(err, 'Review status not updated') from None



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
                    .join(QuestionA, QuestionA.question_id == Answer.question_id)
                    .filter(QuestionA.question_id == question.id)
                    .scalars()
                    .all()
                )
                question_data["answers"] = [{"id": ans.id, "answer": ans.answer} for ans in answers]

            result.append(question_data)

        return result

    except Exception as e:
        log_err(e)
        return []


def save_review_answers(review_id: int, answers: dict[int, str]) -> None:
    for question_id, answer in answers.items():
        new_answer = Answer(**util.get_kwargs_for(Answer, {
            Answer.review_id: review_id,
            Answer.question_id: question_id,
            Answer.answer: answer,
        }))
        db.session.add(new_answer)
        db.session.flush()

    update_review_status(review_id, ReviewStatusEnum.Reviewed)    # TODO: rollback answer submitting when exception here
    db.session.flush()


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
        log_err(e)
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
        log_err(e)
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

        review_status = __get_review_status_or_err(ReviewStatusEnum.Expired)
        for review in reviews:
            print(f'Zmieniono status review {review.id} na \'{ReviewStatusEnum.Expired}\'')
            log_activity(True, {'details': f'Zmieniono status review {review.id} na \'Expired\''})
            review.status_id = review_status.id

        db.session.commit()
        return True
    except Exception as e:
        log_err(e)
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

        review_status = __get_review_status_or_err(ReviewStatusEnum.NotReviewed)
        for review in reviews:
            print(f'Zmieniono status review {review.id} na \'{ReviewStatusEnum.NotReviewed}\'')
            log_activity(True, {'details': f'Zmieniono status review {review.id} na \'Not Reviewed\''})
            review.status_id = review_status.id

        db.session.commit()
        return True
    except Exception as e:
        log_err(e)
        return False
