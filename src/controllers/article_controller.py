import os
import subprocess
from typing import Any
import services.user as au
import services.review as rs
import services.article as aq
from flask import send_from_directory
from models.utils.Response import Response
from models.utils.decors import log_if_error
from db.db_base import log_activity, log_err
from models.utils.EnvConsts import envConsts as ec
from models.utils.MessageException import MessageException
from models.article.Article import Article, ArticleStatusEnum


def get_available_editors() -> dict[int, str]:
    return aq.get_available_editors()

def get_available_reviewers(article_id: int) -> dict[int, str]:
    return aq.get_available_reviewers(article_id)

def is_author(article_id: int) -> bool:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article:
            log_activity(False, {'err': f'Autor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
            return False
        
        return int(article.author_id) == int(user.get_id())
    except Exception as e:
        log_err(e)
        return False

def is_valid_editor(editor_id: int) -> Response:
    user = au.get_curr_user_or_err()
    if editor_id == user.id:
        return Response.error_response(message="An author cannot assign themselves as an editor.")
    elif not au.get_user(editor_id):
        return Response.error_response(message="Editor does not exist.")
    else:
        return Response.success_response()

def is_editor(article_id: int) -> bool:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article or not article.editor_id:
            log_activity(False, {'err': f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
            return False
        
        return int(article.editor_id) == int(user.get_id())
    except Exception as e:
        print(e)
        log_err(e)
        return False

def is_reviewer(article_id: int, user_id: int) -> bool:
    try:
        review = rs.get_review(article_id, user_id)

        if review:
            return True
        
        log_activity(False, {'err': f'Reviewer {user_id} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
        return False
    except Exception as e:
        log_err(e)
        return False
    
def is_reviewer_of_review(review_id: int) -> bool:
    try:
        user = au.get_curr_user_or_err()
        review = rs.get_review_by_id(review_id)
        if not review:
            log_activity(False, {'err': f'Reviewer {user.get_id()} usiłował uzyskać dostęp do nieisteniejącego review o id: {review_id}'})
            return False
        if int(review.reviewer_id) == int(user.get_id()):
            return True
        log_activity(False, {'err': f'Reviewer {user.get_id()} usiłował uzyskać dostęp do review o id: {review_id}'})
        return False
    except Exception as e:
        log_err(e)
        return False

def get_all_articles_by_editor() -> list[Article]:
    user=au.get_curr_user_or_err()
    return aq.get_all_articles_by_editor_id(int(user.get_id()))

def get_my_articles() -> list[Article]:
    user=au.get_curr_user_or_err()
    return aq.get_my_articles(int(user.get_id()))

@log_if_error
def get_article_data(article_id: int) -> Response:
    article = aq.get_article(article_id)
    if article is None:
        raise MessageException('Nie znaleziono artykułu', Exception(f'Article with id: {article_id} not found'))

    if article.content.startswith('/'):
        article.content = f'<br><embed src="{article.content}" width="800" height="500" type="application/pdf">'

    data: dict[str, Any] = {"article": article}

    if article.status.stat == ArticleStatusEnum.Accepted:
        data["reviewers"] = aq.get_available_reviewers(article.id)
        data["assigned_reviewers"] = aq.get_assigned_reviewers(article.id)
        data["reviews"] = aq.get_assigned_reviews(article.id)

    elif article.status.stat == ArticleStatusEnum.InReview:
        data["reviews"] = aq.get_assigned_reviews(article.id)

    elif article.status.stat == ArticleStatusEnum.Reviewed:
        data["grouped_answers"] = aq.get_answers_as_editor(article.id)

    return Response.success_response(data=data)

@log_if_error
def set_article_status(article_id: int, status: ArticleStatusEnum) -> Response:
    article = aq.get_article(article_id)
    if article is None:
        raise MessageException('Article not found')
    aq.update_article_status(article, status)
    return Response.success_response()

@log_if_error
def add_round(article_id: int) -> Response:
    article = aq.get_article(article_id)
    if article is None:
        raise MessageException('Article not found')

    # Sprawdzanie, czy artykuł spełnia wymagane statusy
    if article.status.stat not in {ArticleStatusEnum.Accepted, ArticleStatusEnum.Reviewed}:
        raise MessageException('Round cannot be added')

    new_round_number = len(article.rounds) + 1
    aq.create_round(article_id=article_id, round_number=new_round_number)
    return Response.success_response(message=f'Round {new_round_number} added successfully')

@log_if_error
def assign_reviewers(article_id: int, assigned_reviewers: list[str], deadline_confirm: str, deadline_submit: str) -> Response:
    if not assigned_reviewers:
        raise MessageException('No reviewers assigned')
    
    article = aq.get_article(article_id)
    if not article:
        log_activity(False, {'err': f'Editor attepted to set reviewers to a non-existing article {article_id}.'})
        return Response.error_response(message = f"Article {article_id} does not exist")

    assigned_reviewers_ids = [int(rid) for rid in assigned_reviewers]

    if article.editor_id in assigned_reviewers_ids:
        log_activity(False, {'err': f'Editor attempted to assign editor {article.editor_id} to the article {article_id}.'})
        return Response.error_response(message = f"Reviewer cannot be assigned to the article.")
    
    if article.author_id in assigned_reviewers_ids:
        log_activity(False, {'err': f'Editor attempted to assign author {article.author_id} to the article {article_id}.'})
        return Response.error_response(message = f"Reviewer cannot be assigned to the article.")

    last_round_number = aq.get_last_round_number(article_id)
    new_round_number = last_round_number + 1 if last_round_number else 1
    aq.create_round(article_id, new_round_number, deadline_confirm, deadline_submit)

    for reviewer_id in assigned_reviewers_ids:
        aq.add_reviewer_to_article(article_id, reviewer_id)

    update_status_result = set_article_status.__wrapped__(article_id, ArticleStatusEnum.InReview)
    if not update_status_result.success:
        raise MessageException(f'Failed to update article status to {ArticleStatusEnum.InReview.value}.')
    return Response.success_response()

@log_if_error
def set_review_status(review_id: int, status: str) -> Response:
    review = rs.get_review_by_id(review_id)
    if review is None:
        raise MessageException('Review not found')

    result = rs.update_review_status(review_id, status)
    if not result:
        raise MessageException('Review status not updated')

    return Response.success_response()

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
        raise MessageException(str(e))

@log_if_error
def upload_file(title: str, editor_id: int, tex_path: str) -> Response:
    # TODO: check if the function handles all possibilities
    upload_folder=os.path.dirname(tex_path)
    filename=os.path.basename(tex_path)
    # Konwersja LaTeX do PDF
    if filename.endswith('.tex'):
        conversion_success = convert_tex_to_pdf(tex_path, upload_folder)
        if not conversion_success:
            raise MessageException('Error converting LaTeX to PDF')

    # file_url=f"/articles/uploads/{filename}"
    file_url = f"/articles/uploads/{filename.replace('.tex', '.pdf') if filename.endswith('.tex') else filename}"

    aq.create_article(title, file_url, editor_id)
    return Response.success_response(
        message=f"File {filename} uploaded successfully",
        data={"pdf_url": file_url}
    )

@log_if_error
def __get_file(folder: str, filename: str) -> Response:
    file_path = os.path.join(folder, filename)
    if os.path.exists(file_path):
        return Response.success_response(send_from_directory(folder, filename))
    raise MessageException('Plik nie istnieje')

@log_if_error
def get_uploaded_file(filename: str) -> Response:
    return __get_file.__wrapped__(ec.getDocFilesDir(), filename)

@log_if_error
def generate_preview(tex_path: str) -> Response:
    temp_folder=os.path.dirname(tex_path)
    filename=os.path.basename(tex_path)
    conversion_success = convert_tex_to_pdf(tex_path, temp_folder)
    if conversion_success:
        return Response.success_response(data={"pdf_url": f"/articles/temp-preview/{filename.replace('.tex', '.pdf')}"})
    raise MessageException('Błąd generowania PDF')

@log_if_error
def temp_preview(filename: str) -> Response:
    return __get_file.__wrapped__(ec.getTempDir(), filename)
