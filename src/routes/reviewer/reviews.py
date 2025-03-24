import services.user as su
import services.review as rq
import services.article as aq
from db.db_base import log_activity
from models.utils.Response import Response
import controllers.article_controller as ac
from models.utils.decors import approve_required
from flask import Blueprint, render_template, request, redirect, url_for, flash

review_bp = Blueprint("review", __name__)


@review_bp.route("/")
@approve_required
def list_reviewer_reviews():
    try:
        user=su.get_curr_user_or_err()
        articles = rq.get_articles_as_reviewer(int(user.get_id()))
    except Exception as err:
        return str(err), 500
    return render_template("reviews.html", articles=articles)


@review_bp.route("/<int:article_id>", methods=["GET"])
@approve_required
def article_details(article_id: int):
    try:
        user=su.get_curr_user_or_err()
        if not ac.is_reviewer(article_id, int(user.get_id())):
            return Response.error_response(message = "You are not a reviewer of this article").to_dict()

        article = aq.get_article(article_id)
        if not article:
            log_activity(False, {'err': f'Article with id: {article_id} not found'})
            return Response.error_response(message = 'Article not found').to_dict()
        reviewer_id = int(user.get_id())
        review = rq.get_review(article_id, reviewer_id)
        if not review:
            log_activity(False, {'err': f'Review with article_id: {article_id} and reviewer_id: {reviewer_id} not found'})
            return Response.error_response(message = 'Review not found').to_dict()

        if review.status == "Pending confirmation":
            return render_template("review_tabs/pending_confirmation.html", article=article, review_id=review.id)
        elif review.status == "Accepted by reviewer":
            questions = rq.get_questions_by_article(article_id)

            if not questions:
                return "No questions found for the article.", 404

            for question in questions:
                if question['is_abc']:
                    answers = rq.get_question_answers(question['id'])
                    question['answers'] = answers if answers else [{"id": 0, "answer": "No answers available"}]

            return render_template("review_tabs/review_form.html", review_id=review.id, questions=questions)
        else:
            return "Not implemented", 501
    except Exception as err:
        return str(err), 500


@review_bp.route("/<int:review_id>/accept", methods=["POST"])
@approve_required
def accept_article(review_id):
    try:
        if not ac.is_reviewer_of_review(review_id):
            return Response.error_response(message = "You are not a reviewer of this review").to_dict()

        result = ac.set_review_status(review_id, "Accepted by reviewer")
        if result.success:
            print('success')
            return {"message": "Accepted reviewing the article"}, 200
        else:
            print(result.message)
            return {"error": "Failed to accept the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500
    
@review_bp.route("/<int:review_id>/reject", methods=["POST"])
@approve_required
def reject_article(review_id):
    try:
        if not ac.is_reviewer_of_review(review_id):
            return Response.error_response(message = "You are not a reviewer of this review").to_dict()

        result = ac.set_review_status(review_id, "Rejected by reviewer")
        if result.success:
            return {"message": "Rejected reviewing the article"}, 200
        else:
            return {"error": "Failed to reject the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500
    
@review_bp.route('/<int:review_id>/submit_review', methods=['POST'])
@approve_required
def submit_review(review_id):
    if not ac.is_reviewer_of_review(review_id):
        return Response.error_response(message = "You are not a reviewer of this review").to_dict()

    answers = {}

    if request.method != 'POST':
        flash("Invalid request method.", "error")
        return redirect(url_for("review.list_reviewer_reviews"))
    
    for question_id, answer in request.form.items():
        if question_id.startswith("question_"):
            question_id_int = int(question_id.split("_")[1])
            answers[question_id_int] = answer
    
    if rq.save_review_answers(review_id, answers):
        # TODO: replace with observer
        rq.check_reviews_and_update_article_status(review_id)

        return redirect(url_for("review.list_reviewer_reviews"))
    else:
        flash(f"Error submitting review", "error")
        return "Error submitting review.", 500
