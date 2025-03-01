from db.db_base import db
from flask_login import UserMixin
from passlib.hash import sha256_crypt
from ..utils.utils import validate_pass
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Boolean, Text, DateTime

class User(db.Model, UserMixin):
    __tablename__ = 'usr'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nick: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    passwd: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    code_exp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    def get_id(self) -> str:
        return f"{self.id}"
    def get_nick(self) -> str:
        return self.nick
    def get_email(self) -> str:
        return self.email
    def is_approved(self) -> bool:
        return self.approved
    def get_passwd(self) -> str:
        return self.passwd
    
    def approve(self, code: str) -> bool:
        if self.approved:
            return False
        if code!=self.code:
            return False
        self.approved=True
        self.code=''
        db.session.commit()
        return True
    def verify_pass(self, passwd: str) -> bool:
        if (self.passwd is None):
            return False
        return sha256_crypt.verify(passwd, self.passwd)
    def ch_pass(self, passwd: str) -> bool:
        if self.verify_pass(passwd) or (not validate_pass(passwd)):
            return False
        self.passwd=sha256_crypt.hash(passwd)
        db.session.commit()
        return True
