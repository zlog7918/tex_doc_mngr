from flask import Blueprint, render_template, request, redirect, url_for, flash

review_bp = Blueprint("review", __name__)

# Dane testowe
reviews = []
articles = [{"id": 1, "title": "Article 1", "status": "Pending Review"}]

# @review_bp.route("/")


@review_bp.route("/next_round/<int:article_id>")
def next_round(article_id):
    for article in articles:
        if article["id"] == article_id:
            article["status"] = "Second Round"
            flash(f"Article '{article['title']}' moved to the next round.")
    return redirect(url_for("review.index"))

@review_bp.route("/<int:article_id>", methods=["GET", "POST"])
def review(article_id):
    if request.method == "POST":
        review_data = {
            "article_id": article_id,
            "reviewer": request.form["reviewer"],
            "comments": request.form["comments"],
            "rating": request.form["rating"]
        }
        reviews.append(review_data)
        flash("Review submitted successfully!")
        return redirect(url_for("review.index"))
    return render_template("review_form.html", article_id=article_id)
