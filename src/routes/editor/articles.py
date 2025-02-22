from models.db.db_base import db
from models.db.usr.User import User
from models.db.article.Round import Round
from models.db.article.Review import Review
from models.db.article.Article import Article
from models.utils.utils import render_base_template
from flask_login import login_required, current_user
from models.db.article.Questions import Answer, Question
from flask import request, redirect, url_for, Blueprint, jsonify, render_template
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
        articles = Article.query.filter_by(editor_id=current_user.get__id()).all()
    except Exception as err:
        return str(err), 500
    return render_base_template("articles.html", articles=articles)


@editor_articles_bp.route('/<int:article_id>')
@login_required
def article_details(article_id):
    try:
        article = get_article(article_id)
    except Exception as err:
        return str(err), 500
    if not article:
        return "Article not found", 404

    if article.content.startswith('/'):
        article.content=f'<br><embed src="{article.content}" width="800" height="500" type="application/pdf">'

    if article.status.stat == "Submitted":
        return render_base_template("article_submitted.html", article=article)
    elif article.status.stat == "Accepted":
        reviewers = get_available_reviewers(article_id)
        assigned_reviewers = get_assigned_reviewers(article_id)
        assigned_reviews = get_assigned_reviews(article_id)
        tab_content = render_base_template("round_tabs/accepted.html", article=article, reviewers=reviewers, assigned_reviewers=assigned_reviewers, reviews=assigned_reviews)
    elif article.status.stat == "In review":
        reviews = get_assigned_reviews(article_id)
        tab_content = render_base_template("round_tabs/in_review.html", reviews=reviews)
    elif article.status.stat == "Reviewed":
        grouped_answers = get_answers_as_editor(article_id)
        tab_content = render_template("round_tabs/reviewed.html", grouped_answers=grouped_answers)
    elif article.status.stat == "Rejected":
        return render_template("round_tabs/rejected.html")
    else:
        tab_content = "<p>No content available for this status.</p>"

    return render_template("article_round_base.html", article=article, tab_content=tab_content)


@editor_articles_bp.route('/<int:article_id>/accept', methods=['POST'])
@login_required
def accept_article(article_id):
    try:
        article = get_article(article_id)
        if not article:
            return "Article not found", 404

        # Zmiana statusu na 'Accepted'
        result = update_article_status(article_id, 2)
        if not result:
            return {"warning": "Article status not updated"}, 500

        return {"message": f"Article status updated to Accepted."}, 200

    except Exception as err:
        return {"error": str(err)}, 500


@editor_articles_bp.route('/<int:article_id>/add_round', methods=['POST'])
@login_required
def add_round(article_id):
    article = get_article(article_id)
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
        last_round_number = get_last_round_number(article_id)
        new_round_number = last_round_number + 1 if last_round_number else 1
        create_round(article_id, new_round_number, deadline_confirm, deadline_submit)

        for reviewer_id in assigned_reviewers_ids:
            add_reviewer_to_article(article_id, reviewer_id)

        update_status_result = update_article_status(article_id, 3)
        if not update_status_result:
            return {"error": "Failed to update article status to 3."}, 500

        return redirect(url_for('editor_articles.article_details', article_id=article_id))
    except Exception as err:
        return str(err), 500


@editor_articles_bp.route('/<int:article_id>/reject', methods=['POST'])
@login_required
def reject_article(article_id):
    result = update_article_status(article_id, 5)
    if not result:
            return {"warning": "Article status not updated"}, 500
    return jsonify({"success": True})


@editor_articles_bp.route('/<int:article_id>/update_status', methods=['POST'])
@login_required
def update_article_status(article_id):
    try:
        article = get_article(article_id)
        if not article:
            return {"error": "Article not found"}, 404

        current_status = article["status"]

        # Sprawdzenie obecnego statusu i zmiana
        if current_status == "Accepted":
            # Ustawienie statusu na "In review"
            result = update_article_status(article_id, 3)
            if not result:
                return {"error": "Failed to update status to 'In review'"}, 500

            # Tworzenie nowej rundy recenzji
            new_round_id = len(article["rounds"]) + 1
            new_round = {"id": new_round_id, "reviews": []}
            article["rounds"].append(new_round)
            # save_article_rounds(article_id, article["rounds"])

            return {"message": "Status updated to 'In review' and new review round created"}, 200

        elif current_status == "In review":
            # Sprawdzenie liczby przesłanych recenzji
            latest_round = article["rounds"][-1] if article["rounds"] else None
            if not latest_round:
                return {"error": "No active review round found"}, 400

            total_reviews = len(latest_round["reviews"])
            if total_reviews >= 3:  # Zakładamy, że wymagane są 3 recenzje
                result = update_article_status(article_id, 4)
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




# TODO: move these functions to a different file
def get_article(article_id: int):
    return Article.query.get_or_404(article_id)


def get_available_reviewers(article_id: int) -> list[dict[int, str]]:
    try:
        # Pobieramy identyfikator najnowszej rundy dla danego artykułu
        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .subquery()
        )

        # Pobieramy identyfikatory recenzentów, którzy są już przypisani do tej rundy
        assigned_reviewers_subquery = (
            db.session.query(Review.reviewer_id)
            .filter(Review.round_id.in_(latest_round_subquery))
            .subquery()
        )

        # Pobieramy użytkowników, którzy NIE są przypisani do tej rundy
        reviewers = (
            db.session.query(User.id, User.nick)
            .filter(~User.id.in_(assigned_reviewers_subquery))  # NOT IN
            .all()
        )

        # Konwersja wyników na listę słowników
        return [{"id": row.id, "nick": row.nick} for row in reviewers]

    except Exception as err:
        print("error: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return []
    

def get_assigned_reviewers(article_id: int) -> list[dict[int, str]]:
    try:
        # Pobieramy identyfikator najnowszej rundy dla artykułu
        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .subquery()
        )

        # Pobieramy użytkowników, którzy są recenzentami w tej rundzie
        reviewers = (
            db.session.query(User.id, User.nick)
            .join(Review, Review.reviewer_id == User.id)
            .filter(Review.round_id.in_(latest_round_subquery))
            .all()
        )

        # Konwersja do listy słowników
        return [{"id": row.id, "nick": row.nick} for row in reviewers]

    except Exception as err:
        print("error: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return []


def get_assigned_reviews(article_id: int) -> list[Review]:
    try:
        # Pobieramy identyfikator najnowszej rundy dla artykułu
        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .subquery()
        )

        # Pobieramy recenzje przypisane do tej rundy
        reviews = (
            db.session.query(Review)
            .filter(Review.round_id.in_(latest_round_subquery))
            .all()
        )

        return reviews

    except Exception as err:
        print("error: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return []

from collections import defaultdict

def get_answers_as_editor(article_id: int) -> dict[str, list[dict]]:
    try:
        # Pobieramy identyfikator najnowszej rundy dla artykułu
        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .scalar_subquery()
        )

        # Pobieramy odpowiedzi z recenzji najnowszej rundy
        results = (
            db.session.query(User.nick, Question.question, Answer.answer)
            .join(Review, Review.reviewer_id == User.id)
            .join(Answer, Answer.review_id == Review.id)
            .join(Question, Question.id == Answer.question_id)
            .filter(Review.round_id == latest_round_subquery)
            .all()
        )

        # Grupowanie wyników po recenzencie
        grouped_answers = defaultdict(list)
        for nick, question, answer in results:
            grouped_answers[nick].append({"question": question, "answer": answer})

        return grouped_answers

    except Exception as err:
        print("error: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return {}

def update_article_status(article_id: int, status: int) -> bool:
    try:
        article = db.session.get(Article, article_id)
        if article:
            article.status_id = status
            db.session.commit()
            return True
        return False
    except Exception as err:
        print("exception:", str(err))
        # self.__log_activity(
        #     inspect.currentframe().f_code.co_name,
        #     False,
        #     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
        # )
        db.session.rollback()
        return False


def get_last_round_number(article_id: int) -> int:
    try:
        last_round = (
            db.session.query(Round.round_number)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .scalar()
        )
        return last_round if last_round is not None else 0
    except Exception as err:
        print("Error in get_last_round_number:", err)
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return 0


def create_round(article_id: int, round_number: int, deadline_confirm: str, deadline_submit: str) -> bool:
    try:
        new_round = Round(
            article_id=article_id,
            round_number=round_number,
            q_set_id=1,
            deadline_confirm=deadline_confirm,
            deadline_submit=deadline_submit
        )
        db.session.add(new_round)
        db.session.commit()
        return True
    except Exception as err:
        print("create:", str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        db.session.rollback()
        return False


def add_reviewer_to_article(article_id: int, reviewer_id: int) -> bool:
    try:
        round_id = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .scalar()
        )

        if round_id:
            new_review = Review(
                round_id=round_id,
                reviewer_id=reviewer_id,
                status="Pending confirmation"
            )
            db.session.add(new_review)
            db.session.commit()
            return True
        else:
            print("No round found for the given article_id:", article_id)
            return False

    except Exception as err:
        print("Assignment error:", str(err))
        # self.__log_activity(
        #     inspect.currentframe().f_code.co_name,
        #     False,
        #     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
        # )
        db.session.rollback()
        return False
