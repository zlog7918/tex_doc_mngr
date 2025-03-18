from sqlalchemy import and_, select
from models.utils.utils import get_function
from . import user as uq
from db.db_base import db, log_err
from models.usr.User import User
from flask_login import current_user
from models.article.Round import Round
from models.article.Review import Review
from models.article.Questions import Answer, Question
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum

def create_article(title: str, file_url: str, editor_id: int) -> bool:
    try:
        user_id = current_user.get_id()
        if not editor_id:
            return False

        status = ArticleStatus.query.filter_by(stat=ArticleStatusEnum.Submitted).first()
        if not status:
            return False

        new_article = Article(
            title=title,
            author_id=int(user_id),
            editor_id=editor_id,
            content=file_url,
            status_id=status.id
        )
        db.session.add(new_article)
        db.session.commit()

        return True

    except Exception as e:
        # TODO: log
        print(str(e))
        db.session.rollback()
        return False


def get_article(article_id: int) -> Article|None:
    return Article.query.where(Article.id==article_id).first()


def get_all_articles_by_editor_id(editor_id: int) -> list[Article]:
    return Article.query.where(Article.editor_id == editor_id).all()


def get_available_reviewers(article_id: int) -> dict[int, str]:
    try:
        user_id = current_user.get_id()
        article = Article.query.where(Article.id == article_id).first()
        author_id = article.author_id if article else None

        latest_round_subquery = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .subquery()
        )

        assigned_reviewers_subquery = (
            db.session.query(Review.reviewer_id)
            .filter(Review.round_id.in_(select(latest_round_subquery)))
            .subquery()
        )

        reviewers = (
            db.session.query(User.id, User.nick)
            .where(and_(
                ~User.id.in_(select(assigned_reviewers_subquery)),
                User.id != user_id,
                User.id != author_id
            ))
            .all()
        )

        # Konwersja wyników na listę słowników
        return { row.id: row.nick for row in reviewers }

    except Exception as err:
        print("error1: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return {}
    
def get_available_editors() -> dict[int, str]:
    try:
        editors = (
            db.session.query(User.id, User.nick)
            .filter(User.id != current_user.id)
            .all()
        )

        return {row.id: row.nick for row in editors} 

    except Exception as e:
        log_err(get_function(), e)
        return {}

def get_assigned_reviewers(article_id: int) -> dict[int, str]:
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
            .filter(Review.round_id.in_(select(latest_round_subquery)))
            .all()
        )

        # Konwersja do listy słowników
        return {row.id: row.nick for row in reviewers}

    except Exception as err:
        print("error2: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return {}


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
            .filter(Review.round_id.in_(select(latest_round_subquery)))
            .all()
        )

        return reviews

    except Exception as err:
        print("error3: " + str(err))
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
        print("error4: " + str(err))
        # self.__log_activity(inspect.currentframe().f_code.co_name, False,
        #                     {'err': str(err), 'traceback': ''.join(traceback.format_tb(err.__traceback__))})
        return {}

# TODO: compare with update_status from controller
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


def create_round(article_id: int, round_number: int, deadline_confirm: str = None, deadline_submit: str = None) -> bool:
    try:
        new_round = Round(
            article_id=article_id,
            round_number=round_number,
            q_set_id=1, # TODO: should be set later
            deadline_confirm=deadline_confirm,
            deadline_submit=deadline_submit
        )
        db.session.add(new_round)
        db.session.commit()
        print("created")
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