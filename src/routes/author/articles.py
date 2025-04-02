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
    try:
        result = ac.upload_file(
            title=request.form.get('title'),
            editor=request.form.get('editor'),
            files=request.files.getlist('files'),
            main_tex_name=request.form.get("mainTex")
        )
        return result.to_dict()
    except Exception:
        return Response.error_response(message="Błąd wewnętrzny podczas przesyłania pliku").to_dict()

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
    try:
        response = ac.generate_preview(
            files=request.files.getlist('files'),
            main_tex_name=request.form.get("mainTex")
        )
        return response.data if response.success else response.to_dict()
    except Exception:
        return Response.error_response(message="Błąd wewnętrzny podczas generowania podglądu").to_dict()

@articles_bp.route('/temp-preview/<filename>')
@approve_required
def temp_preview(filename: str):
    response = ac.temp_preview(filename)
    if response.success:
        return response.data
    abort(404)
