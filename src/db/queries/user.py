from sqlalchemy import or_
from db.db_base import db
from models.usr.User import User

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


def is_user_existing(nick, email):
    try:
        q=User.query.where(or_(User.nick==nick, User.email==email))
        return db.session.execute(q).first()
    except Exception as e:
        # TODO: Add logs
        return None

def add_user(user) -> bool:
    try:
        db.session.add(user)
        db.session.commit()
        return True 
    except Exception as e:
        #TODO: add logs
        return False