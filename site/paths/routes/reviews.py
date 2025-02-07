from flask import Blueprint, render_template, request, redirect, url_for, flash
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from classes.article.Review import Review
from classes.db.DBQ_Articles import DBQ_Articles
from classes.db import DB_Queries
from flask_login import login_required, current_user

review_bp = Blueprint("review", __name__)


@review_bp.route("/")
@login_required
def list_reviewer_reviews():
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        articles = db.get_articles_as_reviewer(current_user.get__id())
    except Exception as err:
        return str(err), 500
    return render_template("reviews.html", articles=articles)


@review_bp.route("/<int:article_id>", methods=["GET"])
@login_required
def article_details(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        article = db.get_article(article_id)
        review = db.get_review(article_id, current_user.get__id())
        print("get review id: " + str(review.id))

        if review.status == "Pending confirmation":
            return render_template("review_tabs/pending_confirmation.html", article=article, review_id=review.id)
        elif review.status == "Accepted by reviewer":
            questions = db.get_questions_by_article(article_id)

            if not questions:
                return "No questions found for the article.", 404

            for question in questions:
                if question['is_abc']:
                    answers = db.get_question_answers(question['id'])
                    question['answers'] = answers if answers else [{"id": 0, "answer": "No answers available"}]

            return render_template("review_tabs/review_form.html", review_id=review.id, questions=questions)
        else:
            return "Not implemented", 501
    except Exception as err:
        return str(err), 500


@review_bp.route("/<int:review_id>/accept", methods=["POST"])
@login_required
def accept_article(review_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        result = db.update_review_status(review_id, "Accepted by reviewer")
        if result:
            return {"message": "Accepted reviewing the article"}, 200
        else:
            return {"error": "Failed to accept the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500
    
@review_bp.route("/<int:review_id>/reject", methods=["POST"])
@login_required
def reject_article(review_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        result = db.update_review_status(review_id, "Rejected by reviewer")
        if result:
            return {"message": "Rejected reviewing the article"}, 200
        else:
            return {"error": "Failed to reject the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500
    
@review_bp.route('/<int:review_id>/submit_review', methods=['POST'])
@login_required
def submit_review(review_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    answers = {}

    if request.method != 'POST':
        flash("Invalid request method.", "error")
        return redirect(url_for("review.list_reviewer_reviews"))
    
    for question_id, answer in request.form.items():
        if question_id.startswith("question_"):
            question_id_int = int(question_id.split("_")[1])
            answers[question_id_int] = answer
    
    if db.save_review_answers(review_id, answers):
        # TODO: replace with observer
        db.check_reviews_and_update_article_status(review_id)

        return redirect(url_for("review.list_reviewer_reviews"))
    else:
        flash(f"Error submitting review", "error")
        return "Error submitting review.", 500
