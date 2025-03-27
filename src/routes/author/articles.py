import os
from decors import approve_required
from werkzeug.utils import secure_filename
from models.utils.Response import Response
import controllers.article_controller as ac
from werkzeug.datastructures import FileStorage
from models.utils.consts import ALLOWED_EXTENSIONS
from flask import request, Blueprint, render_template, jsonify
from models.utils.utils import get_temp_folder, get_upload_folder
from latex.latex_service import LatexService

articles_bp = Blueprint("articles", __name__)

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
    return render_template('uploading_article.html')


@articles_bp.route('/upload', methods=['POST'])
@approve_required
def upload_file():
    title = request.form.get('title')
    editor = request.form.get('editor')

    if not title:
        return Response.error_response(message='Tytuł nie może być pusty').to_dict()
    if not editor:
        return Response.error_response(message='Edytor musi być wybrany').to_dict()

    if 'files' not in request.files:
        return Response.error_response(message='Nie przesłano plików').to_dict()

    files = request.files.getlist('files')
    if not files or all(not f.filename for f in files):
        return Response.error_response(message='Nie wybrano żadnych plików').to_dict()

    upload_folder = get_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)

    tex_file_path = None
    allowed_archives = ('.zip', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2')

    for file in files:
        filename = file.filename.lower()

        if filename.endswith(allowed_archives):
            extracted_tex = LatexService.extract_archive_and_find_tex(file, upload_folder)
            if extracted_tex:
                tex_file_path = extracted_tex
        else:
            saved_path = LatexService.save_file(file, upload_folder)
            if saved_path.endswith(".tex"):
                tex_file_path = saved_path

    if not tex_file_path:
        return Response.error_response(message='Nie znaleziono pliku .tex').to_dict()

    result = ac.upload_file(title, editor, tex_file_path)
    return result.to_dict()



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
    if 'files' not in request.files:
        return Response.error_response(message='Nie przesłano plików').to_dict()

    files = request.files.getlist('files')
    if not files or all(not f.filename for f in files):
        return Response.error_response(message='Nie wybrano żadnych plików').to_dict()

    temp_folder = get_temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    archive_extensions = ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2')
    tex_path = None

    for file in files:
        filename = file.filename.lower()

        if filename.endswith(archive_extensions):
            extracted_tex = LatexService.extract_archive_and_find_tex(file, temp_folder)
            if extracted_tex:
                tex_path = extracted_tex

        elif filename.endswith('.tex'):
            saved_path = LatexService.save_file(file, temp_folder)
            if saved_path.endswith(".tex"):
                tex_path = saved_path

        else:
            LatexService.save_file(file, temp_folder)

    if not tex_path:
        return Response.error_response(message="Nie znaleziono pliku .tex").to_dict()

    response = LatexService.generate_preview(tex_path)
    return response.data if response.success else response.to_dict()




@articles_bp.route('/temp-preview/<filename>')
@approve_required
def temp_preview(filename):
    response = LatexService.get_temp_preview(filename)

    if not response.success:
        return jsonify(response.to_dict()), 400

    return response.data

