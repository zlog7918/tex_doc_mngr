from db.db_base import log_err
from models.article.Article import ArticleStatusEnum
from models.utils.Response import Response
from models.utils.utils import get_function, render_base_template
from decors import approve_required
import controllers.article_controller as ac
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
@approve_required
def show_articles():
    try:
        articles = ac.get_all_articles_by_editor()
    except Exception as e:
        log_err(get_function(), e)
        return Response.error_response(message=str(e)).to_dict()
    return render_base_template("articles.html", articles=articles)


@editor_articles_bp.route('/<int:article_id>')
@approve_required
def article_details(article_id):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

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
@approve_required
def accept_article(article_id):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

    return ac.set_article_status(article_id, ArticleStatusEnum.Accepted).to_dict()


@editor_articles_bp.route('/<int:article_id>/add_round', methods=['POST'])
@approve_required
def add_round(article_id):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()
    return ac.add_round(article_id).to_dict()


@editor_articles_bp.route('<int:article_id>/assign_reviewers/', methods=['POST'])
@approve_required
def assign_reviewers(article_id):
    assigned_reviewers = request.form.getlist('assigned_reviewers[]')
    deadline_confirm = request.form.get('deadline_confirm')
    deadline_submit = request.form.get('deadline_submit')
    
    if not deadline_confirm or not deadline_submit:
        return Response.error_response(message="Both deadlines must be provided.")
    
    response = ac.assign_reviewers(article_id, assigned_reviewers, deadline_confirm, deadline_submit)

    if response.success:
        return redirect(url_for('editor_articles.article_details', article_id=article_id))
    return response.to_dict()


@editor_articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@approve_required
def reject_article(article_id):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

    result = ac.set_article_status(article_id, ArticleStatusEnum.Rejected)
    if not result:
        return Response.error_response("Article status not updated").to_dict()
    return Response.success_response().to_dict()
