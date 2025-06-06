import os
import shutil
import subprocess
import zipfile
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import Any
from zoneinfo import ZoneInfo
import services.user_service as au
from db.db_base import log_activity
import services.article_service as aq
import services.question_service as sq
from . import question_controller as qc
from datetime import datetime, timedelta
from models.article import Questions as Q
from werkzeug.utils import secure_filename
from models.utils.Response import Response
from models.utils.utils import get_timestamp
from latex.latex_service import LatexService
from werkzeug.datastructures import FileStorage
from models.utils.EnvConsts import envConsts as ec
from models.article.Article import ArticleStatusEnum
from models.utils import utils as util, decors as decor
from models.utils.MessageException import MessageException


def get_available_editors() -> dict[int, str]:
    return aq.get_available_editors()

def get_available_reviewers(article_id: int) -> dict[int, str]:
    return aq.get_available_reviewers(article_id)

def _get_user_temp_dir() -> str:
    user_id = au.get_curr_user_or_err().get_id()
    user_temp_path = os.path.join(ec.getTempDir(), user_id)
    return user_temp_path

def is_valid_editor(editor_id: int) -> Response:
    user = au.get_curr_user_or_err()
    user0_id = au.get_usr0_or_err().id
    if editor_id == user.id or  user.id == user0_id:
        return Response.error_response(message="An author cannot assign themselves as an editor.")
    elif not au.get_user(editor_id):
        return Response.error_response(message="Editor does not exist.")
    return Response.success_response()

def is_author(article_id: int) -> None:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article:
            raise MessageException(
                'You are not an author of this article.',
                err=Exception(f'Autor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
        if int(article.author_id) != int(user.id):
            raise MessageException(
                'You are not an author of this article.',
                err=Exception(f'Autor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
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
                err=Exception(f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
        
        if int(article.editor_id) != user.id:
            raise MessageException(
                'You are not an author of this article.',
                err=Exception(f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}')
            )
    except Exception as e:
        raise MessageException.from_exception(e, 'You are not an editor of this article.')

@decor.log_if_error
def get_my_articles() -> Response:
    user=au.get_curr_user_or_err()
    return Response.success_response(data = aq.get_my_articles(user.id))

@decor.log_if_error
def get_all_articles_by_editor() -> Response:
    user_id = au.get_curr_user_or_err().id
    articles = aq.get_all_articles_by_editor_id(user_id)
    return Response.success_response(data=articles)

@decor.log_if_error
def get_article_data_as_editor(article_id: int) -> Response:
    is_editor(article_id)
    return get_article_data(article_id)

@decor.log_if_error
def get_article_data_as_author(article_id: int) -> Response:
    is_author(article_id)
    return get_article_data(article_id)

def get_article_data(article_id: int) -> Response:
    article = aq.get_article(article_id)
    if not article:
        raise MessageException('Nie znaleziono artykułu', Exception(f'Article with id: {article_id} not found'))
    latest_round = aq.get_latest_round(article)
    if not latest_round:
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

@decor.log_if_error
def set_article_status_accept(article_id: int) -> Response:
    is_editor(article_id)
    return set_article_status(article_id, ArticleStatusEnum.Accepted)

@decor.log_if_error
def set_article_status_reject(article_id: int) -> Response:
    is_editor(article_id)
    return set_article_status(article_id, ArticleStatusEnum.Rejected)

@decor.log_if_error
def set_article_status_needs_corrections(article_id: int) -> Response:
    is_editor(article_id)
    zip_latest_round(article_id)
    return set_article_status(article_id, ArticleStatusEnum.NeedsCorrections)

@decor.log_if_error
def set_article_status_final(article_id: int) -> Response:
    is_editor(article_id)
    return set_article_status(article_id, ArticleStatusEnum.Final)

def set_article_status(article_id: int, status: ArticleStatusEnum) -> Response:
    article = aq.get_article(article_id)
    if article is None:
        raise MessageException('Article not found')
    aq.update_article_status(article, status)
    return Response.success_response()

def zip_latest_round(article_id: int) -> Response:
    upload_folder=ec.getDocFilesDir()
    article = aq.get_article(article_id)

    if article:
        round_number = len(article.rounds)
        folder_path = f"{upload_folder}/{article.id}/{round_number}/"
        if not os.path.exists(folder_path):
            raise MessageException('Podany folder nie istnieje')

        zip_name = f"{article_id}_{round_number}.zip"
        output_zip_path = os.path.join(folder_path, zip_name)
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.aux', '.log', '.pdf', '.synctex.gz', '.zip')):
                    os.remove(os.path.join(root, file))
                elif file.startswith(('_minted',)):
                    os.remove(os.path.join(root, file))
            for dir_name in dirs:
                if dir_name.startswith("_minted"):
                    shutil.rmtree(os.path.join(root, dir_name))

        try:
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=folder_path)
                        zipf.write(file_path, arcname)
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if not file.endswith(('.zip',)):
                            os.remove(os.path.join(root, file))

        except Exception as e:
            print(e)
            raise MessageException.from_exception(e, 'Nie udało się utworzyć pliku ZIP')

    return Response.success_response()

@decor.log_if_error
def assign_reviewers(article_id: int, question_set: list[str], assigned_reviewers: list[str], deadline_confirm: str, deadline_submit: str, tz: str) -> Response:
    is_editor(article_id)
    lang_pkg=util.get_lang_pkg()

    if not assigned_reviewers:
        raise MessageException('No reviewers assigned')
    
    confirm_date = datetime.strptime(deadline_confirm, "%Y-%m-%d")
    submit_date = datetime.strptime(deadline_submit, "%Y-%m-%d")
    date = get_timestamp(ZoneInfo(tz)).date()

    min_date = date + timedelta(days=2)
    if confirm_date.date() < min_date:
        return Response.error_response(message=f"Confirmation deadline must be at least {min_date}.")

    if submit_date.date() < min_date:
        return Response.error_response(message=f"Submission deadline must be at least {min_date}.")

    if submit_date <= confirm_date:
        return Response.error_response(message="Submission deadline cannot be earlier than confirmation deadline.")

    article = aq.get_article(article_id)
    if not article:
        log_activity(False, {'err': f'Editor attepted to set reviewers to a non-existing article {article_id}.'})
        return Response.error_response(message = f"Article {article_id} does not exist")

    question_groups_ids = {int(qg_id) for qg_id in question_set}
    question_groups: list[Q.QuestionGroup]=[]
    for qg_id in question_groups_ids:
        qg=sq.get_question_group(qg_id)
        if qg is None:
            raise MessageException(lang_pkg.QuestionGroupNotFound.value)
        question_groups.append(qg)
    usr=au.get_curr_user_or_err()
    if any(not qc._does_user_has_access(usr, qg.user_id) for qg in question_groups):
        raise MessageException(lang_pkg.QuestionGroupNotFound.value, Exception(f'Illegal access attempt on guestion group'))

    assigned_reviewers_ids = {int(rid) for rid in assigned_reviewers}

    message=f"Reviewer cannot be assigned to the article."
    if article.editor_id in assigned_reviewers_ids:
        log_activity(False, {'err': f'Editor attempted to assign editor {article.editor_id} to the article {article_id}.'})
        return Response.error_response(message)
    
    if article.author_id in assigned_reviewers_ids:
        log_activity(False, {'err': f'Editor attempted to assign author {article.author_id} to the article {article_id}.'})
        return Response.error_response(message)
    
    usr0=au.get_usr0_or_err()
    if usr0.id in assigned_reviewers_ids:
        log_activity(False, {'err': f'Editor attempted to assign default user {usr0.id} to the article {article_id}.'})
        return Response.error_response(message)

    for reviewer_id in list(assigned_reviewers_ids):
        aq.add_reviewer_to_article(article_id, reviewer_id)
        
    aq.set_deadlines_and_qs(article_id = article_id, question_set = question_groups, deadline_confirm = deadline_confirm, deadline_submit = deadline_submit)

    aq.update_article_status(article, ArticleStatusEnum.InReview)
    return Response.success_response()

def _handle_files(url_start: str, dir_path: str, files: list[FileStorage], main_tex_name: str|None=None) -> str:
    lang_pkg=util.get_lang_pkg()
    dir_path=os.path.join(dir_path, '')
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    saved_paths: list[str] = []

    allowed_archives = ('.zip', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2')

    for file in files:
        filename = file.filename.lower() if file.filename else ''

        if filename.endswith(allowed_archives):
            extracted_tex_files = LatexService.extract_tex_files_from_archive(file, dir_path)
            saved_paths.extend(extracted_tex_files)
        else:
            saved_path = LatexService.save_file(file, dir_path)
            if saved_path.endswith(".tex"):
                saved_paths.append(saved_path)

    tex_file_path=None
    if main_tex_name:
        for path in saved_paths:
            if os.path.basename(path) == main_tex_name:
                tex_file_path = path
                break
    elif len(saved_paths) == 1:
        tex_file_path = saved_paths[0]
    elif len(saved_paths) > 1:
        raise MessageException('Nie wybrano głównego pliku', {
            "need_main_tex": True,
            "tex_files": [os.path.basename(p) for p in saved_paths]
        })

    if not tex_file_path:
        raise MessageException('Nie znaleziono pliku .tex')

    file=os.path.basename(tex_file_path)
    if not LatexService.convert_tex_to_pdf(tex_file_path, dir_path):
        raise MessageException(lang_pkg.LaTeXtoPDFconvertError.value)
    file_url = f"{url_start}/{file.replace('.tex', '.pdf')}"
    return file_url
    
@decor.log_if_error
def upload_correction(article_id: int, files: list[FileStorage], main_tex_name: str|None=None) -> Response:
    # TODO: check if the function handles all possibilities
    article = aq.get_article(article_id)
    if article is None:
        raise MessageException('Article not created')
    is_author(article_id)
    if article.status.stat != ArticleStatusEnum.NeedsCorrections:
        raise MessageException('Correction had already been uploaded.')

    round_number=len(article.rounds)+1
    sub_dir=f'{article.id}/{round_number}'
    prefix=f'/articles/uploads/{sub_dir}'
    file_url=_handle_files(prefix, f'{ec.getDocFilesDir()}/{sub_dir}', files, main_tex_name)

    filename=file_url.removeprefix(prefix)
    aq.create_round(article.id, filename, round_number)
    aq.update_article_status(article, ArticleStatusEnum.Submitted)
    log_activity(True, {
        'message': f'Uploaded files: {files} with "{main_tex_name}" as main successfully',
        'data': {'pdf_url': file_url}
    })
    return Response.success_response(
        message=f'File {filename} uploaded successfully',
        data={'pdf_url': file_url}
    )

@decor.log_if_error
def upload_file(title: str, editor_id: int, files: list[FileStorage], main_tex_name: str | None = None) -> Response:
    user = au.get_curr_user_or_err()

    if aq.article_exists_for_author(title, user.id):
        return Response.error_response(message="Masz już artykuł o tym tytule. Zmień tytuł i spróbuj ponownie.")

    is_valid_editor(editor_id)
    article = aq.create_article(title, editor_id)

    sub_dir = f'{article.id}/1'
    prefix = f'/articles/uploads/{sub_dir}'
    file_url = _handle_files(prefix, f'{ec.getDocFilesDir()}/{sub_dir}', files, main_tex_name)

    filename = file_url.removeprefix(prefix)
    aq.create_round(article.id, filename, 1)

    log_activity(True, {
        'message': f'Uploaded files: {files} with \"{main_tex_name}\" as main successfully',
        'data': {'pdf_url': file_url}
    })

    return Response.success_response(
        message=f'File {filename} uploaded successfully',
        data={'pdf_url': file_url}
    )


@decor.log_if_error
def generate_preview(files: list[FileStorage], main_tex_name: str | None = None) -> Response:
    user_temp_dir = _get_user_temp_dir()
    ret = _handle_files(f'/articles/temp-preview', user_temp_dir, files, main_tex_name)
    return Response.success_response(data={
        'pdf_url': ret
    })

@decor.log_if_error
def temp_preview(filename: str) -> Response:
    filename=secure_filename(filename)
    user_temp_dir=_get_user_temp_dir()
    return LatexService.get_file(user_temp_dir, filename)

@decor.log_if_error
def get_uploaded_file(article_id: int, round_num: int, filename: str) -> Response:
    return LatexService.get_file(f'{ec.getDocFilesDir()}/{article_id}/{round_num}', filename)
