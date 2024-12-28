from flask_login import UserMixin
from passlib.hash import sha256_crypt

class User(UserMixin):
    def __init__(self
        # ,id: int
        ,nick: str
        ,passwd: str
    ):
        # self.__id: int=id
        self.__nick: str=nick
        self.__passwd: str=passwd
    def get_id(self) -> str:
        return self.__nick
    def get_nick(self) -> str:
        return self.__nick
    def verify_pass(self, passwd: str) -> bool:
        return passwd==self.__passwd
        # return sha256_crypt.verify(passwd, self.__passwd)
    def ch_pass(self, passwd: str) -> str|False:
        if self.verify_pass(passwd):
            return False
        self.__passwd=sha256_crypt.hash(passwd)
        return self.__passwd