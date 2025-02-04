from flask import Blueprint, render_template, request, redirect, url_for, flash
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from classes.article.Review import Review
from classes.db.DBQ_Articles import DBQ_Articles

review_bp = Blueprint("review", __name__)

@review_bp.route("/<int:reviewer_id>")
def list_reviewer_reviews(reviewer_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        articles = db.get_articles_as_reviewer(reviewer_id)
    except Exception as err:
        return str(err), 500
    return render_template("reviews.html", articles=articles)

@review_bp.route("/<int:review_id>", methods=["GET", "POST"])
def review(review_id):
    if request.method == "POST":
        db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
        review = Review(
            round_id=-1,
            review_text=request.form["comments"],
            status="Reviewed",
            reviewer_id=-1
        )
        try:
            db.post_review(review)
        except Exception as err:
            return str(err), 500
        flash("Review submitted successfully!")
        return redirect(url_for("review.index"))
    return "Not implemented", 501#render_template("review_form.html", article_id=article_id)

@review_bp.route("/<int:article_id>/details", methods=["GET"])
def article_details(article_id):
    return "Not implemented", 501