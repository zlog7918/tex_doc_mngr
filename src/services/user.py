from sqlalchemy import or_
from db.db_base import db
from models.usr.User import User
from flask_login import current_user
from models.utils.MessageException import MessageException

def get_user(id: int) -> User|None:
    return User.query.where(User.id==id).first()

def get_user_by_nick(nick: str) -> User|None:
    return User.query.where(User.nick==nick).first()

def get_user_by_email(email: str) -> User|None:
    return User.query.where(User.email==email).first()

def get_user_id(nick: str) -> int:
    # TODO: split handling exceptions and handling non-existing user
    try:
        user=get_user_by_nick(nick)
        if user is None:
            raise MessageException(f'{nick}')
        return user.id
    except MessageException as e:
        raise MessageException.from_exception(e, f'Nie znaleziono użytkownika: {str(e)}') from None

def get_curr_user() -> User|None:
    try:
        u=current_user._get_current_object() # type: ignore[private_access]
    except RuntimeError:
        return None
    if u is None:
        return None
    if isinstance(u, User):
        return u
    return None

def get_curr_user_or_err() -> User:
    u=get_curr_user()
    if u is None:
        raise MessageException('Nie jest zalogowany, żaden użytkownik')
    return u

def add_user(user: User):
    try:
        db.session.add(user)
    except Exception as e:
        raise MessageException.from_exception(e, 'Użytkownik nie został dodany')

def approve_user(user: User) -> None:
    try:
        user.approve()
        db.session.flush()
    except Exception as e:
        raise MessageException.from_exception(e, 'Konto nie zostało potwierdzone')

def change_user_pass(user: User, passwd: str) -> bool:
    try:
        if user.ch_pass(passwd):
            db.session.flush()
            return True
        return False
    except Exception as e:
        raise MessageException.from_exception(e, 'Hasło nie zostało zmienione')
    
def set_user_nick(user: User, nick: str) -> None:
    try:
        user.nick=nick
        db.session.flush()
    except Exception as e:
        raise MessageException.from_exception(e, 'Konto nie zostało utworzone')
