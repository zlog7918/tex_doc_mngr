from db.db_base import log_err
from models.article.Article import ArticleStatusEnum
from models.utils.Response import Response
import controllers.article_controller as ac
from flask import request, Blueprint, render_template
from models.utils import decors as decor, utils as util

articles_bp = Blueprint("articles", __name__)

@articles_bp.route('/')
@decor.approve_required
def show_articles():
    response = ac.get_my_articles()
    if response.success:
        articles = response.data
        return util.render_base_template("my_articles.html", articles=articles)
    return response.to_dict()

@articles_bp.route('/<int:article_id>')
@decor.approve_required
def article_details(article_id):
    response = ac.get_article_data_as_author(article_id)

    if not response.success:
        return response.to_dict()

    article = response.data["article"]
    article_content = response.data["article_content"]

    data = response.to_dict()

    if article.status.stat == ArticleStatusEnum.Submitted:
        tab_content = util.render_base_template("author_tabs/default_tab.html", article=article, article_content=article_content)
    elif article.status.stat == ArticleStatusEnum.Accepted:
        tab_content = util.render_base_template("author_tabs/default_tab.html", article=article, article_content=article_content)
    elif article.status.stat == ArticleStatusEnum.InReview:
        tab_content = util.render_base_template("author_tabs/default_tab.html", article=article, article_content=article_content)
    elif article.status.stat == ArticleStatusEnum.Reviewed:
        tab_content = util.render_base_template("author_tabs/default_tab.html", article=article, article_content=article_content)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        tab_content = util.render_base_template("author_tabs/default_tab.html", article=article, article_content=article_content)
    elif article.status.stat == ArticleStatusEnum.NeedsCorrections:
        tab_content = util.render_base_template("author_tabs/needs_corrections.html", article=article)
    else:
        return Response.error_response(message="Not found").to_dict()
    return render_template("article_author_base.html", tab_content=tab_content, article=article, data=data)

@articles_bp.route('/upload-form')
@decor.approve_required
def upload_form():
    editors = ac.get_available_editors()
    return render_template('uploading_article.html', editors = editors)

@articles_bp.route('/upload', methods=['POST'])
@decor.approve_required
@decor.handle_form_not_filled
def upload_file():
    title, editor=util.get_from_form(request.form, (
        'title',
        'editor',
    ))

    try:
        editor = int(editor)
    except (ValueError, TypeError) as e:
        log_err(e)
        return Response.error_response(message='Invalid editor ID').to_dict()
    if 'file' not in request.files:
        return Response.error_response(message='Nie przesłano pliku').to_dict()

    file = request.files['file']
    if not file.filename:
        return Response.error_response(message='No file selected').to_dict()

    return ac.upload_file(title, editor, file).to_dict()

@articles_bp.route('/<int:article_id>/upload-correction', methods=['POST'])
@decor.approve_required
@decor.handle_form_not_filled
def upload_correction(article_id: int):
    if 'file' not in request.files:
        return Response.error_response(message='Nie przesłano pliku').to_dict()

    file = request.files['file']
    if not file.filename:
        return Response.error_response(message='No file selected').to_dict()

    return ac.upload_correction(article_id, file).to_dict()


@articles_bp.route('/uploads/<int:article_id>/<int:round_num>/<filename>')
@decor.approve_required
def uploaded_file(filename, article_id: int, round_num: int):
    ret=ac.get_uploaded_file(f"{article_id}/{round_num}/{filename}")
    if ret.success:
        return ret.data
    return ret.to_dict()


@articles_bp.route('/generate-preview', methods=['POST'])
@decor.approve_required
def generate_preview():
    if 'file' not in request.files:
        return Response.error_response(message='Nie przesłano pliku').to_dict()

    file = request.files['file']
    if not file.filename:
        return Response.error_response(message='No file selected').to_dict()
    if not file.filename.endswith('.tex'):
        return Response.error_response(message="Nieprawidłowy format pliku").to_dict()

    response = ac.generate_preview(file)
    if response.success:
        return response.data
    return response.to_dict()


@articles_bp.route('/temp-preview/<filename>')
@decor.approve_required
def temp_preview(filename: str):
    ret=ac.temp_preview(filename)
    if ret.success:
        return ret.data
    return ret.to_dict()
