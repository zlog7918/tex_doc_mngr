from flask import Blueprint, render_template, request, redirect, url_for, flash
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from classes.article.Review import Review
from classes.db.DBQ_Articles import DBQ_Articles
from classes.db import DB_Queries
from flask_login import current_user

review_bp = Blueprint("review", __name__)

@review_bp.route("/")
def list_reviewer_reviews():
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        articles = db.get_articles_as_reviewer(current_user.get__id())
    except Exception as err:
        return str(err), 500
    return render_template("reviews.html", articles=articles)

@review_bp.route("/<int:article_id>", methods=["GET"])
def article_details(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        article = db.get_article(article_id)
        review = db.get_review(article_id, current_user.get__id())
        print("get review id: " + str(review.id))
        
        if review.status == "Pending confirmation":
            return render_template("review_tabs/pending_confirmation.html", article=article, review_id=review.id)
        elif review.status == "Accepted":
            return render_template("review_form.html", article=article)
        else:
            return "Not implemented", 501
    except Exception as err:
        return str(err), 500

@review_bp.route("/<int:review_id>/accept", methods=["POST"])
def accept_article(review_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        result = db.update_review_status(review_id, "Accepted")
        if result:
            return {"message": "Accepted reviewing the article"}, 200
        else:
            return {"error": "Failed to accept the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500