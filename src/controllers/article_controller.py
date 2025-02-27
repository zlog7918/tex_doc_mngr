import os
import subprocess
from db.db_base import db
from werkzeug.utils import secure_filename
from models.article.Article import ArticleStatusEnum
from models.usr.User import User
from models.utils.Response import Response
from models.utils.utils import get_temp_folder, get_upload_folder, render_base_template
from flask_login import current_user
from flask import request, send_from_directory, send_file
import db.queries.article as aq

def get_all_articles_by_editor():
    user: User=current_user
    return aq.get_all_articles_by_editor_id(int(user.get_id()))


def show_articles():
    try:
        user: User=current_user
        articles = aq.get_all_articles_by_editor_id(int(user.get_id()))
    except Exception as err:
        return Response.error_response(message=str(err)).to_dict()
    return render_base_template("articles.html", articles=articles)


def get_article_data(article_id) -> Response:
    article = aq.get_article(article_id)
    if not article:
        return Response.error_response()

    if article.content.startswith('/'):
        article.content = f'<br><embed src="{article.content}" width="800" height="500" type="application/pdf">'

    data = {"article": article}

    if article.status.stat == ArticleStatusEnum.Accepted:
        data["reviewers"] = aq.get_available_reviewers(article.id)
        data["assigned_reviewers"] = aq.get_assigned_reviewers(article.id)
        data["reviews"] = aq.get_assigned_reviews(article.id)

    elif article.status.stat == ArticleStatusEnum.InReview:
        data["reviews"] = aq.get_assigned_reviews(article.id)

    elif article.status.stat == ArticleStatusEnum.Reviewed:
        data["grouped_answers"] = aq.get_answers_as_editor(article.id)

    return Response.success_response(data=data)

def set_article_status(article_id: int, status: ArticleStatusEnum) -> Response:
    try:
        article = aq.get_article(article_id)
        if not article:
            return Response.error_response("Article not found")

        result = article.update_status(status)
        if not result:
            return Response.error_response("Article status not updated")

        return Response.success_response()

    except Exception as err:
        return Response.error_response(str(err))
    
def add_round(article_id) -> Response:
    article = aq.get_article(article_id)
    if not article:
        return Response.error_response(message = "Article not found")

    # Sprawdzanie, czy artykuł spełnia wymagane statusy
    if article.status.stat not in {ArticleStatusEnum.Accepted, ArticleStatusEnum.Reviewed}:
        return Response.error_response(message = "Round cannot be added")

    new_round_number = len(article.rounds) + 1
    result = aq.create_round(article_id=article_id, round_number=new_round_number)

    if result:
        return Response.success_response(message=f"Round {new_round_number} added successfully")
    else:
        return Response.error_response(message='Round was not created.')
    
def assign_reviewers(article_id, assigned_reviewers, deadline_confirm, deadline_submit) -> Response:
    if not assigned_reviewers:
        return Response.error_response(message = 'No reviewers assigned')
    
    try:
        assigned_reviewers_ids = [int(rid.strip()) for rid in assigned_reviewers.split(',')]
        last_round_number = aq.get_last_round_number(article_id)
        new_round_number = last_round_number + 1 if last_round_number else 1
        aq.create_round(article_id, new_round_number, deadline_confirm, deadline_submit)

        for reviewer_id in assigned_reviewers_ids:
            aq.add_reviewer_to_article(article_id, reviewer_id)

        update_status_result = set_article_status(article_id, ArticleStatusEnum.InReview)
        if not update_status_result.success:
            return Response.error_response(message = 'Failed to update article status to 3.')

        return Response.success_response()
    except Exception as err:
        return Response.error_response(str(err))

def upload_file(title: str, editor: str) -> Response:
    # TODO: check if the function handles all possibilities
    try:
        if 'file' not in request.files:
            return Response.error_response(message='Nie przesłano pliku')

        file = request.files['file']
        if not file.filename:
            return Response.error_response(message="No file selected")

        upload_folder = get_upload_folder()
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        tex_path = os.path.join(upload_folder, filename)
        # pdf_path = tex_path.replace('.tex', '.pdf')
        file.save(tex_path)

        # Konwersja LaTeX do PDF
        if filename.endswith('.tex'):
            conversion_success = convert_tex_to_pdf(tex_path, upload_folder)
            if not conversion_success:
                return Response.error_response(message="Error converting LaTeX to PDF")

            # try:
            #     subprocess.run(
            #         ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
            #          "-output-directory", get_upload_folder(), tex_path],
            #         cwd=get_upload_folder(),
            #         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            #     )
            #     subprocess.run(
            #         ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
            #          "-output-directory", get_upload_folder(), tex_path],
            #         cwd=get_upload_folder(),
            #         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            #     )

            #     if os.path.exists(pdf_path):
            #         user: User=current_user
            #         url=f"/articles/uploads/{filename.replace('.tex', '.pdf')}"
            #         editor=user_loader_by_nick(editor)
            #         if editor is None:
            #             return jsonify({"error": "Nie znany edytor"}), 500
            #         status=ArticleStatus.query.where(ArticleStatus.stat==ArticleStatusEnum.Submitted).first()
            #         db.session.add(Article(title=title, author_id=int(user.get_id()), content=url, status_id=status.id, editor_id=int(editor.get_id())))
            #         db.session.commit()
            #         return jsonify({"message": f"Plik {pdf_path} zapisany", "pdf_url": url}), 200
            #     else:
            #         return jsonify({"error": "Plik PDF nie został wygenerowany"}), 500

            # except subprocess.CalledProcessError as e:
            #     return jsonify({"error": "Błąd podczas konwersji LaTeX na PDF"}), 500


        # file_url=f"/articles/uploads/{filename}"
        file_url = f"/articles/uploads/{filename.replace('.tex', '.pdf') if filename.endswith('.tex') else filename}"

        if aq.create_article(title, file_url, editor):
            return Response.success_response(
                message=f"File {filename} uploaded successfully",
                data={"pdf_url": file_url}
            )
        else:
            print('Else')
            return Response.error_response(message='Article not created')

    except Exception as e:
        print('Exception')
        db.session.rollback()
        return Response.error_response(message=f"Server error: {str(e)}")

def convert_tex_to_pdf(tex_path: str, output_dir: str) -> bool:
    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "--shell-escape", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                cwd=output_dir,
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        return os.path.exists(tex_path.replace('.tex', '.pdf'))
    except subprocess.CalledProcessError:
        return False
    
def get_file(filename: str):
    upload_folder = get_upload_folder()
    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path):
        return send_from_directory(upload_folder, filename)
    else:
        return Response.error_response(message="Plik nie istnieje")
    
def generate_preview() -> Response:
    if 'file' not in request.files:
        return Response.error_response(message="Nie przesłano pliku")

    file = request.files['file']
    if not file.filename.endswith('.tex'):
        return Response.error_response(message="Nieprawidłowy format pliku")

    temp_folder = get_temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    tex_path = os.path.join(temp_folder, filename)
    pdf_path = tex_path.replace('.tex', '.pdf')
    file.save(tex_path)

    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "--shell-escape", "-interaction=nonstopmode",
                 "-output-directory", temp_folder, tex_path],
                cwd=temp_folder,
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        if os.path.exists(pdf_path):
            return Response.success_response(data={"pdf_url": f"/articles/temp-preview/{filename.replace('.tex', '.pdf')}"})
        else:
            return Response.error_response(message="Błąd generowania PDF")

    except subprocess.CalledProcessError:
        return Response.error_response(message="Błąd podczas generowania podglądu")

def temp_preview(filename):
    temp_folder = get_temp_folder()
    file_path = os.path.join(temp_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return Response.error_response(message="Podgląd nie istnieje.")