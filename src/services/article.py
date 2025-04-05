from db.db_base import db
from services import user as uq
from models.usr.User import User
from sqlalchemy import and_, select
from models.usr.User import User
from flask_login import current_user
from models.usr.User import User
from models.article.Round import Round
from models.utils import utils as util
from models.article.Review import Review
from db.db_base import db, log_activity, log_err
from models.article.Questions import Answer, Question
from models.utils.MessageException import MessageException
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum

def __get_status_or_err(status: ArticleStatusEnum) -> ArticleStatus:
    _status: ArticleStatus|None = ArticleStatus.query.where(ArticleStatus.stat==status).first()
    if _status is None:
        raise ValueError(f'Podany status artykułu: {status.name} nie istnieje w bazie danych')
    return _status

def create_article(title: str, editor_id: int) -> Article:
    try:
        user_id=int(uq.get_curr_user_or_err().get_id())
        status = __get_status_or_err(ArticleStatusEnum.Submitted)

        new_article = Article(**util.get_kwargs_for(Article, {
            Article.title: title,
            Article.author_id: user_id,
            Article.editor_id: editor_id,
            Article.status_id: status.id,
        }))
        db.session.add(new_article)
        db.session.flush()
        article = get_article_by_title(user_id, title)
        if article is None:
            raise MessageException(f'Nie udało się pobrać artykułu "{title}" po zapisaniu')

        log_activity(True, {'msg': f'Created article "{title}" with id {article.id} by user {user_id}'})
        return article
    except MessageException as e:
        raise MessageException.from_exception(e, 'Article not created')


def get_article(article_id: int) -> Article|None:
    return Article.query.where(Article.id==article_id).first()

def get_article_by_title(author_id: int, title: str) -> Article|None:
    return Article.query.where(and_(Article.author_id == author_id, Article.title == title)).first()

def get_all_articles_by_editor_id(editor_id: int) -> list[Article]:
    return (
        Article.query
        .join(ArticleStatus)
        .where(and_(
            Article.editor_id == editor_id,
            ArticleStatus.stat != ArticleStatusEnum.Rejected
        ))
        .all()
    )


def is_article_rejected(article_id: int) -> bool:
    article_status = (
        db.session.query(ArticleStatus.stat)
        .join(Article, Article.status_id == ArticleStatus.id)
        .where(Article.id == article_id)
        .scalar()
    )
    return article_status == ArticleStatusEnum.Rejected

def get_latest_round(article_id: int) -> Round | None:
    return Round.query.filter_by(article_id=article_id).order_by(Round.round_number.desc()).first()

def get_available_reviewers(article_id: int) -> dict[int, str]:
    try:
        user_id = uq.get_curr_user_or_err().get_id()
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
        raise MessageException.from_exception(err, 'Error while: finding available reviewers')
    
def get_available_editors() -> dict[int, str]:
    try:
        editors = (
            db.session.query(User.id, User.nick)
            .filter(User.id != int(uq.get_curr_user_or_err().get_id()))
            .all()
        )

        return {row.id: row.nick for row in editors} 

    except Exception as e:
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
        raise MessageException.from_exception(err, 'Error while: finding assigned reviewers')


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
        raise MessageException.from_exception(err, 'Error while: finding assigned reviews')

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
        raise MessageException.from_exception(err, 'Error while: finding answers')

def get_last_round_number(article_id: int) -> int:
    try:
        last_round = (
            db.session.query(Round.round_number)
            .where(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .scalar()
        )
        return 0 if last_round is None else last_round
    except Exception as err:
        raise MessageException.from_exception(err, 'Error while: finding last round number')


def create_round(article_id: int, article_content: str, round_number: int, deadline_confirm: str|None = None, deadline_submit: str|None = None) -> None:
    try:
        article = get_article(article_id)
        if not article:
            raise MessageException(f'Article with id {article_id} has not been found')
        
        if article.status.stat != ArticleStatusEnum.NeedsCorrections and not (article.status.stat == ArticleStatusEnum.Submitted and round_number == 1):
            raise MessageException(f'Article has incorrect status')

        new_round = Round(**util.get_kwargs_for(Round, {
            Round.article_id: article_id,
            Round.article_content: article_content,
            Round.round_number: round_number,
            Round.q_set_id: 1, # TODO: should be set later
            Round.deadline_confirm: deadline_confirm,
            Round.deadline_submit: deadline_submit,
        }))
        db.session.add(new_round)
        db.session.flush()
    except Exception as err:
        raise MessageException.from_exception(err, 'Round was not created')

def set_deadlines(article_id: int, deadline_confirm: str|None, deadline_submit: str|None) -> bool:
    try:
        article = get_article(article_id)
        if not article or not article.rounds:
            return False

        round = get_latest_round(article_id)

        if not round:
            log_activity(False, {'err':f'Did not set deadlines because of not finding latest round.'})
            return False

        if deadline_confirm:
            round.deadline_confirm = deadline_confirm
        if deadline_submit:
            round.deadline_submit = deadline_submit

        return True
    except Exception as e:
        db.session.rollback()
        log_err(e)
        return False


def add_reviewer_to_article(article_id: int, reviewer_id: int) -> None:
    try:
        round_id = (
            db.session.query(Round.id)
            .filter(Round.article_id == article_id)
            .order_by(Round.round_number.desc())
            .limit(1)
            .scalar()
        )

        if round_id:
            new_review = Review(**util.get_kwargs_for(Review, {
                Review.round_id: round_id,
                Review.reviewer_id: reviewer_id,
                Review.status: 'Pending confirmation',
            }))
            db.session.add(new_review)
            db.session.flush()
        else:
            raise MessageException(f'No round found for the given article_id: {article_id}')

    except Exception as err:
        raise MessageException.from_exception(err, f'Nie dodano podanych reviewer\'ów do artykułu: {article_id}')

def update_article_status(article: Article, status: ArticleStatusEnum) -> None:
    try:
        _status=__get_status_or_err(status)
        article.update_status(_status)
        db.session.commit()
    except Exception as err:
        print(err)
        raise MessageException.from_exception(err, 'Article status not updated')
