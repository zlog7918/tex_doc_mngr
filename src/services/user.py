from sqlalchemy import or_
from models.usr.User import User
from db.db_base import db, log_err
from flask_login import current_user
from models.utils.utils import get_function

def user_loader(id: int) -> User|None:
    return User.query.where(User.id==id).first()

def user_loader_by_nick(nick: str) -> User|None:
    return User.query.where(User.nick==nick).first()

def user_loader_by_email(email: str) -> User|None:
    return User.query.where(User.email==email).first()

def get_user_id(nick: str) -> int:
    # TODO: split handling exceptions and handling non-existing user
    try:
        user=user_loader_by_nick(nick)
        if user is None:
            raise Exception()
        return user.id
    except Exception as e:
        raise Exception(f'Nie znaleziono użytkownika: {str(e)}')

def get_curr_user() -> User|None:
    return current_user._get_current_object()

def get_curr_user_or_err() -> User:
    u=get_curr_user()
    if u is None:
        raise Exception('Nie jest zalogowany, żaden użytkownik')
    return u

def is_user_existing(nick: str, email: str) -> bool:
    try:
        return User.query.where(
            or_(
                User.nick==nick
                ,User.email==email
            )
        ).first() is not None
    except Exception as e:
        log_err(get_function(), e)
        return False

def add_user(user: User) -> bool:
    try:
        db.session.add(user)
        db.session.commit()
        return True 
    except Exception as e:
        log_err(get_function(), e)
        return False

def approve_user(user: User) -> None:
    try:
        user.approve()
        db.session.commit()
    except Exception as e:
        log_err(get_function(), e)
        raise Exception('Konto nie zostało potwierdzone')

def change_user_pass(user: User, passwd: str) -> bool:
    try:
        if user.ch_pass(passwd):
            db.session.commit()
            return True
        return False
    except Exception as e:
        log_err(get_function(), e)
        raise Exception('Hasło nie zostało zmienione')
