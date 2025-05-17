from db.db_base import log_err
from models.article.Review import ReviewStatusEnum
from models.utils.Response import Response
import controllers.review_controller as rc
from models.utils.decors import approve_required
from models.article.Article import ArticleStatusEnum
from flask import Blueprint, render_template, request, redirect, url_for

review_bp = Blueprint("review", __name__)


@review_bp.route("/")
@approve_required
def list_reviewer_reviews():
    response = rc.get_articles_as_reviewer()
    if response.success:
        articles = response.data
        return render_template("reviews.html", articles = articles)
    return response.to_dict()


@review_bp.route("/<int:article_id>", methods=["GET"])
@approve_required
def article_details(article_id: int):
    response = rc.get_article_details_as_reviewer(article_id)
    if not response.success:
        return response.to_dict()
    
    data = response.data
    article = data["article"]
    review = data["review"]

    if article.status.stat == ArticleStatusEnum.Rejected:
        return render_template("round_tabs/rejected.html")

    if review.status.stat == ReviewStatusEnum.PendingConfirmation:
        article_content = data["article_content"]
        return render_template("review_tabs/pending_confirmation.html", article=article, article_content=article_content, review_id=review.id)
    elif review.status.stat == ReviewStatusEnum.AcceptedByReviewer:
        questions = data["questions"]
        return render_template("review_tabs/review_form.html", review_id=review.id, questions=questions)
    else:
        return Response.error_response(message = "Not implemented").to_dict()


@review_bp.route("/<int:review_id>/accept", methods=["POST"])
@approve_required
def accept_article(review_id: int):
    return rc.set_review_status_accept(review_id).to_dict()
    
@review_bp.route("/<int:review_id>/reject", methods=["POST"])
@approve_required
def reject_article(review_id: int):
    return rc.set_review_status_reject(review_id).to_dict()
    
@review_bp.route('/<int:review_id>/submit_review', methods=['POST'])
@approve_required
def submit_review(review_id: int):
    answers = {}
    try:
        for question_id, answer in request.form.items():
            if question_id.startswith("question_"):
                question_id_int = int(question_id.split("_")[1])
                answers[question_id_int] = answer
    except Exception as e:
        log_err(e)
        return Response.error_response(message = "Failed to save answers.").to_dict()

    response = rc.submit_review(review_id, answers)

    if response.success:
        return redirect(url_for("review.list_reviewer_reviews"))

    return response.to_dict()
