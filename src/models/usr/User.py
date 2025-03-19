import os
from db.db_base import db
from flask_login import UserMixin
from passlib.hash import sha256_crypt
from ..utils.utils import validate_pass
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import or_, Integer, Boolean, Text, CheckConstraint

class User(db.Model, UserMixin):
    __tablename__ = 'usr'
    __PEPPER__=bytes.fromhex(os.getenv('PEPPER_VAL'))
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nick: Mapped[str|None] = mapped_column(Text, nullable=True, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    passwd: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint(or_(
            nick!=None,
            approved==False,
        ), name='usr_invited_is_not_approved'),
    )
    def get_id(self) -> str:
        return f"{self.id}"
    def get_nick(self) -> str:
        return '' if self.nick is None else self.nick
    def get_email(self) -> str:
        return self.email
    def is_approved(self) -> bool:
        return self.approved
    def get_passwd(self) -> str:
        return self.passwd
    
    def approve(self) -> None:
        self.approved=True
    def __pass(self, passwd: str) -> bytes:
        return self.__PEPPER__+bytes(passwd, 'utf8')
    def verify_pass(self, passwd: str) -> bool:
        if (self.passwd is None):
            return False
        return sha256_crypt.verify(self.__pass(passwd), self.passwd)
    def ch_pass(self, passwd: str) -> bool:
        if not validate_pass(passwd):
            return False
        self.passwd=sha256_crypt.hash(self.__pass(passwd))
        return True
