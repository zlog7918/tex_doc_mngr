from models.article.Article import Article, ArticleStatus, ArticleStatusEnum
from models.utils.utils import render_base_template
from flask_login import login_required, current_user
from flask import request, redirect, url_for, Blueprint, jsonify, render_template
from models.usr.User import User
import db.queries.article as aq

editor_articles_bp = Blueprint("editor_articles", __name__)

'''
Submitted - artykół przesłany przez autora - nowy lub poprawiony
Accepted - zweryfikownay przez edytora, gotowy do recenzji
In review - przesłany do recenzentów, oczekujący na recenzje
Reviewed - przesłane wszystkie recenzje/zakończył się czas na recenzje
Rejected - odrzucony
Needs Corrections - wymaga poprawek, czeka na poprawki autora
Final - artykół jest zakończony, nie wymaga poprawek, wersja końcowa
'''


@editor_articles_bp.route('/')
@login_required
def show_articles():
    try:
        user: User=current_user
        articles = Article.query.filter_by(editor_id=int(user.get_id())).all()
    except Exception as err:
        return str(err), 500
    return render_base_template("articles.html", articles=articles)


@editor_articles_bp.route('/<int:article_id>')
@login_required
def article_details(article_id):
    try:
        article = aq.get_article(article_id)
    except Exception as err:
        return str(err), 500
    if not article:
        return "Article not found", 404

    if article.content.startswith('/'):
        article.content=f'<br><embed src="{article.content}" width="800" height="500" type="application/pdf">'

    if article.status.stat == ArticleStatusEnum.Submitted:
        return render_base_template("article_submitted.html", article=article)
    elif article.status.stat == ArticleStatusEnum.Accepted:
        reviewers = aq.get_available_reviewers(article_id)
        assigned_reviewers = aq.get_assigned_reviewers(article_id)
        assigned_reviews = aq.get_assigned_reviews(article_id)
        tab_content = render_base_template("round_tabs/accepted.html", article=article, reviewers=reviewers, assigned_reviewers=assigned_reviewers, reviews=assigned_reviews)
    elif article.status.stat == ArticleStatusEnum.InReview:
        reviews = aq.get_assigned_reviews(article_id)
        tab_content = render_base_template("round_tabs/in_review.html", reviews=reviews)
    elif article.status.stat == ArticleStatusEnum.Reviewed:
        grouped_answers = aq.get_answers_as_editor(article_id)
        tab_content = render_template("round_tabs/reviewed.html", grouped_answers=grouped_answers)
    elif article.status.stat == ArticleStatusEnum.Rejected:
        return render_template("round_tabs/rejected.html")
    else:
        tab_content = "<p>No content available for this status.</p>"

    return render_template("article_round_base.html", article=article, tab_content=tab_content)


@editor_articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@login_required
def accept_article(article_id):
    try:
        article = aq.get_article(article_id)
        if not article:
            return "Article not found", 404

        # Zmiana statusu na 'Accepted'
        status_id=ArticleStatus.query.where(ArticleStatus.stat==ArticleStatusEnum.Accepted).first().id
        result = aq.update_article_status(article_id, status_id)
        if not result:
            return {"warning": "Article status not updated"}, 500

        return {"message": f"Article status updated to Accepted."}, 200

    except Exception as err:
        return {"error": str(err)}, 500


@editor_articles_bp.route('/<int:article_id>/add_round')
@login_required
def add_round(article_id):
    article = aq.get_article(article_id)
    if not article:
        return jsonify({"success": False}), 404

    # Sprawdzanie, czy artykuł spełnia wymagane statusy
    if article.status.stat not in {ArticleStatusEnum.Accepted, ArticleStatusEnum.InReview, ArticleStatusEnum.Reviewed}:
        return jsonify({"success": False}), 400

    # Dodawanie nowej rundy
    new_round_id = len(article.rounds) + 1
    new_round = {"id": new_round_id, "reviews": []}
    article.rounds.append(new_round)
    return jsonify({"success": True})


@editor_articles_bp.route('<int:article_id>/assign_reviewers/', methods=['POST'])
@login_required
def assign_reviewers(article_id):
    # Pobieranie wybranych recenzentów z formularza
    assigned_reviewers = request.form.get('assigned_reviewers[]')
    deadline_confirm = request.form.get('deadline_confirm')
    deadline_submit = request.form.get('deadline_submit')
    
    if not assigned_reviewers:
        return "No reviewers assigned.", 400
    
    try:
        assigned_reviewers_ids = [int(rid.strip()) for rid in assigned_reviewers.split(',')]
        last_round_number = aq.get_last_round_number(article_id)
        new_round_number = last_round_number + 1 if last_round_number else 1
        aq.create_round(article_id, new_round_number, deadline_confirm, deadline_submit)

        for reviewer_id in assigned_reviewers_ids:
            aq.add_reviewer_to_article(article_id, reviewer_id)

        update_status_result = aq.update_article_status(article_id, 3)
        if not update_status_result:
            return {"error": "Failed to update article status to 3."}, 500

        return redirect(url_for('editor_articles.article_details', article_id=article_id))
    except Exception as err:
        return str(err), 500


@editor_articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@login_required
def reject_article(article_id):
    result = aq.update_article_status(article_id, 5)
    if not result:
            return {"warning": "Article status not updated"}, 500
    return jsonify({"success": True})


@editor_articles_bp.route('/<int:article_id>/update_status', methods=['POST'])
@login_required
def update_article_status(article_id):
    try:
        article = aq.get_article(article_id)
        if not article:
            return {"error": "Article not found"}, 404

        current_status = article["status"].stat

        # Sprawdzenie obecnego statusu i zmiana
        if current_status == ArticleStatusEnum.Accepted:
            # Ustawienie statusu na "In review"
            result = aq.update_article_status(article_id, 3)
            if not result:
                return {"error": "Failed to update status to 'In review'"}, 500

            # Tworzenie nowej rundy recenzji
            new_round_id = len(article["rounds"]) + 1
            new_round = {"id": new_round_id, "reviews": []}
            article["rounds"].append(new_round)
            # save_article_rounds(article_id, article["rounds"])

            return {"message": "Status updated to 'In review' and new review round created"}, 200

        elif current_status == ArticleStatusEnum.InReview:
            # Sprawdzenie liczby przesłanych recenzji
            latest_round = article["rounds"][-1] if article["rounds"] else None
            if not latest_round:
                return {"error": "No active review round found"}, 400

            total_reviews = len(latest_round["reviews"])
            if total_reviews >= 3:  # Zakładamy, że wymagane są 3 recenzje
                result = aq.update_article_status(article_id, 4)
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
