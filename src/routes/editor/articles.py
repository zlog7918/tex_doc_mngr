from db.db_base import log_err
from models.utils.Response import Response
import controllers.article_controller as ac
from models.utils import decors as decor, utils as util
from models.article.Article import ArticleStatusEnum, Article
from flask import request, redirect, url_for, Blueprint, render_template

editor_articles_bp=Blueprint("editor_articles", __name__)

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
@decor.approve_required
def show_articles():
    try:
        articles = ac.get_all_articles_by_editor()
    except Exception as e:
        log_err(e)
        return Response.error_response(message=str(e)).to_dict()
    return util.render_base_template("articles.html", articles=articles)


@editor_articles_bp.route('/<int:article_id>')
@decor.approve_required
def article_details(article_id: int):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

    response = ac.get_article_data(article_id)

    if not response.success:
        return response.to_dict()

    article: Article = response.data["article"]

    data = response.to_dict()
# TODO: change templates
    if article.status.stat == ArticleStatusEnum.Submitted:
        return util.render_base_template("article_submitted.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Accepted:
        reviewers = response.data["reviewers"]
        assigned_reviewers = response.data["assigned_reviewers"]
        reviews = response.data["reviews"]
        tab_content = util.render_base_template("round_tabs/accepted.html", article=article, assigned_reviewers=assigned_reviewers, reviewers=reviewers)
    elif article.status.stat == ArticleStatusEnum.InReview:
        reviews = response.data["reviews"]
        tab_content = util.render_base_template("round_tabs/in_review.html", reviews=reviews)
    elif article.status.stat == ArticleStatusEnum.Reviewed:
        grouped_answers = response.data["grouped_answers"]
        return util.render_base_template("round_tabs/reviewed.html", grouped_answers=grouped_answers)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        return util.render_base_template("round_tabs/rejected.html")

    return render_template("article_round_base.html", tab_content=tab_content, article=article, data=data)


@editor_articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@decor.approve_required
def accept_article(article_id: int):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

    return ac.set_article_status(article_id, ArticleStatusEnum.Accepted).to_dict()


@editor_articles_bp.route('/<int:article_id>/add_round', methods=['POST'])
@decor.approve_required
def add_round(article_id: int):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()
    return ac.add_round(article_id).to_dict()


@editor_articles_bp.route('<int:article_id>/assign_reviewers/', methods=['POST'])
@decor.approve_required
@decor.handle_form_not_filled
def assign_reviewers(article_id: int):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

    assigned_reviewers = request.form.getlist('assigned_reviewers[]')
    (deadline_confirm, deadline_submit)=util.get_from_form(request.form, (
        'deadline_confirm',
        'deadline_submit',
    ))
    
    response = ac.assign_reviewers(article_id, assigned_reviewers, deadline_confirm, deadline_submit)

    if response.success:
        return redirect(url_for('editor_articles.article_details', article_id=article_id))
    return response.to_dict()


@editor_articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@decor.approve_required
def reject_article(article_id: int):
    if not ac.is_editor(article_id):
        return Response.error_response(message = "You are not an editor of this article").to_dict()

    result = ac.set_article_status(article_id, ArticleStatusEnum.Rejected)
    if result.success:
        return Response.success_response().to_dict()
    return Response.error_response("Article status not updated").to_dict()
