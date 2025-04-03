from sqlalchemy import and_, desc
from . import article as aq
from models.utils import utils as util
from models.article.Round import Round
from models.article.Review import Review
from models.article.Article import Article
from db.db_base import db, log_err, log_activity
from models.utils.MessageException import MessageException
from models.article.Article import Article, ArticleStatusEnum
from models.article.Questions import QuestionSet, Answer, Question, QuestionA, QuestionSetQuestions

def get_review_by_id(review_id: int) -> Review|None:
    return Review.query.where(Review.id==review_id).first()

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
        db.session.query(Review.status)
        .where(Review.round_id == round_id)
        .scalar()
        .all()
    )

    all_reviewed = all(status == 'Reviewed' for status in statuses)

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



def get_articles_as_reviewer(reviewer_id: int) -> list[tuple[Article, str]]:
    articles = (
        db.session.query(Article, Review.status)
        .join(Round, Round.article_id == Article.id)
        .join(Review, Review.round_id == Round.id)
        .filter(Review.reviewer_id == reviewer_id, Review.status.in_(['Pending confirmation', 'Accepted by reviewer']))
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


def update_review_status(review_id: int, status: str) -> bool:
    try:
        review = get_review_by_id(review_id)
        if review is None:
            log_activity(False, {'err': f'Review with id: {review_id} not found'})
            return False
        review.status=status
        db.session.flush()
        return True
    except Exception as err:
        raise MessageException('Review status not updated', err) from None



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
        log_err(e)
        return []


def save_review_answers(review_id: int, answers: dict[int, str]) -> bool:
    try:
        for question_id, answer in answers.items():
            new_answer = Answer(**util.get_kwargs_for(Answer, {
                Answer.review_id: review_id,
                Answer.question_id: question_id,
                Answer.answer: answer,
            }))
            db.session.add(new_answer)
            db.session.flush()
            db.session.flush()

        update_review_status(review_id=review_id, status='Reviewed')
        return True
    except Exception as e:
        log_err(e)
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