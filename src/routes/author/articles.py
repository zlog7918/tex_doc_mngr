import os
import subprocess
from models.db.db_base import db
from werkzeug.utils import secure_filename
from models.db.article.Article import Article
from models.db.usr.User import User, user_loader
from flask_login import login_required, current_user
from models.utils.utils import get_temp_folder, get_upload_folder
from flask import request, Blueprint, jsonify, render_template, send_from_directory, send_file
articles_bp = Blueprint("articles", __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'tex'}


@articles_bp.route('/upload-form')
@login_required
def upload_form():
    return render_template('uploading_article.html')


@articles_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Nie przesłano pliku"}), 400
        title = request.form.get('title')
        editor = request.form.get('editor')

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Brak wybranego pliku"}), 400

        upload_folder = get_upload_folder()
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        tex_path = os.path.join(upload_folder, filename)
        pdf_path = tex_path.replace('.tex', '.pdf')
        file.save(tex_path)

        # Konwersja LaTeX do PDF
        if filename.endswith('.tex'):
            try:
                subprocess.run(
                    ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
                     "-output-directory", get_upload_folder(), tex_path],
                    cwd=get_upload_folder(),
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                subprocess.run(
                    ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
                     "-output-directory", get_upload_folder(), tex_path],
                    cwd=get_upload_folder(),
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                if os.path.exists(pdf_path):
                    user: User=current_user
                    url=f"/articles/uploads/{filename.replace('.tex', '.pdf')}"
                    editor=user_loader(editor)
                    if editor is None:
                        return jsonify({"error": "Nie znany edytor"}), 500
                    db.session.add(Article(title=title, author_id=user.get__id(), content=url, status_id=1, editor_id=editor.get__id())) # TODO: change status_id
                    db.session.commit()
                    return jsonify({"message": f"Plik {pdf_path} zapisany", "pdf_url": url}), 200
                else:
                    return jsonify({"error": "Plik PDF nie został wygenerowany"}), 500

            except subprocess.CalledProcessError as e:
                return jsonify({"error": "Błąd podczas konwersji LaTeX na PDF"}), 500

        url=f"/articles/uploads/{filename}"
        user: User=current_user
        editor=user_loader(editor)
        if editor is None:
            return jsonify({"error": "Nie znany edytor"}), 500
        db.session.add(Article(title=title, author_id=user.get__id(), content=url, status_id=1, editor_id=editor.get__id())) # TODO: change status_id
        db.session.commit()
        return jsonify({"message": f"Plik {filename} został zapisany"}), 200

    except Exception as e:
        return jsonify({"error": f"Błąd serwera: {str(e)}"}), 500


@articles_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    upload_folder = get_upload_folder()
    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path):
        return send_from_directory(upload_folder, filename)
    else:
        return jsonify({"error": "Plik nie istnieje"}), 404


@articles_bp.route('/generate-preview', methods=['POST'])
@login_required
def generate_preview():
    if 'file' not in request.files:
        return jsonify({"error": "Nie przesłano pliku"}), 400

    file = request.files['file']
    if not file.filename.endswith('.tex'):
        return jsonify({"error": "Nieprawidłowy format pliku"}), 400

    temp_folder = get_temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    tex_path = os.path.join(temp_folder, filename)
    pdf_path = tex_path.replace('.tex', '.pdf')
    file.save(tex_path)

    try:
        subprocess.run(
            ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
             "-output-directory", get_temp_folder(), tex_path],
            cwd=get_temp_folder(),
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        subprocess.run(
            ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
             "-output-directory", get_temp_folder(), tex_path],
            cwd=get_temp_folder(),
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if os.path.exists(pdf_path):
            return jsonify({"pdf_url": f"/articles/temp-preview/{filename.replace('.tex', '.pdf')}"}), 200
        else:
            return jsonify({"error": "Błąd generowania PDF"}), 500

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Błąd podczas generowania podglądu"}), 500


@articles_bp.route('/temp-preview/<filename>')
@login_required
def temp_preview(filename):
    temp_folder = get_temp_folder()
    file_path = os.path.join(temp_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return jsonify({"error": "Podgląd nie istnieje"}), 404