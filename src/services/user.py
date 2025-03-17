from db.db_base import db
from sqlalchemy import or_
from db.db_base import log_err
from models.usr.User import User
from models.utils.utils import get_function

def user_loader(id: int) -> User|None:
    q=User.query.where(User.id==id)
    ret=db.session.execute(q).first()
    if ret is None:
        return None
    return ret[0]

def user_loader_by_nick(nick: str|None) -> User|None:
    if nick is None:
        return None

    q=User.query.where(User.nick==nick)
    ret=db.session.execute(q).first()
    if ret is None:
        return None
    return ret[0]

def get_user_id(nick: str) -> int:
    # TODO: split handling exceptions and handling non-existing user
    try:
        return User.query.filter_by(nick=nick).first().id
    except Exception as e:
        raise Exception('Nie znaleziono użytkownika: ' + str(e))


def is_user_existing(nick: str, email: str) -> bool:
    try:
        q=User.query.where(or_(User.nick==nick, User.email==email))
        return db.session.execute(q).first() is not None
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