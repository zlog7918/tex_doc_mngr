import os
from werkzeug.utils import secure_filename
from models.utils.Response import Response
import controllers.article_controller as ac
from werkzeug.datastructures import FileStorage
from models.utils.decors import approve_required
from models.utils.consts import ALLOWED_EXTENSIONS
from flask import request, Blueprint, render_template
from models.utils.utils import get_temp_folder, get_upload_folder

articles_bp = Blueprint("articles", __name__)

# I leave it here, but commented becouse it's not used anywhere
# def allowed_file(filename: str) -> bool:
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def __handle_file(file: FileStorage, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename('' if file.filename is None else file.filename)
    tex_path = os.path.join(folder, filename)
    file.save(tex_path)
    return tex_path

@articles_bp.route('/upload-form')
@approve_required
def upload_form():
    return render_template('uploading_article.html')


@articles_bp.route('/upload', methods=['POST'])
@approve_required
def upload_file():
    title = request.form.get('title')
    editor = request.form.get('editor')
    if 'file' not in request.files:
        return Response.error_response(message='Nie przesłano pliku').to_dict()

    file = request.files['file']
    if not file.filename:
        return Response.error_response(message='No file selected').to_dict()

    tex_path=__handle_file(file, get_upload_folder())
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
    if not file.filename:
        return Response.error_response(message='No file selected').to_dict()
    if not file.filename.endswith('.tex'):
        return Response.error_response(message="Nieprawidłowy format pliku").to_dict()

    tex_path=__handle_file(file, get_temp_folder())
    response = ac.generate_preview(tex_path)
    if response.success:
        return response.data
    return response.to_dict()


@articles_bp.route('/temp-preview/<filename>')
@approve_required
def temp_preview(filename):
    ret=ac.temp_preview(filename)
    if ret.success:
        return ret.data
    return ret.to_dict()
