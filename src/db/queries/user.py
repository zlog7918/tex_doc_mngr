from sqlalchemy import or_
from db.db_base import db
from db.db_base import log_err
from models.usr.User import User
from models.utils.utils import get_function

def user_loader(nick: str|None) -> User|None:
    if nick is None:
        return None
    id=int(nick)
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

def is_user_existing(nick, email) -> bool:
    try:
        q=User.query.where(or_(User.nick==nick, User.email==email))
        return db.session.execute(q).first() is not None
    except Exception as e:
        log_err(get_function(), e)
        return False

def add_user(user) -> bool:
    try:
        db.session.add(user)
        db.session.commit()
        return True 
    except Exception as e:
        log_err(get_function(), e)
        return False