from sqlalchemy import or_
from db.db_base import db
from models.usr.User import User

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