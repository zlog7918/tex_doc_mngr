from classes.usr.User import User, user_loader
from classes.article import Article
from classes.db.DBQ_Articles import DBQ_Articles
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from flask import request, redirect, url_for, Blueprint, jsonify, render_template, send_from_directory, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import subprocess
import tempfile
import shutil
from classes.utils.utils import get_temp_folder, get_upload_folder

articles_bp = Blueprint("articles", __name__, template_folder="templates")

'''
Submitted - artykół przesłany przez autora - nowy lub poprawiony
Accepted - zweryfikownay przez edytora, gotowy do recenzji
In review - przesłany do recenzentów, oczekujący na recenzje
Reviewed - przesłane wszystkie recenzje/zakończył się czas na recenzje
Rejected - odrzucony
Needs Corrections - wymaga poprawek, czeka na poprawki autora
Final - artykół jest zakończony, nie wymaga poprawek, wersja końcowa
'''


@articles_bp.route('/')
@login_required
def show_articles():
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        articles = db.get_articles_as_editor(current_user.get__id())
    except Exception as err:
        return str(err), 500
    return render_template("articles.html", articles=articles)



@articles_bp.route('/<int:article_id>')
@login_required
def article_details(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        article = db.get_article(article_id)
    except Exception as err:
        return str(err), 500
    if not article:
        return "Article not found", 404

    if article.content.startswith('/'):
        article.content=f'<br><embed src="{article.content}" width="800" height="500" type="application/pdf">'

    if article.status == "Submitted":
        return render_template("article_submitted.html", article=article)
    elif article.status == "Accepted":
        reviewers = db.get_available_reviewers(article_id)
        assigned_reviewers = db.get_assigned_reviewers(article_id)
        assigned_reviews = db.get_assigned_reviews(article_id)
        tab_content = render_template("round_tabs/accepted.html", article=article, reviewers=reviewers, assigned_reviewers=assigned_reviewers, reviews=assigned_reviews)
    elif article.status == "In review":
        reviews_remaining = 3
        if article.rounds:
            reviews_remaining = 3 - len(article["rounds"][-1]["reviews"]) if article["rounds"] else 3
        tab_content = render_template("round_tabs/in_review.html", article=article, reviews_remaining=reviews_remaining)
    elif article.status == "Reviewed":
        tab_content = render_template("round_tabs/reviewed.html", article=article)
    elif article.status == "Rejected":
        return render_template("round_tabs/rejected.html")
    else:
        tab_content = "<p>No content available for this status.</p>"

    return render_template("article_round_base.html", article=article, tab_content=tab_content)


@articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@login_required
def accept_article(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        article = db.get_article(article_id)
        if not article:
            return "Article not found", 404

        # Zmiana statusu na 'Accepted'
        result = db.update_article_status(article_id, 2)
        if not result:
            return {"warning": "Article status not updated"}, 500

        return {"message": f"Article status updated to Accepted."}, 200

    except Exception as err:
        return {"error": str(err)}, 500


@articles_bp.route('/<int:article_id>/add_round', methods=['POST'])
@login_required
def add_round(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    article = db.get_article(article_id)
    if not article:
        return jsonify({"success": False}), 404

    # Sprawdzanie, czy artykuł spełnia wymagane statusy
    if article.status not in ["Accepted", "In review", "Reviewed"]:
        return jsonify({"success": False}), 400

    # Dodawanie nowej rundy
    new_round_id = len(article.rounds) + 1
    new_round = {"id": new_round_id, "reviews": []}
    article.rounds.append(new_round)
    return jsonify({"success": True})

@articles_bp.route('<int:article_id>/assign_reviewers/', methods=['POST'])
@login_required
def assign_reviewers(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)

    # Pobieranie wybranych recenzentów z formularza
    assigned_reviewers = request.form.get('assigned_reviewers[]')
    deadline_confirm = request.form.get('deadline_confirm')
    deadline_submit = request.form.get('deadline_submit')
    
    if not assigned_reviewers:
        return "No reviewers assigned.", 400
    
    try:
        assigned_reviewers_ids = [int(rid.strip()) for rid in assigned_reviewers.split(',')]
        last_round_number = db.get_last_round_number(article_id)
        new_round_number = last_round_number + 1 if last_round_number else 1
        db.create_round(article_id, new_round_number, deadline_confirm, deadline_submit)

        for reviewer_id in assigned_reviewers_ids:
            db.add_reviewer_to_article(article_id, reviewer_id)

        update_status_result = db.update_article_status(article_id, 3)
        if not update_status_result:
            return {"error": "Failed to update article status to 3."}, 500
                    
        return redirect(url_for('articles.article_details', article_id=article_id))
    except Exception as err:
        return str(err), 500


@articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@login_required
def reject_article(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    result = db.update_article_status(article_id, 5)
    if not result:
            return {"warning": "Article status not updated"}, 500
    return jsonify({"success": True})


@articles_bp.route('/<int:article_id>/update_status', methods=['POST'])
@login_required
def update_article_status(article_id):
    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
    try:
        article = db.get_article(article_id)
        if not article:
            return {"error": "Article not found"}, 404

        current_status = article["status"]

        # Sprawdzenie obecnego statusu i zmiana
        if current_status == "Accepted":
            # Ustawienie statusu na "In review"
            result = db.update_article_status(article_id, 3)
            if not result:
                return {"error": "Failed to update status to 'In review'"}, 500

            # Tworzenie nowej rundy recenzji
            new_round_id = len(article["rounds"]) + 1
            new_round = {"id": new_round_id, "reviews": []}
            article["rounds"].append(new_round)
            db.save_article_rounds(article_id, article["rounds"])

            return {"message": "Status updated to 'In review' and new review round created"}, 200

        elif current_status == "In review":
            # Sprawdzenie liczby przesłanych recenzji
            latest_round = article["rounds"][-1] if article["rounds"] else None
            if not latest_round:
                return {"error": "No active review round found"}, 400

            total_reviews = len(latest_round["reviews"])
            if total_reviews >= 3:  # Zakładamy, że wymagane są 3 recenzje
                result = db.update_article_status(article_id, 4)
                if result:
                    return {"message": "All reviews submitted. Status updated to 'Reviewed'"}, 200
                else:
                    return {"error": "Failed to update status to 'Reviewed'"}, 500
            else:
                remaining = 3 - total_reviews
                return {"message": f"Waiting for {remaining} more reviews"}, 200

        else:
            return {"error": "Invalid status for update"}, 400

    except Exception as err:
        return {"error": str(err)}, 500


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
                    db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
                    url=f"/articles/uploads/{filename.replace('.tex', '.pdf')}"
                    user: User=current_user
                    editor=user_loader(editor)
                    if editor is None:
                        return jsonify({"error": "Nie znany edytor"}), 500
                    db.upload_article(user.get__id(), title, url, editor.get__id())
                    return jsonify({"message": f"Plik {pdf_path} zapisany", "pdf_url": url}), 200
                else:
                    return jsonify({"error": "Plik PDF nie został wygenerowany"}), 500

            except subprocess.CalledProcessError as e:
                return jsonify({"error": "Błąd podczas konwersji LaTeX na PDF"}), 500

        db: DBQ_Articles = DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Articles)
        url=f"/articles/uploads/{filename}"
        user: User=current_user
        editor=user_loader(editor)
        if editor is None:
            return jsonify({"error": "Nie znany edytor"}), 500
        db.upload_article(user.get__id(), title, url, editor.get__id())
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