import services.user as au
import services.review as rs
import services.article as aq
from models.utils.Response import Response
from models.utils.decors import log_if_error
from db.db_base import log_activity
from models.utils.MessageException import MessageException


def is_reviewer(article_id: int, user_id: int) -> bool:
    review = rs.get_review(article_id, user_id)

    if review:
        return True
    
    log_activity(False, {'err': f'Reviewer {user_id} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
    return False
    
def is_reviewer_of_review(review_id: int) -> bool:
    user_id = int(au.get_curr_user_or_err().get_id())
    review = rs.get_review_by_id(review_id)
    if not review:
        log_activity(False, {'err': f'Reviewer {user_id} usiłował uzyskać dostęp do nieisteniejącego review o id: {review_id}'})
        return False
    if int(review.reviewer_id) == int(user_id):
        return True
    log_activity(False, {'err': f'Reviewer {user_id} usiłował uzyskać dostęp do review o id: {review_id}'})
    return False


@log_if_error
def set_review_status_accept(review_id: int) -> Response:
    if is_reviewer_of_review(review_id):
        return set_review_status(review_id, "Accepted by reviewer")
    raise MessageException("You are not a reviewer of this review")

@log_if_error
def set_review_status_reject(review_id: int) -> Response:
    if is_reviewer_of_review(review_id):
        set_review_status(review_id, "Rejected by reviewer")
    raise MessageException("You are not a reviewer of this review")

@log_if_error
def submit_review(review_id: int, answers) -> Response:
    if not is_reviewer_of_review(review_id):
        return Response.error_response(message = "You are not a reviewer of this review")
    
    if rs.save_review_answers(review_id, answers):
        rs.check_reviews_and_update_article_status(review_id)
        return Response.success_response()
    raise MessageException("Error submitting review")

def set_review_status(review_id: int, status: str) -> Response:
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
    if articles:
        return Response.success_response(data = articles)

    raise MessageException('Could not access the article')

@log_if_error
def get_article_details_as_reviewer(article_id: int) -> Response:
    reviewer_id = int(au.get_curr_user_or_err().get_id())
    if not is_reviewer(article_id, reviewer_id):
        return Response.error_response(message = "You are not a reviewer of this article")
    
    article = aq.get_article(article_id)
    if not article:
        log_activity(False, {'err': f'Article with id: {article_id} not found'})
        return Response.error_response(message = 'Article not found')

    review = rs.get_review(article_id, reviewer_id)
    if not review:
        log_activity(False, {'err': f'Review with article_id: {article_id} and reviewer_id: {reviewer_id} not found'})
        return Response.error_response(message = 'Review not found')
    
    questions=None
    article_content=None
    if review.status == "Pending confirmation":
        latest_round = aq.get_latest_round(article_id)
        article_content = ""
        if article and latest_round:
            article_content = latest_round.article_content
            if article_content.startswith('/'):
                article_content = f'<br><embed src="{f"/articles/uploads/{article.id}/{latest_round.round_number}/{article_content}"}" width="800" height="500" type="application/pdf">'

    elif review.status == "Accepted by reviewer":
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
