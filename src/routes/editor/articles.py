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
    response = ac.get_all_articles_by_editor()
    if response.success:
        articles = response.data
        return util.render_base_template("articles.html", articles=articles)
    else:
        return response.to_dict()


@editor_articles_bp.route('/<int:article_id>')
@decor.approve_required
def article_details(article_id: int):
    response = ac.get_article_data_as_editor(article_id)

    if not response.success:
        return response.to_dict()

    article: Article = response.data["article"]
    article_content = response.data["article_content"]

    data = response.to_dict()
# TODO: change templates
    if article.status.stat == ArticleStatusEnum.Submitted:
        return util.render_base_template("article_submitted.html", article=article, article_content=article_content)
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
        tab_content = util.render_base_template("round_tabs/reviewed.html", article=article, grouped_answers=grouped_answers)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        return util.render_base_template("round_tabs/rejected.html")
    elif article.status.stat == ArticleStatusEnum.NeedsCorrections:
        return util.render_base_template("round_tabs/needs_corrections.html", article=article)
    else:
        return Response.error_response(message="Not found").to_dict()

    return render_template("article_round_base.html", tab_content=tab_content, article=article, data=data)


@editor_articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@decor.approve_required
def accept_article(article_id: int):
    return ac.set_article_status_accept(article_id).to_dict()

@editor_articles_bp.route('/<int:article_id>/request_correction', methods=['POST'])
@decor.approve_required
def request_article_correction(article_id: int):
    return ac.set_article_status_needs_corrections(article_id).to_dict()


@editor_articles_bp.route('<int:article_id>/assign_reviewers/', methods=['POST'])
@decor.approve_required
@decor.handle_form_not_filled
def assign_reviewers(article_id: int):
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
    return ac.set_article_status_reject(article_id).to_dict()
