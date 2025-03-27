import os
import services.user as au
import services.review as rs
import services.article as aq
from flask import send_from_directory
from models.utils.Response import Response
from models.utils.utils import get_function
from latex.latex_service import LatexService
from werkzeug.datastructures import FileStorage
from db.db_base import db, log_activity, log_err
from models.utils.EnvConsts import envConsts as ec
from models.article.Article import Article, ArticleStatusEnum

def get_available_editors() -> dict[int, str]:
    return aq.get_available_editors()

def get_available_reviewers(article_id: int) -> dict[int, str]:
    return aq.get_available_reviewers(article_id)

def is_valid_editor(editor_id: int) -> Response:
    user = au.get_curr_user_or_err()
    if editor_id == user.id:
        return Response.error_response(message="An author cannot assign themselves as an editor.")
    elif not au.user_loader(editor_id):
        return Response.error_response(message="Editor does not exist.")
    else:
        return Response.success_response()

def is_editor(article_id: int) -> bool:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article or not article.editor_id:
            log_activity(get_function(), False, {'err': f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
            return False
        
        return int(article.editor_id) == int(user.get_id())
    except Exception as e:
        log_err(get_function(), e)
        return False

def is_reviewer(article_id: int, user_id: int) -> bool:
    try:
        review = rs.get_review(article_id, user_id)

        if review:
            return True
        
        log_activity(get_function(), False, {'err': f'Reviewer {user_id} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
        return False
    except Exception as e:
        log_err(get_function(), e)
        return False
    
def is_reviewer_of_review(review_id: int):
    try:
        user = au.get_curr_user_or_err()
        review = rs.get_review_by_id(review_id)
        if not review:
            log_activity(get_function(), False, {'err': f'Reviewer {user.get_id()} usiłował uzyskać dostęp do nieisteniejącego review o id: {review_id}'})
            return False
        if int(review.reviewer_id) == int(user.get_id()):
            return True
        log_activity(get_function(), False, {'err': f'Reviewer {user.get_id()} usiłował uzyskać dostęp do review o id: {review_id}'})
        return False
    except Exception as e:
        log_err(get_function(), e)
        return False

def get_all_articles_by_editor() -> list[Article]:
    user=au.get_curr_user_or_err()
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

        result = aq.set_article_status(article, status)
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
        return Response.error_response(message = 'No reviewers assigned')
    
    try:
        article = aq.get_article(article_id)
        if not article:
            log_activity(get_function(), False, {'err': f'Editor attepted to set reviewers to a non-existing article {article_id}.'})
            return Response.error_response(message = f"Article {article_id} does not exist")

        assigned_reviewers_ids = [int(rid) for rid in assigned_reviewers]

        if article.editor_id in assigned_reviewers_ids:
            log_activity(get_function(), False, {'err': f'Editor attempted to assign editor {article.editor_id} to the article {article_id}.'})
            return Response.error_response(message = f"Reviewer cannot be assigned to the article.")
        
        if article.author_id in assigned_reviewers_ids:
            log_activity(get_function(), False, {'err': f'Editor attempted to assign author {article.author_id} to the article {article_id}.'})
            return Response.error_response(message = f"Reviewer cannot be assigned to the article.")

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
    
def set_review_status(review_id: int, status: str) -> Response:
    try:
        review = rs.get_review_by_id(review_id)
        if not review:
            return Response.error_response("Review not found")

        result = rs.update_review_status(review_id, status)
        if not result:
            return Response.error_response("Review status not updated")

        return Response.success_response()

    except Exception as err:
        return Response.error_response(str(err))


def upload_file(title: str, editor_id: int, files: list[FileStorage]) -> Response:
    upload_folder = ec.getDocFilesDir()
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
        return Response.error_response(message='Nie znaleziono pliku .tex')

    # TODO: check if the function handles all possibilities
    try:
        upload_folder = os.path.dirname(tex_file_path)
        filename = os.path.basename(tex_file_path)

        if filename.endswith('.tex'):
            if not LatexService.convert_tex_to_pdf(tex_file_path, upload_folder):
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

def generate_preview(files: list[FileStorage]) -> Response:
    
    temp_folder = ec.getTempDir()
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
        return Response.error_response(message="Nie znaleziono pliku .tex")

    return LatexService.generate_preview(tex_path)


def temp_preview(filename: str) -> Response:
    return LatexService.get_file(ec.getTempDir(), filename)


def get_uploaded_file(filename: str) -> Response:
    return LatexService.get_file(ec.getDocFilesDir(), filename)
