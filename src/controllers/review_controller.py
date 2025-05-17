import services.user as au
import services.review as rs
import services.article as aq
from models.utils.Response import Response
from models.utils.decors import log_if_error
from models.article.Review import ReviewStatusEnum
from models.utils.MessageException import MessageException


def is_reviewer(article_id: int, user_id: int) -> None:
    review = rs.get_review(article_id, user_id)
    if not review:
        raise MessageException(
            'You are not a reviewer of this article',
            err=Exception(f'Reviewer {user_id} usiłował uzyskać dostęp do artykułu o id: {article_id}')
        )

def is_reviewer_of_review(review_id: int) -> None:
    user_id = int(au.get_curr_user_or_err().get_id())
    review = rs.get_review_by_id(review_id)
    if not review:
        raise MessageException(
            'You are not a reviewer of this review',
            err=Exception(f'Reviewer {user_id} usiłował uzyskać dostęp do nieisteniejącego review o id: {review_id}')
        )
    if int(review.reviewer_id) == int(user_id):
        return
    raise MessageException(
        'You are not a reviewer of this review',
        err=Exception(f'Reviewer {user_id} usiłował uzyskać dostęp do review o id: {review_id}')
    )

@log_if_error
def set_review_status_accept(review_id: int) -> Response:
    is_reviewer_of_review(review_id)
    return set_review_status(review_id, ReviewStatusEnum.AcceptedByReviewer)

@log_if_error
def set_review_status_reject(review_id: int) -> Response:
    is_reviewer_of_review(review_id)
    return set_review_status(review_id, ReviewStatusEnum.RejectedByReviewer)

@log_if_error
def submit_review(review_id: int, answers) -> Response:
    is_reviewer_of_review(review_id)
    
    rs.save_review_answers(review_id, answers)
    rs.check_reviews_and_update_article_status(review_id)
    return Response.success_response()

def set_review_status(review_id: int, status: ReviewStatusEnum) -> Response:
    review = rs.get_review_by_id(review_id)
    if review is None:
        raise MessageException('Review not found')

    result = rs.update_review_status(review_id, status)
    if not result:
        raise MessageException('Review status not updated')

    return Response.success_response()

@log_if_error
def get_articles_as_reviewer() -> Response:
    reviewer_id = int(au.get_curr_user_or_err().get_id())
    articles = rs.get_articles_as_reviewer(reviewer_id)
    return Response.success_response(data = articles)

@log_if_error
def get_article_details_as_reviewer(article_id: int) -> Response:
    reviewer_id = int(au.get_curr_user_or_err().get_id())
    is_reviewer(article_id, reviewer_id)
    
    article = aq.get_article(article_id)
    if not article:
        raise MessageException(
            'Article not found',
            err=Exception(f'Article with id: {article_id} not found')
        )

    review = rs.get_review(article_id, reviewer_id)
    if not review:
        raise MessageException(
            'Review not found',
            err=Exception(f'Review with article_id: {article_id} and reviewer_id: {reviewer_id} not found')
        )
    
    questions=None
    article_content=None
    if review.status.stat == ReviewStatusEnum.PendingConfirmation:
        latest_round = aq.get_latest_round(article_id)
        article_content = ""
        if article and latest_round:
            article_content = latest_round.article_content
            if article_content.startswith('/'):
                article_content = f'<br><embed src="{f"/articles/uploads/{article.id}/{latest_round.round_number}/{article_content}"}" width="800" height="500" type="application/pdf">'

    elif review.status.stat == ReviewStatusEnum.AcceptedByReviewer:
        questions = rs.get_questions_by_article(article_id)
        if not questions:
            raise MessageException("No questions found for the article.")

        for question in questions:
            if question['is_abc']:
                answers = rs.get_question_answers(question['id'])
                question['answers'] = answers if answers else [{"id": 0, "answer": "No answers available"}]
    
    else:
        return Response.error_response(message = "Not implemented")
    return Response.success_response(data = {"article": article, "review": review, "questions": questions, "article_content": article_content})
