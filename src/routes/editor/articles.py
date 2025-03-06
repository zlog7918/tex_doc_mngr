import services.article as aq
from flask_login import login_required
from models.utils.Response import Response
import controllers.article_controller as ac
from models.utils.utils import render_base_template
from models.article.Article import ArticleStatusEnum
from flask import request, redirect, url_for, Blueprint, render_template

editor_articles_bp = Blueprint("editor_articles", __name__)

'''
Submitted - artykół przesłany przez autora - nowy lub poprawiony
Accepted - zweryfikownay przez edytora, gotowy do recenzji
In review - przesłany do recenzentów, oczekujący na recenzje
Reviewed - przesłane wszystkie recenzje/zakończył się czas na recenzje
Rejected - odrzucony
Needs Corrections - wymaga poprawek, czeka na poprawki autora
Final - artykół jest zakończony, nie wymaga poprawek, wersja końcowa
'''


@editor_articles_bp.route('/')
@login_required
def show_articles():
    try:
        articles = ac.get_all_articles_by_editor()
    except Exception as err:
        return Response.Response.error_response(message=str(err)).to_dict()
    return render_base_template("articles.html", articles=articles)


@editor_articles_bp.route('/<int:article_id>')
@login_required
def article_details(article_id):
    response = ac.get_article_data(article_id)

    if not response.success:
        return response.to_dict()

    article = response.data["article"]

    data = response.to_dict()
# TODO: change templates
    if article.status.stat == ArticleStatusEnum.Submitted:
        return render_base_template("article_submitted.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Accepted:
        reviewers = response.data["reviewers"]
        assigned_reviewers = response.data["assigned_reviewers"]
        reviews = response.data["reviews"]
        tab_content = render_base_template("round_tabs/accepted.html", article=article, assigned_reviewers=assigned_reviewers, reviewers=reviewers)
    elif article.status.stat == ArticleStatusEnum.InReview:
        reviews = response.data["reviews"]
        tab_content = render_base_template("round_tabs/in_review.html", reviews=reviews)
    elif article.status.stat == ArticleStatusEnum.Reviewed:
        grouped_answers = response.data["grouped_answers"]
        return render_base_template("round_tabs/reviewed.html", grouped_answers=grouped_answers)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        return render_base_template("round_tabs/rejected.html")

    return render_template("article_round_base.html", tab_content=tab_content, article=article, data=data)


@editor_articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@login_required
def accept_article(article_id):
    return ac.set_article_status(article_id, ArticleStatusEnum.Accepted).to_dict()


@editor_articles_bp.route('/<int:article_id>/add_round', methods=['POST'])
@login_required
def add_round(article_id):
    return ac.add_round(article_id).to_dict()


@editor_articles_bp.route('<int:article_id>/assign_reviewers/', methods=['POST'])
@login_required
def assign_reviewers(article_id):
    assigned_reviewers = request.form.get('assigned_reviewers[]')
    deadline_confirm = request.form.get('deadline_confirm')
    deadline_submit = request.form.get('deadline_submit')
    
    response = ac.assign_reviewers(article_id, assigned_reviewers, deadline_confirm, deadline_submit)

    if response.success:
        return redirect(url_for('editor_articles.article_details', article_id=article_id))
    return response.to_dict()


@editor_articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@login_required
def reject_article(article_id):
    result = aq.update_article_status(article_id, 5)
    if not result:
        return Response.error_response("Article status not updated")
    return Response.success_response()


# @editor_articles_bp.route('/<int:article_id>/update_status', methods=['POST'])
# @login_required
# def update_article_status(article_id):
#     try:
#         article = aq.get_article(article_id)
#         if not article:
#             return Response.error_response("Article not found")

#         current_status = article.status.stat.stat

#         # Sprawdzenie obecnego statusu i zmiana
#         if current_status == ArticleStatusEnum.Accepted:
#             # Ustawienie statusu na "In review"
#             result = aq.update_article_status(article_id, 3)
#             if not result:
#                 return {"error": "Failed to update status to 'In review'"}, 500

#             # Tworzenie nowej rundy recenzji
#             new_round_id = len(article["rounds"]) + 1
#             new_round = {"id": new_round_id, "reviews": []}
#             article["rounds"].append(new_round)
#             # save_article_rounds(article_id, article["rounds"])

#             return {"message": "Status updated to 'In review' and new review round created"}, 200

#         elif current_status == ArticleStatusEnum.InReview:
#             # Sprawdzenie liczby przesłanych recenzji
#             latest_round = article["rounds"][-1] if article["rounds"] else None
#             if not latest_round:
#                 return {"error": "No active review round found"}, 400

#             total_reviews = len(latest_round["reviews"])
#             if total_reviews >= 3:  # Zakładamy, że wymagane są 3 recenzje
#                 result = aq.update_article_status(article_id, 4)
#                 if result:
#                     return {"message": "All reviews submitted. Status updated to 'Reviewed'"}, 200
#                 else:
#                     return {"error": "Failed to update status to 'Reviewed'"}, 500
#             else:
#                 remaining = 3 - total_reviews
#                 return {"message": f"Waiting for {remaining} more reviews"}, 200

#         else:
#             return {"error": "Invalid status for update"}, 400

#     except Exception as err:
#         return {"error": str(err)}, 500
