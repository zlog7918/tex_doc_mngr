from flask_login import UserMixin
from ..db.DBQ_Users import DBQ_Users
from passlib.hash import sha256_crypt
from ..db.DB_Factory import DB_Factory, DB_QueriesOpt

class User(UserMixin):
    __PASS_NOT_SET__: str=''
    def __init__(self
        # ,id: int
        ,nick: str
        ,email: str
        ,passwd: str=__PASS_NOT_SET__
        ,is_approved: bool=False
    ):
        # self.__id: int=id
        self.__nick: str=nick
        self.__email: str=email
        self.__passwd: str=passwd
        self.__is_approved: bool=is_approved
    def get_id(self) -> str:
        return self.__nick
    def get_nick(self) -> str:
        return self.__nick
    def get_email(self) -> str:
        return self.__email
    def is_approved(self) -> bool:
        return self.__is_approved
    def get_passwd(self) -> str:
        return self.__passwd
    def verify_pass(self, passwd: str) -> bool:
        if self.__passwd==self.__PASS_NOT_SET__:
            return False
        return sha256_crypt.verify(passwd, self.__passwd)
    def ch_pass(self, passwd: str) -> str|bool:
        if self.verify_pass(passwd):
            return False
        self.__passwd=sha256_crypt.hash(passwd)
        return self.__passwd


def user_loader(nick: str|None) -> User|None:
    if nick is None:
        return None

    db: DBQ_Users=DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Users)
    try:
        nick, email, passwd, is_approved=db.get_user(nick)
    except:
        return None
    user=User(nick, email, passwd, is_approved)
    return user