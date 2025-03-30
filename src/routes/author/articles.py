import os
from db.db_base import log_err
from decors import approve_required
from werkzeug.utils import secure_filename
from models.article.Article import ArticleStatusEnum
from models.utils.Response import Response
import controllers.article_controller as ac
from werkzeug.datastructures import FileStorage
from models.utils.consts import ALLOWED_EXTENSIONS
from models.utils.EnvConsts import envConsts as ec
from flask import request, Blueprint, render_template
from models.utils.utils import get_function, render_base_template

articles_bp = Blueprint("articles", __name__)

@articles_bp.route('/')
@approve_required
def show_articles():
    try:
        articles = ac.get_my_articles()
    except Exception as e:
        log_err(get_function(), e)
        return Response.error_response(message=str(e)).to_dict()
    return render_base_template("my_articles.html", articles=articles)

@articles_bp.route('/<int:article_id>')
@approve_required
def article_details(article_id):
    if not ac.is_author(article_id):
        return Response.error_response(message = "You are not an author of this article").to_dict()

    response = ac.get_article_data(article_id)

    if not response.success:
        return response.to_dict()

    article = response.data["article"]

    data = response.to_dict()

    if article.status.stat == ArticleStatusEnum.Submitted:
        tab_content = render_base_template("author_tabs/default_tab.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Accepted:
        tab_content = render_base_template("author_tabs/default_tab.html", article=article)
    elif article.status.stat == ArticleStatusEnum.InReview:
        tab_content = render_base_template("author_tabs/default_tab.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Reviewed:
        tab_content = render_base_template("author_tabs/default_tab.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        tab_content = render_base_template("author_tabs/default_tab.html", article=article)
    elif article.status.stat == ArticleStatusEnum.NeedsCorrections:
        tab_content = render_base_template("author_tabs/needs_corrections.html", article=article)
    else:
        return Response.error_response(message="Not found").to_dict()
    return render_template("article_author_base.html", tab_content=tab_content, article=article, data=data)



def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file(file: FileStorage, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(file.filename)
    tex_path = os.path.join(folder, filename)
    file.save(tex_path)
    return tex_path

@articles_bp.route('/upload-form')
@approve_required
def upload_form():
    editors = ac.get_available_editors()
    return render_template('uploading_article.html', editors = editors)

@articles_bp.route('/upload', methods=['POST'])
@approve_required
def upload_file():
    title = request.form.get('title')
    editor = request.form.get('editor')

    if not title:
        return Response.error_response(message='Title cannot be empty').to_dict()
    if not editor:
        return Response.error_response(message='Editor must be selected').to_dict()

    try:
        editor = int(editor)
    except (ValueError, TypeError) as e:
        log_err(get_function(), e)
        return Response.error_response(message='Invalid editor ID').to_dict()

    response = ac.is_valid_editor(editor)
    if not response.success:
        return response.to_dict()
    if 'file' not in request.files:
        return Response.error_response(message='Nie przesłano pliku').to_dict()

    file = request.files['file']
    if not file.filename:
        return Response.error_response(message='No file selected').to_dict()

    tex_path=handle_file(file, ec.getDocFilesDir())
    return ac.upload_file(title, editor, tex_path).to_dict()


@articles_bp.route('/uploads/<filename>')
@approve_required
def uploaded_file(filename):
    ret=ac.get_uploaded_file(filename)
    if ret.success:
        return ret.data
    return ret.to_dict()


@articles_bp.route('/generate-preview', methods=['POST'])
@approve_required
def generate_preview():
    if 'file' not in request.files:
        return Response.error_response(message='Nie przesłano pliku').to_dict()

    file = request.files['file']
    if not file.filename.endswith('.tex'):
        return Response.error_response(message="Nieprawidłowy format pliku").to_dict()

    tex_path=handle_file(file, ec.getTempDir())
    response = ac.generate_preview(tex_path)
    if response.success:
        return response.data
    return response.to_dict()


@articles_bp.route('/temp-preview/<filename>')
@approve_required
def temp_preview(filename):
    ret=ac.temp_preview(filename)
    if isinstance(ret, Response):
        return ret.to_dict()
    return ret
