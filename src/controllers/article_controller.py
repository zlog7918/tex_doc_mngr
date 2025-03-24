import os
import subprocess
from db.db_base import db, log_activity, log_err
from models.article.Review import Review
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import services.user as au
import services.article as aq
import services.review as rs
from flask import send_from_directory
from models.utils.Response import Response
from models.article.Article import Article, ArticleStatusEnum
from models.utils.utils import get_function, get_temp_folder, get_upload_folder

def is_editor(article_id: int) -> bool:
    try:
        user = au.get_curr_user_or_err()
        article = aq.get_article(article_id)
        if not article or not article.editor_id:
            log_activity(get_function(), False, {'err': f'Edytor {user.get_id()} usiłował uzyskać dostęp do artykułu o id: {article_id}'})
            return False
        
        return int(article.editor_id) == int(user.get_id())
    except Exception as e:
        print(e)
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
        print("error: " + str(e))
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
    latest_round = aq.get_latest_round(article_id)
    if not article or not latest_round:
        return Response.error_response(message='Nie znaleziono artykułu.')

    article_content = latest_round.article_content
    if article_content.startswith('/'):
        article_content = f'<br><embed src="{f"/articles/uploads/{article.id}/{latest_round.round_number}/{article_content}"}" width="800" height="500" type="application/pdf">'
        print(article_content)

    data = {"article": article, "article_content": article_content}

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
    
def assign_reviewers(article_id: int, assigned_reviewers: list[str], deadline_confirm: str, deadline_submit: str) -> Response:
    if not assigned_reviewers:
        return Response.error_response(message = 'No reviewers assigned')
    
    try:
        assigned_reviewers_ids = [int(rid.strip()) for rid in assigned_reviewers.split(',')]
        aq.set_deadlines(article_id = article_id, deadline_confirm = deadline_confirm, deadline_submit = deadline_submit)

        for reviewer_id in assigned_reviewers_ids:
            aq.add_reviewer_to_article(article_id, reviewer_id)

        update_status_result = set_article_status(article_id, ArticleStatusEnum.InReview)
        if not update_status_result.success:
            return Response.error_response(message = 'Failed to update article status to 3.')

        return Response.success_response()
    except Exception as err:
        return Response.error_response(str(err))
    
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

def handle_file(file: FileStorage, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(file.filename)
    tex_path = os.path.join(folder, filename)
    file.save(tex_path)
    return tex_path

def upload_file(title: str, editor: str, file: FileStorage) -> Response:
    # TODO: check if the function handles all possibilities
    try:
        upload_folder=get_upload_folder()

        result = aq.create_article(title, editor)
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
                        return Response.error_response(message="Error converting LaTeX to PDF")

                filename=f'/{filename.replace('.tex', '.pdf')}'
                if aq.create_round(int(article.id), filename, 1):
                    db.session.commit()
                    return Response.success_response(
                        message=f"File {filename} uploaded successfully",
                        data={"pdf_url": file_url}
                    )

        db.session.rollback()
        return Response.error_response(message='Article not created')

    except Exception as e:
        # TODO: log
        print('Exception')
        db.session.rollback()
        return Response.error_response(message=f"Server error: {str(e)}")
    
def upload_correction(article_id: int, file: FileStorage) -> Response:
    # TODO: check if the function handles all possibilities
    try:
        upload_folder=get_upload_folder()
        
        article = aq.get_article(article_id)

        if article:
            round_number = len(article.rounds) + 1
            file_url = f"{upload_folder}/{article.id}/{round_number}/"
            tex_path=handle_file(file, file_url)
            filename=os.path.basename(tex_path)
            # Konwersja LaTeX do PDF
            if filename.endswith('.tex'):
                conversion_success = convert_tex_to_pdf(tex_path, file_url)
                if not conversion_success:
                    return Response.error_response(message="Error converting LaTeX to PDF")
                    
            filename=f'/{filename.replace('.tex', '.pdf')}'
            if aq.create_round(article.id, filename, round_number):
                if article.update_status(ArticleStatusEnum.Submitted):
                    return Response.success_response(
                        message=f"File {filename} uploaded successfully",
                        data={"pdf_url": file_url}
                    )

        db.session.rollback()
        return Response.error_response(message='Correction not uploaded.')

    except Exception as e:
        db.session.rollback()
        log_err(get_function(), e)
        return Response.error_response(message=f"Server error: {str(e)}")

def get_file(folder: str, filename: str) -> Response:
    file_path = os.path.join(folder, filename)
    if os.path.exists(file_path):
        return Response.success_response(send_from_directory(folder, filename))
    else:
        return Response.error_response(message="Plik nie istnieje")

def get_uploaded_file(filename: str) -> Response:
    return get_file(get_upload_folder(), filename)

def generate_preview(file: FileStorage) -> Response:
    tex_path=handle_file(file, get_temp_folder())
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
