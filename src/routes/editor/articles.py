from models.usr import User as U
from models.utils.Response import Response
import controllers.article_controller as ac
import controllers.question_controller as qc
from flask import request, redirect, Blueprint
from models.article.Article import ArticleStatusEnum, Article
from models.utils import decors as decor, utils as util, utils_flask as f_util

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
@decor.group_required(U.UserGroupEnum.Editor)
def show_articles():
    response = ac.get_all_articles_by_editor()
    if response.success:
        articles = response.data
        return f_util.render_base_template("articles.html", articles=articles)
    else:
        return response.to_dict()

@editor_articles_bp.route('/rejected_articles')
@decor.group_required(U.UserGroupEnum.Editor)
def rejected_articles():
    return ac.get_all_rejected_articles_by_editor().to_dict()

@editor_articles_bp.route('/<int:article_id>')
@decor.group_required(U.UserGroupEnum.Editor)
def article_details(article_id: int):
    response = ac.get_article_data_as_editor(article_id)

    if not response.success:
        return response.to_dict()

    article: Article = response.data["article"]
    article_content = response.data["article_content"]

    data = response.to_dict()
# TODO: change templates
    if article.status.stat == ArticleStatusEnum.Submitted:
        return f_util.render_base_template("article_submitted.html", article=article, article_content=article_content)
    elif article.status.stat == ArticleStatusEnum.Accepted:
        reviewers = response.data["reviewers"]
        assigned_reviewers = response.data["assigned_reviewers"]
        reviews = response.data["reviews"]
        question_groups=qc.get_all_question_groups()
        if question_groups.success:
            question_groups=question_groups.data
        else:
            question_groups=[]
        tab_content = f_util.render_base_template("round_tabs/accepted.html", article=article, assigned_reviewers=assigned_reviewers, reviewers=reviewers, question_groups=question_groups)
    elif article.status.stat == ArticleStatusEnum.InReview:
        reviews = response.data["reviews"]
        tab_content = f_util.render_base_template("round_tabs/in_review.html", reviews=reviews)
    elif article.status.stat == ArticleStatusEnum.Reviewed:
        grouped_answers = response.data["grouped_answers"]
        tab_content = f_util.render_base_template("round_tabs/reviewed.html", article=article, grouped_answers=grouped_answers)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        print("here")
        return f_util.render_base_template("round_tabs/rejected.html", article=article)
    elif article.status.stat == ArticleStatusEnum.NeedsCorrections:
        return f_util.render_base_template("round_tabs/needs_corrections.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Final:
        return f_util.render_base_template("round_tabs/final.html", article=article)
    else:
        return Response.error_response(message="Not found").to_dict()

    return f_util.render_base_template("article_round_base.html", tab_content=tab_content, article=article, data=data)


@editor_articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def accept_article(article_id: int):
    return ac.set_article_status_accept(article_id).to_dict()

@editor_articles_bp.route('/<int:article_id>/request_correction', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def request_article_correction(article_id: int):
    return ac.set_article_status_needs_corrections(article_id).to_dict()

@editor_articles_bp.route('/<int:article_id>/finish', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def finish_article(article_id: int):
    return ac.set_article_status_final(article_id).to_dict()

@editor_articles_bp.route('<int:article_id>/assign_reviewers', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
@decor.handle_form_not_filled
def assign_reviewers(article_id: int):
    assigned_reviewers = request.form.getlist('assigned_reviewers[]')
    assigned_emails = request.form.getlist('invited_emails[]')
    question_set = request.form.getlist('question_group')
    (deadline_confirm, deadline_submit, tz)=util.get_from_form(request.form, (
        'deadline_confirm',
        'deadline_submit',
        'tz',
    ))
    
    response = ac.assign_reviewers(article_id, question_set, assigned_reviewers, assigned_emails, deadline_confirm, deadline_submit, tz)

    if response.success:
        return redirect(f_util.url_with_lang_for('editor_articles.article_details', article_id=article_id))
    return response.to_dict()

@editor_articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@decor.group_required(U.UserGroupEnum.Editor)
def reject_article(article_id: int):
    return ac.set_article_status_reject(article_id).to_dict()

@editor_articles_bp.route('/uploads/<int:article_id>/<int:round_num>/<filename>')
@decor.group_required(U.UserGroupEnum.Editor)
def uploaded_file(filename: str, article_id: int, round_num: int):
    ret=ac.get_uploaded_file(article_id, round_num, filename, U.UserGroupEnum.Editor)
    if ret.success:
        return ret.data
    return ret.to_dict()
