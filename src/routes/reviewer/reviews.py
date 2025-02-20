from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.db.DB_Factory import DB_Factory, DB_QueriesOpt
from models.db.DBQ_Articles import DBQ_Articles
from flask_login import login_required, current_user
from models.models import QuestionSet, db
from models.models import Answer, Article, Question, QuestionA, QuestionSetQuestions, Review, Round

review_bp = Blueprint("review", __name__)


@review_bp.route("/")
@login_required
def list_reviewer_reviews():
    try:
        articles = get_articles_as_reviewer(current_user.get__id())
    except Exception as err:
        return str(err), 500
    return render_template("reviews.html", articles=articles)


@review_bp.route("/<int:article_id>", methods=["GET"])
@login_required
def article_details(article_id):
    try:
        article = get_article(article_id)
        review = get_review(article_id, current_user.get__id())
        if not review:
            return str("review not found"), 500

        if review.status == "Pending confirmation":
            return render_template("review_tabs/pending_confirmation.html", article=article, review_id=review.id)
        elif review.status == "Accepted by reviewer":
            questions = get_questions_by_article(article_id)

            if not questions:
                return "No questions found for the article.", 404

            for question in questions:
                if question['is_abc']:
                    answers = get_question_answers(question['id'])
                    question['answers'] = answers if answers else [{"id": 0, "answer": "No answers available"}]

            return render_template("review_tabs/review_form.html", review_id=review.id, questions=questions)
        else:
            return "Not implemented", 501
    except Exception as err:
        return str(err), 500


@review_bp.route("/<int:review_id>/accept", methods=["POST"])
@login_required
def accept_article(review_id):
    try:
        result = update_review_status(review_id, "Accepted by reviewer")
        if result:
            return {"message": "Accepted reviewing the article"}, 200
        else:
            return {"error": "Failed to accept the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500
    
@review_bp.route("/<int:review_id>/reject", methods=["POST"])
@login_required
def reject_article(review_id):
    try:
        result = update_review_status(review_id, "Rejected by reviewer")
        if result:
            return {"message": "Rejected reviewing the article"}, 200
        else:
            return {"error": "Failed to reject the review"}, 500
    except Exception as err:
        return {"error": str(err)}, 500
    
@review_bp.route('/<int:review_id>/submit_review', methods=['POST'])
@login_required
def submit_review(review_id):
    answers = {}

    if request.method != 'POST':
        flash("Invalid request method.", "error")
        return redirect(url_for("review.list_reviewer_reviews"))
    
    for question_id, answer in request.form.items():
        if question_id.startswith("question_"):
            question_id_int = int(question_id.split("_")[1])
            answers[question_id_int] = answer
    
    if save_review_answers(review_id, answers):
        # TODO: replace with observer
        check_reviews_and_update_article_status(review_id)

        return redirect(url_for("review.list_reviewer_reviews"))
    else:
        flash(f"Error submitting review", "error")
        return "Error submitting review.", 500


# TODO: Move to a different file
def get_article(article_id: int):
    return Article.query.get_or_404(article_id)


def get_review(article_id: int, reviewer_id: int) -> Review:
    try:
        review = (
            db.session.query(Review)
            .join(Round, Review.round_id == Round.id)
            .filter(Round.article_id == article_id, Review.reviewer_id == reviewer_id)
            .first()
        )

        return review

    except Exception as err:
        print("error get_review: " + str(err))
        return {}


def get_assigned_reviews(article_id: int) -> list[dict[int, str]]:
    try:
        # Pobieramy identyfikator najnowszej rundy dla danego artykułu
        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .subquery()
        )

        # Pobieramy przypisane recenzje dla danej rundy
        reviews = (
            db.session.query(Review)
            .filter(Review.round_id.in_(latest_round_subquery))
            .all()
        )

        # Konwersja wyników na listę obiektów Review
        return [{"review_id": review.id, "reviewer_id": review.reviewer_id} for review in reviews]

    except Exception as err:
        print("error: " + str(err))
        return []


def check_reviews_and_update_article_status(review_id: int):
    try:
        round_id = (
            db.session.query(Review.round_id)
            .filter(Review.id == review_id)
            .scalar()
        )

        if round_id is None:
            return

        statuses = (
            db.session.query(Review.status)
            .filter(Review.round_id == round_id)
            .all()
        )

        all_reviewed = all(status[0] == 'Reviewed' for status in statuses)
        print("all_reviewed is", all_reviewed)

        if all_reviewed:
            article_id = (
                db.session.query(Round.article_id)
                .filter(Round.id == round_id)
                .scalar()
            )
            if article_id:
                update_article_status(article_id, 4)

    except Exception as err:
        print("exception:", str(err))
        # self.__log_activity(
        #     inspect.currentframe().f_code.co_name,
        #     False,
            # {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
        # )


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


def get_articles_as_reviewer(reviewer_id: int) -> list[Article, int]:
    try:
        articles = (
            db.session.query(Article, Review.status)
            .join(Round, Round.article_id == Article.id)
            .join(Review, Review.round_id == Round.id)
            .filter(Review.reviewer_id == reviewer_id, Review.status.in_(['Pending confirmation', 'Accepted by reviewer']))
            .all()
        )

        # Konwersja do listy słowników
        return articles

    except Exception as err:
        print("error: " + str(err))
        return []


def post_review(review: Review) -> bool:
    try:
        # Dodajemy nową recenzję do bazy danych
        db.session.add(review)
        db.session.commit()
        return True
    except Exception as err:
        print("error: " + str(err))
        db.session.rollback()
        return False


def update_review_status(review_id: int, status: str) -> bool:
    try:
        review = db.session.get(Review, review_id)
        if review:
            review.status = status
            db.session.commit()
            return True
        return False
    except Exception as err:
        print(f"Error updating review status: {err}")
        # self.__log_activity(
        #     inspect.currentframe().f_code.co_name,
        #     False,
        #     {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
        # )
        db.session.rollback()
        return False



def get_questions_with_answers(q_set_id: int) -> list[dict[int, str]]:
    try:
        questions = (
            db.session.query(Question)
            .join(QuestionSetQuestions, QuestionSetQuestions.question_id == Question.id)
            .filter(QuestionSetQuestions.question_set_id == q_set_id)
            .all()
        )

        result = []
        for question in questions:
            question_data = {
                "id": question.id,
                "text": question.question,
                "is_abc": question.is_abc,
                "answers": []
            }
            if question.is_abc:
                answers = (
                    db.session.query(Answer)
                    .join(QuestionA, Question.question_id == Answer.question_id)
                    .filter(QuestionA.question_id == question.id)
                    .scalars()
                    .all()
                )
                question_data["answers"] = [{"id": ans.id, "answer": ans.answer} for ans in answers]

            result.append(question_data)

        return result

    except Exception as err:
        print("error: " + str(err))
        return []


def save_review_answers(review_id: int, answers: dict[int, str]) -> bool:
    try:
        for question_id, answer in answers.items():
            new_answer = Answer(review_id=review_id, question_id=question_id, answer=answer)
            db.session.add(new_answer)

        update_review_status(review_id=review_id, status='Reviewed')    # TODO: rollback answer submitting when exception here
        db.session.commit()
        return True
    except Exception as err:
        print("error: " + str(err))
        db.session.rollback()
        return False


def get_questions_by_article(article_id: int):
    # TODO: finish this
    try:
        questions = (
            db.session.query(Question)
            .join(QuestionSetQuestions, Question.id == QuestionSetQuestions.question_id)
            .join(QuestionSet, QuestionSetQuestions.question_set_id == QuestionSet.id)
            .all()
        )

        return [{"id": q.id, "text": q.question, "is_abc": q.is_abc} for q in questions]

    except Exception as err:
        print(f"Error fetching questions: {err}")
        return None


def get_question_answers(question_id: int):
    try:
        answers = (
            db.session.query(QuestionA)
            .filter(QuestionA.question_id == question_id)
            .all()
        )

        return [{"id": ans.id, "answer": ans.answer} for ans in answers]

    except Exception as err:
        print(f"Error fetching answers: {err}")
        return []