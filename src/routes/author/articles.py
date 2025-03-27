from db.db_base import log_err
from decors import approve_required
from models.utils.Response import Response
from models.utils.utils import get_function
import controllers.article_controller as ac
from models.utils.consts import ALLOWED_EXTENSIONS
from flask import request, Blueprint, render_template, abort

articles_bp = Blueprint("articles", __name__)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    files = request.files.getlist('files')
    if not files or all(not f.filename for f in files):
        return Response.error_response(message='Nie wybrano żadnych plików').to_dict()

    return ac.upload_file(title, editor, files).to_dict()


@articles_bp.route('/uploads/<filename>')
@approve_required
def uploaded_file(filename: str):
    response = ac.get_uploaded_file(filename)
    if response.success:
        return response.data
    abort(404)


@articles_bp.route('/generate-preview', methods=['POST'])
@approve_required
def generate_preview():
    if 'files' not in request.files:
        return Response.error_response(message='Nie przesłano plików').to_dict()

    files = request.files.getlist('files')
    if not files or all(not f.filename for f in files):
        return Response.error_response(message='Nie wybrano żadnych plików').to_dict()

    response = ac.generate_preview(files)
    return response.data if response.success else response.to_dict()


@articles_bp.route('/temp-preview/<filename>')
@approve_required
def temp_preview(filename: str):
    response = ac.temp_preview(filename)
    if response.success:
        return response.data
    abort(404)
