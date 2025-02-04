from flask import Blueprint, render_template, request, redirect, url_for, flash
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from classes.article.Review import Review
from classes.db.DBQ_Articles import DBQ_Articles
from classes.db import DB_Queries
from flask_login import current_user

review_bp = Blueprint("review", __name__)

@review_bp.route("/<int:reviewer_id>")
def list_reviewer_reviews(reviewer_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        articles = db.get_articles_as_reviewer(reviewer_id)
    except Exception as err:
        return str(err), 500
    return render_template("reviews.html", articles=articles)

@review_bp.route("/<int:article_id>/details", methods=["GET"])
def article_details(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        article = db.get_article(article_id)
        # user_id = current_user.id
        # review = db.get_review(article_id, user_id)
    except Exception as err:
        return str(err), 500

    if article.status == "Confirmation pending":
        return render_template("pending_confirmation.html", article=article, review_id=article_id)
    elif article.status == "Accepted":
        return render_template("review_form.html", article=article)
    else:
        flash("Invalid status")
        return redirect(url_for("review.list_reviewer_reviews"))

@review_bp.route("/<int:review_id>/accept", methods=["POST"])
def accept_article(review_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        db.update_review_status(review_id, "Accepted")
        return {""}, 200
    except Exception as err:
        return {"error": str(err)}, 500