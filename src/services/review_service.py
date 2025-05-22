from sqlalchemy import and_, select
from . import article_service as aq
from models.article import Round as R
from models.utils import utils as util
from models.article import Review as Rv
from datetime import datetime, timedelta
from models.article import Questions as Q
from db.db_base import db, log_err, log_activity
from models.utils.MessageException import MessageException
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum

def get_review_by_id(review_id: int) -> Rv.Review|None:
    return Rv.Review.query.where(Rv.Review.id==review_id).first()

def __get_review_status_or_err(review_status: Rv.ReviewStatusEnum) -> Rv.ReviewStatus:
    r = Rv.ReviewStatus.query.where(Rv.ReviewStatus.stat==review_status).first()
    if r is None:
        raise ValueError(f'Review status {review_status.value} not found')
    return r

def get_review(article_id: int, reviewer_id: int) -> Rv.Review|None:
    try:
        review = db.session.execute(
            select(Rv.Review)
            .join(R.Round, Rv.Review.round_id == R.Round.id)
            .where(and_(R.Round.article_id == article_id, Rv.Review.reviewer_id == reviewer_id))
            .order_by(R.Round.round_number.desc())
        ).first()
        if review:
            return review.tuple()[0]
        return None

    except Exception as e:
        return None


def check_reviews_and_update_article_status(review_id: int) -> None:
    round_id = db.session.execute(
        select(Rv.Review.round_id)
        .filter(Rv.Review.id == review_id)
    ).scalar()

    if round_id is None:
        return

    statuses = db.session.execute(
        select(Rv.ReviewStatus.stat)
        .join(Rv.Review, Rv.Review.status_id == Rv.ReviewStatus.id)
        .where(Rv.Review.round_id == round_id)
    ).all()

    all_reviewed = all(status.tuple()[0] == Rv.ReviewStatusEnum.Reviewed for status in statuses)

    if all_reviewed:
        article: Article|None = db.session.execute(
            select(Article)
            .join(R.Round, R.Round.article_id == Article.id)
            .where(R.Round.id == round_id)
        ).scalar()
        if article:
            aq.update_article_status(article, ArticleStatusEnum.Reviewed)
        else:
            raise MessageException(f'Article with round id {round_id} not found.')



def get_articles_as_reviewer(reviewer_id: int) -> list[tuple[Article, Rv.ReviewStatusEnum]]:
    articles = db.session.execute(
        select(Article, Rv.ReviewStatus.stat)
        .join(R.Round, R.Round.article_id == Article.id)
        .join(Rv.Review, Rv.Review.round_id == R.Round.id)
        .join(Rv.ReviewStatus, Rv.ReviewStatus.id == Rv.Review.status_id)
        .join(ArticleStatus, ArticleStatus.id == Article.status_id)
        .where(and_(
            Rv.Review.reviewer_id == reviewer_id,
            Rv.ReviewStatus.stat.in_([Rv.ReviewStatusEnum.PendingConfirmation, Rv.ReviewStatusEnum.AcceptedByReviewer]),
            ArticleStatus.stat != ArticleStatusEnum.Rejected
        ))
    ).all()
    return [row.tuple() for row in articles]


def post_review(review: Rv.Review) -> bool:
    try:
        # Dodajemy nową recenzję do bazy danych
        db.session.add(review)
        db.session.flush()
        return True
    except Exception as e:
        log_err(e)
        return False


def update_review_status(review_id: int, status: Rv.ReviewStatusEnum) -> bool:
    try:
        review = get_review_by_id(review_id)
        if review is None:
            log_activity(False, {'err': f'Review with id: {review_id} not found'})
            return False

        if review.status.stat in {Rv.ReviewStatusEnum.Reviewed, Rv.ReviewStatusEnum.NotReviewed, Rv.ReviewStatusEnum.RejectedByReviewer} or aq.is_article_rejected(review.round.article_id):
            log_activity(False, {'err': f'Attempt to access review: {review_id} which should be unavailable'})
            return False
        
        review.update_status(__get_review_status_or_err(status))
        db.session.flush()
        return True
    except Exception as err:
        raise MessageException('Rv.Review status not updated', err) from None


# def get_questions_with_answers(review: Rv.Review) -> list[dict[int, str]]:
#     try:
#         q_set_id=review.round.q_set_id
#         # TODO: modify question set join
#         questions = db.session.execute(
#             select(Q.Question)
#             .join(Q.QuestionGroupQuestions, Q.QuestionGroupQuestions.question_id == Q.Question.id)
#             .join(Q.QuestionSetGroups, Q.QuestionSetGroups.question_group_id == Q.QuestionGroupQuestions.question_group_id)
#             .where(Q.QuestionSetGroups.question_set_id == q_set_id)
#         ).all()

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
#                 answers = db.session.execute(
#                     select(Q.Answer)
#                     .join(Q.QuestionA, Q.Question.id == Q.Answer.question_id)
#                     .filter(Q.QuestionA.question_id == question.id)
#                 ).all()
#                 question_data["answers"] = [{"id": ans.id, "answer": ans.answer} for ans in answers]

#             result.append(question_data)

#         return result

#     except Exception as e:
#         log_err(e)
#         return []


def save_review_answers(review_id: int, answers: dict[tuple[int, int], str]) -> None:
    for (question_group_id, question_id), answer in answers.items():
        new_answer = Q.Answer(**util.get_kwargs_for(Q.Answer, {
            Q.Answer.review_id: review_id,
            Q.Answer.question_group_id: question_group_id,
            Q.Answer.question_id: question_id,
            Q.Answer.answer: answer,
        }))
        db.session.add(new_answer)
        db.session.flush()
    update_review_status(review_id, Rv.ReviewStatusEnum.Reviewed)


def get_questions_by_article(article: Article) -> list[tuple[int, int, str, bool]]:
    round=aq.get_latest_round(article)
    if round is None:
        raise MessageException('Last round not found', Exception('Last round not found'))
    questions = db.session.execute(
        select(R.RoundQuestionGroups.question_group_id, Q.Question)
            .join(Q.QuestionGroupQuestions, Q.QuestionGroupQuestions.question_id == Q.Question.id)
            .join(R.RoundQuestionGroups, R.RoundQuestionGroups.question_group_id == Q.QuestionGroupQuestions.question_group_id)
            .where(R.RoundQuestionGroups.round_id==round.id)
    )

    return [(q[0], q[1].id, q[1].question, q[1].is_abc) for q in (question.tuple() for question in questions)]


def get_question_answers(question_id: int) -> list[dict[str, str]]:
    answers = db.session.execute(
        select(Q.QuestionA)
        .filter(Q.QuestionA.question_id == question_id)
    ).all()

    return [{"id": str(ans.id), "answer": ans.answer} for ans in (ans.tuple()[0] for ans in answers)]



    
def set_expired_status_for_reviews() -> None:
    now = datetime.now()
    yesterday_end = datetime(now.year, now.month, now.day) - timedelta(seconds=1)
    reviews = db.session.execute(
        select(Rv.Review)
        .join(R.Round, R.Round.id == Rv.Review.round_id)
        .join(Rv.ReviewStatus, Rv.ReviewStatus.id == Rv.Review.status_id)
        .where(Rv.ReviewStatus.stat == Rv.ReviewStatusEnum.PendingConfirmation)
        .where(R.Round.deadline_confirm <= yesterday_end)
    ).all()

    review_status = __get_review_status_or_err(Rv.ReviewStatusEnum.Expired)
    for review in reviews:
        review=review.tuple()[0]
        print(f'Zmieniono status review {review.id} na \'{Rv.ReviewStatusEnum.Expired}\'')
        log_activity(True, {'details': f'Zmieniono status review {review.id} na \'Expired\''})
        review.status_id = review_status.id
    db.session.flush()

def set_not_reviewed_status_for_reviews() -> None:
    now = datetime.now()
    yesterday_end = datetime(now.year, now.month, now.day) - timedelta(seconds=1)
    reviews = db.session.execute(
        select(Rv.Review)
        .join(R.Round, R.Round.id == Rv.Review.round_id)
        .join(Rv.ReviewStatus, Rv.ReviewStatus.id == Rv.Review.status_id)
        .where(Rv.ReviewStatus.stat == Rv.ReviewStatusEnum.AcceptedByReviewer)
        .where(R.Round.deadline_confirm <= yesterday_end)
    ).all()

    review_status = __get_review_status_or_err(Rv.ReviewStatusEnum.NotReviewed)
    for review in reviews:
        review=review.tuple()[0]
        print(f'Zmieniono status review {review.id} na \'{Rv.ReviewStatusEnum.NotReviewed}\'')
        log_activity(True, {'details': f'Zmieniono status review {review.id} na \'Not Reviewed\''})
        review.status_id = review_status.id
    db.session.flush()
