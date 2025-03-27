import os
import subprocess
from db.db_base import db
import services.user as au
import services.article as aq
from flask import send_from_directory
from models.utils.Response import Response
from models.article.Article import Article, ArticleStatusEnum
from models.utils.utils import get_temp_folder, get_upload_folder
from latex.latex_service import LatexService

def get_all_articles_by_editor() -> list[Article]:
    user=au.get_curr_user_or_err()
    return aq.get_all_articles_by_editor_id(int(user.get_id()))


def get_article_data(article_id: int) -> Response:
    article = aq.get_article(article_id)
    if not article:
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
            return Response.error_response("Article not found")

        result = article.update_status(status)
        if not result:
            return Response.error_response("Article status not updated")

        return Response.success_response()

    except Exception as err:
        return Response.error_response(str(err))
    
def add_round(article_id: int) -> Response:
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
    
def assign_reviewers(article_id: int, assigned_reviewers: list[str], deadline_confirm: str, deadline_submit: str) -> Response:
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


def upload_file(title: str, editor_id: str, tex_path: str) -> Response:
    # TODO: check if the function handles all possibilities
    try:
        upload_folder = os.path.dirname(tex_path)
        filename = os.path.basename(tex_path)

        if filename.endswith('.tex'):
            if not LatexService.convert_tex_to_pdf(tex_path, upload_folder):
                return Response.error_response(message="Error converting LaTeX to PDF")

        file_url = f"/articles/uploads/{filename.replace('.tex', '.pdf') if filename.endswith('.tex') else filename}"

        if aq.create_article(title, file_url, editor_id):
            return Response.success_response(
                message=f"File {filename} uploaded successfully",
                data={"pdf_url": file_url}
            )

        db.session.rollback()
        return Response.error_response(message='Article not created')

    except Exception as e:
        db.session.rollback()
        return Response.error_response(message=f"Server error: {str(e)}")

def generate_preview(tex_path: str) -> Response:
    return LatexService.generate_preview(tex_path)


def temp_preview(filename: str) -> Response:
    return LatexService.get_temp_preview(filename)


def get_uploaded_file(filename: str) -> Response:
    return LatexService.get_uploaded_file(filename)
