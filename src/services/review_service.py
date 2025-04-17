from sqlalchemy import and_, select
from . import article_service as aq
from models.utils import utils as util
from models.article.Round import Round
from models.article.Review import Review
from models.article import Questions as Q
from db.db_base import db, log_err, log_activity
from models.utils.MessageException import MessageException
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum

def get_review_by_id(review_id: int) -> Review|None:
    return Review.query.where(Review.id==review_id).first()

def get_review(article_id: int, reviewer_id: int) -> Review|None:
    try:
        review = (
            db.session.query(Review)
            .join(Round, Review.round_id == Round.id)
            .where(and_(Round.article_id == article_id, Review.reviewer_id == reviewer_id))
            .order_by(Round.round_number.desc())
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
        .all()
    )

    all_reviewed = all(status[0] == 'Reviewed' for status in statuses)

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
        .join(ArticleStatus, ArticleStatus.id == Article.status_id)
        .where(and_(
            Review.reviewer_id == reviewer_id,
            Review.status.in_(['Pending confirmation', 'Accepted by reviewer']),
            ArticleStatus.stat != ArticleStatusEnum.Rejected
        ))
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
        if review.status in ("Reviewed", "Not reviewed", "Rejected by reviewer") or aq.is_article_rejected(review.round.article_id):
            log_activity(False, {'err': f'Attempt to access review: {review_id} which should be unavailable'})
            return False
        
        review.status=status
        db.session.flush()
        return True
    except Exception as err:
        raise MessageException('Review status not updated', err) from None


# def get_questions_with_answers(review: Review) -> list[dict[int, str]]:
#     try:
#         q_set_id=review.round.q_set_id
#         # TODO: modify question set join
#         questions = (
#             db.session.query(Q.Question)
#             .join(Q.QuestionGroupQuestions, Q.QuestionGroupQuestions.question_id == Q.Question.id)
#             .join(Q.QuestionSetGroups, Q.QuestionSetGroups.question_group_id == Q.QuestionGroupQuestions.question_group_id)
#             .where(Q.QuestionSetGroups.question_set_id == q_set_id)
#             .all()
#         )

#         result = []
#         for question in questions:
#             question_data = {
#                 "id": question.id,
#                 "text": question.question,
#                 "is_abc": question.is_abc,
#                 "answers": []
#             }
#             if question.is_abc:
#                 # Should it be Answer of reviewer or possible answer (QuestionA)?
#                 answers = (
#                     db.session.query(Q.Answer)
#                     .join(Q.QuestionA, Q.Question.id == Q.Answer.question_id)
#                     .filter(Q.QuestionA.question_id == question.id)
#                     .all()
#                 )
#                 question_data["answers"] = [{"id": ans.id, "answer": ans.answer} for ans in answers]

#             result.append(question_data)

#         return result

#     except Exception as e:
#         log_err(e)
#         return []


def save_review_answers(review_id: int, answers: dict[tuple[int, int], str]) -> bool:
    try:
        for (question_group_id, question_id), answer in answers.items():
            new_answer = Q.Answer(**util.get_kwargs_for(Q.Answer, {
                Q.Answer.review_id: review_id,
                Q.Answer.question_group_id: question_group_id,
                Q.Answer.question_id: question_id,
                Q.Answer.answer: answer,
            }))
            db.session.add(new_answer)
            db.session.flush()

        update_review_status(review_id=review_id, status='Reviewed')
        return True
    except Exception as e:
        log_err(e)
        return False


def get_questions_by_article(article: Article) -> list[tuple[int, int, str, bool]]:
    round=aq.get_latest_round(article)
    if round is None:
        raise MessageException('Last round not found', Exception('Last round not found'))
    questions = db.session.execute(
        select(Q.QuestionSetGroups.question_group_id, Q.Question)
            .join(Q.QuestionGroupQuestions, Q.QuestionGroupQuestions.question_id == Q.Question.id)
            .join(Q.QuestionSetGroups, Q.QuestionSetGroups.question_group_id == Q.QuestionGroupQuestions.question_group_id)
            .where(Q.QuestionSetGroups.question_set_id==round.q_set_id)
    )

    return [(q[0], q[1].id, q[1].question, q[1].is_abc) for q in (question.tuple() for question in questions)]


def get_question_answers(question_id: int) -> list[dict[str, str]]:
    try:
        answers = (
            db.session.query(Q.QuestionA)
            .filter(Q.QuestionA.question_id == question_id)
            .all()
        )

        return [{"id": str(ans.id), "answer": ans.answer} for ans in answers]

    except Exception as e:
        log_err(e)
        return []