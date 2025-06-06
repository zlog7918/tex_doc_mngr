from models.usr import User as U
import services.user_service as au
import services.review_service as rs
import services.article_service as aq
from models.utils.Response import Response
from models.article.Review import ReviewStatusEnum
from models.utils.MessageException import MessageException
from models.utils import decors as decor, utils_flask as f_util


def is_reviewer(user: U.User, article_id: int) -> None:
    if U.UserGroupEnum.Reviewer not in {ug.group.group for ug in user.groups}:
        raise MessageException(
            'You are not a reviewer of this article',
            err=Exception(f'Nie-reviewer {user.id} usiłował uzyskać dostęp do artykułu o id: {article_id}')
        )
    review = rs.get_review(article_id, user.id)
    if not review:
        raise MessageException(
            'You are not a reviewer of this article',
            err=Exception(f'Reviewer {user.id} usiłował uzyskać dostęp do artykułu o id: {article_id}')
        )

def is_reviewer_of_review(review_id: int) -> None:
    user = au.get_curr_user_or_err()
    if U.UserGroupEnum.Reviewer not in {ug.group.group for ug in user.groups}:
        raise MessageException(
            'You are not a reviewer of this review',
            err=Exception(f'Nie-reviewer {user.id} usiłował uzyskać dostęp do review o id: {review_id}')
        )
    review = rs.get_review_by_id(review_id)
    if not review:
        raise MessageException(
            'You are not a reviewer of this review',
            err=Exception(f'Reviewer {user.id} usiłował uzyskać dostęp do nieisteniejącego review o id: {review_id}')
        )
    if review.reviewer_id == user.id:
        return
    raise MessageException(
        'You are not a reviewer of this review',
        err=Exception(f'Reviewer {user.id} usiłował uzyskać dostęp do review o id: {review_id}')
    )

@decor.log_if_error
def set_review_status_accept(review_id: int) -> Response:
    is_reviewer_of_review(review_id)
    return set_review_status(review_id, ReviewStatusEnum.AcceptedByReviewer)

@decor.log_if_error
def set_review_status_reject(review_id: int) -> Response:
    is_reviewer_of_review(review_id)
    return set_review_status(review_id, ReviewStatusEnum.RejectedByReviewer)

@decor.log_if_error
def submit_review(review_id: int, answers: dict[tuple[int, int], str]) -> Response:
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

@decor.log_if_error
def get_articles_as_reviewer() -> Response:
    reviewer_id = au.get_curr_user_or_err().id
    articles = rs.get_articles_as_reviewer(reviewer_id)
    return Response.success_response(data = articles)

@decor.log_if_error
def get_article_details_as_reviewer(article_id: int) -> Response:
    reviewer = au.get_curr_user_or_err()
    is_reviewer(reviewer, article_id)
    
    article = aq.get_article(article_id)
    if not article:
        raise MessageException(
            'Article not found',
            err=Exception(f'Article with id: {article_id} not found')
        )

    review = rs.get_review(article_id, reviewer.id)
    if not review:
        raise MessageException(
            'Review not found',
            err=Exception(f'Review with article_id: {article_id} and reviewer_id: {reviewer.id} not found')
        )
    
    questions=None
    article_content=None
    
    if review.status.stat == ReviewStatusEnum.PendingConfirmation:
        latest_round = aq.get_latest_round(article)
        article_content = ""
        if article and latest_round:
            article_content = latest_round.article_content
            if article_content.startswith('/'):
                article_content = f'<br><embed src="{f_util.url_with_lang_for('review.uploaded_file', filename=article_content, article_id=article.id, round_num=latest_round.round_number)}" width="800" height="500" type="application/pdf">'

    elif review.status.stat == ReviewStatusEnum.AcceptedByReviewer:
        tuple_questions = rs.get_questions_by_article(article)
        if not tuple_questions:
            raise MessageException("No questions found for the article.")
        questions=[]
        for question in tuple_questions:
            question={'group_id': question[0], 'id': question[1], 'text': question[2], 'is_abc': question[3]}
            if question['is_abc']:
                answers = rs.get_question_answers(question['id'])
                question['answers'] = answers if answers else [{'id': '0', 'answer': 'No answers available'}]
            questions.append(question)
    else:
        return Response.error_response(message = "Not implemented")
    return Response.success_response(data = {"article": article, "review": review, "questions": questions, "article_content": article_content})
