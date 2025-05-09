import os
import subprocess
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import Any
import services.user as au
import services.article as aq
import controllers.user_controller as uc
from flask import send_from_directory
from models.utils.Response import Response
from models.utils.decors import log_if_error
from db.db_base import db, log_activity
from models.utils.EnvConsts import envConsts as ec
from models.utils.MessageException import MessageException
from models.article.Article import ArticleStatusEnum


def get_available_editors() -> dict[int, str]:
    return aq.get_available_editors()

def get_available_reviewers(article_id: int) -> dict[int, str]:
    return aq.get_available_reviewers(article_id)

def is_valid_editor(editor_id: int) -> Response:
    user = au.get_curr_user_or_err()
    if editor_id == user.id:
        return Response.error_response(message="An author cannot assign themselves as an editor.")
    elif not au.get_user(editor_id):
        return Response.error_response(message="Editor does not exist.")
    else:
        return Response.success_response()

def is_author(article_id: int) -> None:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article:
            raise MessageException(
                'You are not an author of this article.',
                Exception(f'Autor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
        if int(article.author_id) != int(user.get_id()):
            raise MessageException(
                'You are not an author of this article.',
                Exception(f'Autor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
    except Exception as e:
        raise MessageException.from_exception(e, 'You are not an author of this article.')

def is_editor(article_id: int) -> None:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article or not article.editor_id:
            raise MessageException(
                'You are not an editor of this article.',
                Exception(f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
        
        if int(article.editor_id) != int(user.get_id()):
            raise MessageException(
                'You are not an author of this article.',
                Exception(f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
    except Exception as e:
        raise MessageException.from_exception(e, 'You are not an editor of this article.')

@log_if_error
def get_my_articles() -> Response:
    user=au.get_curr_user_or_err()
    return Response.success_response(data = aq.get_my_articles(int(user.get_id())))

@log_if_error
def get_all_articles_by_editor() -> Response:
    user_id = au.get_curr_user_or_err().get_id()
    articles = aq.get_all_articles_by_editor_id(int(user_id))
    return Response.success_response(data=articles)

@log_if_error
def get_article_data_as_editor(article_id: int) -> Response:
    is_editor(article_id)
    return get_article_data(article_id)

@log_if_error
def get_article_data_as_author(article_id: int) -> Response:
    is_author(article_id)
    return get_article_data(article_id)

def get_article_data(article_id: int) -> Response:
    article = aq.get_article(article_id)
    latest_round = aq.get_latest_round(article_id)
    if not article or not latest_round:
        raise MessageException('Nie znaleziono artykułu', Exception(f'Article with id: {article_id} not found'))

    article_content = latest_round.article_content
    if article_content.startswith('/'):
        article_content = f'<br><embed src="{f"/articles/uploads/{article.id}/{latest_round.round_number}/{article_content}"}" width="800" height="500" type="application/pdf">'

    data: dict[str, Any] = {"article": article, "article_content": article_content}

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
def set_article_status_accept(article_id: int) -> Response:
    is_editor(article_id)
    return set_article_status(article_id, ArticleStatusEnum.Accepted)

@log_if_error
def set_article_status_reject(article_id: int) -> Response:
    is_editor(article_id)
    return set_article_status(article_id, ArticleStatusEnum.Rejected)

@log_if_error
def set_article_status_needs_corrections(article_id: int) -> Response:
    is_editor(article_id)
    return set_article_status(article_id, ArticleStatusEnum.NeedsCorrections)

def set_article_status(article_id: int, status: ArticleStatusEnum) -> Response:
    article = aq.get_article(article_id)
    if article is None:
        raise MessageException('Article not found')
    aq.update_article_status(article, status)
    return Response.success_response()

@log_if_error
def assign_reviewers(article_id: int, assigned_reviewers: list[str], assigned_emails: list[str], deadline_confirm: str, deadline_submit: str) -> Response:
    is_editor(article_id)

    if not assigned_reviewers and not assigned_emails:
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

    for reviewer_id in assigned_reviewers_ids:
        aq.add_reviewer_to_article(article_id, reviewer_id)

    failed_emails = []
    invited_ids = []
    for email in assigned_emails:
        try:
            # funcs: list[tuple[Callable[..., object], tuple[object, ...]]]=[(cos, (User_params.nick,))]
            # funcs.append((cos2, (User_params.nick,)))
            result = uc.invite_user(email)#, do_after_create=funcs)
            if result.success:
                invited_user_id = result.data["user_id"]
                invited_ids.append(invited_user_id)
                aq.add_reviewer_to_article(article_id, invited_user_id)
            else:
                failed_emails.append(email)
        except Exception as e:
            failed_emails.append(email)

    # Czy jakikolwiek recenzent został skutecznie przypisany?
    if not assigned_reviewers_ids and not invited_ids:
        return Response.error_response(message="No valid reviewers could be assigned.")
        
    aq.set_deadlines(article_id = article_id, deadline_confirm = deadline_confirm, deadline_submit = deadline_submit)

    update_status_result = set_article_status(article_id, ArticleStatusEnum.InReview)
    if not update_status_result.success:
        raise MessageException(f'Failed to update article status to {ArticleStatusEnum.InReview.value}.')
    
    if failed_emails:
        return Response.success_response(data={
            "warning": f"Some invitations failed: {', '.join(failed_emails)}"
        })

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

def handle_file(file: FileStorage, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(file.filename)
    tex_path = os.path.join(folder, filename)
    file.save(tex_path)
    return tex_path

@log_if_error
def upload_file(title: str, editor_id: int, file: FileStorage) -> Response:
    # TODO: check if the function handles all possibilities
    response = is_valid_editor(editor_id)
    upload_folder=ec.getDocFilesDir()

    result = aq.create_article(title, editor_id)
    if result:
        user = au.get_curr_user_or_err()
        article = aq.get_article_by_title(int(user.get_id()), title)
        if article:
            file_url = f"{upload_folder}/{article.id}/1/"
            tex_path=handle_file(file, file_url)
            filename=os.path.basename(tex_path)
            # Konwersja LaTeX do PDF
            if filename.endswith('.tex'):
                conversion_success = convert_tex_to_pdf(tex_path, file_url)
                if not conversion_success:
                    raise MessageException('Error converting LaTeX to PDF')

            filename=f'/{filename.replace('.tex', '.pdf')}'
            if aq.create_round(int(article.id), filename, 1):
                db.session.commit()
                return Response.success_response(
                    message=f"File {filename} uploaded successfully",
                    data={"pdf_url": file_url}
                )
    raise MessageException('Article not created')

    
@log_if_error
def upload_correction(article_id: int, file: FileStorage) -> Response:
    # TODO: check if the function handles all possibilities
    upload_folder=ec.getDocFilesDir()
    
    article = aq.get_article(article_id)

    if article:
        is_author(article_id)
        if article.status.stat != ArticleStatusEnum.NeedsCorrections:
            raise MessageException('Correction had already been uploaded.')

        round_number = len(article.rounds) + 1
        file_url = f"{upload_folder}/{article.id}/{round_number}/"
        tex_path=handle_file(file, file_url)
        filename=os.path.basename(tex_path)
        # Konwersja LaTeX do PDF
        if filename.endswith('.tex'):
            conversion_success = convert_tex_to_pdf(tex_path, file_url)
            if not conversion_success:
                raise MessageException('Error converting LaTeX to PDF')
                
        filename=f'/{filename.replace('.tex', '.pdf')}'
        if aq.create_round(article.id, filename, round_number):
            status = aq.__get_status_or_err(ArticleStatusEnum.Submitted)
            article.update_status(status)
            return Response.success_response(
                message=f"File {filename} uploaded successfully",
                data={"pdf_url": file_url}
            )
    raise MessageException('Correction not uploaded.')

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
def generate_preview(file: FileStorage) -> Response:
    tex_path=handle_file(file, ec.getTempDir())
    temp_folder=os.path.dirname(tex_path)
    filename=os.path.basename(tex_path)
    conversion_success = convert_tex_to_pdf(tex_path, temp_folder)
    if conversion_success:
        return Response.success_response(data={"pdf_url": f"/articles/temp-preview/{filename.replace('.tex', '.pdf')}"})
    raise MessageException('Błąd generowania PDF')

@log_if_error
def temp_preview(filename: str) -> Response:
    return __get_file.__wrapped__(ec.getTempDir(), filename)
