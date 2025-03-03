import os
import subprocess
from db.db_base import db, log_activity, log_err
from models.article.Article import Article, ArticleStatusEnum
from models.usr.User import User
from models.utils.Response import Response
from models.utils.utils import get_function, get_temp_folder, get_upload_folder
from flask_login import current_user
from flask import send_from_directory
import db.queries.article as aq

def get_all_articles_by_editor() -> list[Article]:
    user: User=current_user
    return aq.get_all_articles_by_editor_id(int(user.get_id()))


def get_article_data(article_id: int) -> Response:
    article = aq.get_article(article_id)
    if not article:
        log_activity(get_function(), False, {'err': f'Article with id: {article_id} not found'})
        return Response.error_response(message='Nie znaleziono artykułu.')

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
            log_activity(get_function(), False, {'err': f'Article with id: {article_id} not found'})
            return Response.error_response("Article not found")

        result = article.update_status(status)
        if not result:
            return Response.error_response(f"Article status not updated to {status.value}")

        return Response.success_response()

    except Exception as e:
        log_err(get_function(), e)
        return Response.error_response(str(e))
    
def add_round(article_id: int) -> Response:
    article = aq.get_article(article_id)
    if not article:
        log_activity(get_function(), False, {'err': f'Article with id: {article_id} not found'})
        return Response.error_response(message = "Article not found")

    # Sprawdzanie, czy artykuł spełnia wymagane statusy
    if article.status.stat not in {ArticleStatusEnum.Accepted, ArticleStatusEnum.Reviewed}:
        log_activity(get_function(), False, {'err': f'Cannot add a new round to the article with id: {article_id} and status: {article.status.stat}'})
        return Response.error_response(message = "Round cannot be added")

    new_round_number = len(article.rounds) + 1
    result = aq.create_round(article_id=article_id, round_number=new_round_number)

    if result:
        return Response.success_response(message=f"Round {new_round_number} added successfully")
    else:
        return Response.error_response(message='Round was not created.')
    
def assign_reviewers(article_id: int, assigned_reviewers: list[str], deadline_confirm: str, deadline_submit: str) -> Response:
    if not assigned_reviewers:
        log_activity(get_function(), False, {'err': 'No reviewers assigned'})
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
            return update_status_result

        return Response.success_response()
    except Exception as e:
        log_err(get_function(), e)
        return Response.error_response(str(e))

def convert_tex_to_pdf(tex_path: str, output_dir: str) -> bool:
    try:
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "--shell-escape", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                cwd=output_dir,
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        return os.path.exists(tex_path.replace('.tex', '.pdf'))
    except subprocess.CalledProcessError as e:
        # TODO: log
        return False

def upload_file(title: str, editor: str, tex_path: str) -> Response:
    # TODO: check if the function handles all possibilities
    try:
        upload_folder=os.path.dirname(tex_path)
        filename=os.path.basename(tex_path)
        # Konwersja LaTeX do PDF
        if filename.endswith('.tex'):
            conversion_success = convert_tex_to_pdf(tex_path, upload_folder)
            if not conversion_success:
                return Response.error_response(message="Error converting LaTeX to PDF")

        file_url = f"/articles/uploads/{filename.replace('.tex', '.pdf') if filename.endswith('.tex') else filename}"

        if aq.create_article(title, file_url, editor):
            return Response.success_response(
                message=f"File {filename} uploaded successfully",
                data={"pdf_url": file_url}
            )
        else:
            db.session.rollback()
            return Response.error_response(message='Article not created')

    except Exception as e:
        # TODO: log
        print('Exception')
        db.session.rollback()
        return Response.error_response(message=f"Server error: {str(e)}")

def get_file(folder: str, filename: str) -> Response:
    file_path = os.path.join(folder, filename)
    if os.path.exists(file_path):
        return Response.success_response(send_from_directory(folder, filename))
    else:
        return Response.error_response(message="Plik nie istnieje")

def get_uploaded_file(filename: str) -> Response:
    return get_file(get_upload_folder(), filename)

def generate_preview(tex_path: str) -> Response:
    temp_folder=os.path.dirname(tex_path)
    filename=os.path.basename(tex_path)
    try:
        conversion_success = convert_tex_to_pdf(tex_path, temp_folder)
        if conversion_success:
            return Response.success_response(data={"pdf_url": f"/articles/temp-preview/{filename.replace('.tex', '.pdf')}"})
        else:
            return Response.error_response(message="Błąd generowania PDF")
    except subprocess.CalledProcessError as e:
        # TODO: log
        return Response.error_response(message="Błąd podczas generowania podglądu")

def temp_preview(filename: str) -> Response:
    return Response.success_response(data = get_file(get_temp_folder(), filename))
