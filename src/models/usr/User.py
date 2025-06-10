import time
import random
import sqlalchemy as sqla
from db.db_base import db
from enum import Enum, auto
import sqlalchemy.orm as sqlao
from flask_login import UserMixin
from passlib.hash import sha256_crypt
from models.utils.utils import validate_pass
from models.utils.EnvConsts import envConsts as ec

class UserGroupEnum(Enum):
    Author=auto()
    Editor=auto()
    Reviewer=auto()
    
class UserGroup(db.Model):
    __tablename__ = 'user_groups'

    id: sqlao.Mapped[int] = sqlao.mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    group: sqlao.Mapped[UserGroupEnum] = sqlao.mapped_column(sqla.Enum(UserGroupEnum), nullable=False, unique=True)

class User(db.Model, UserMixin):
    __tablename__ = 'usr'
    __PEPPER__=bytes.fromhex(ec.getPepper())

    id: sqlao.Mapped[int] = sqlao.mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    nick: sqlao.Mapped[str|None] = sqlao.mapped_column(sqla.Text, nullable=True, unique=True)
    email: sqlao.Mapped[str] = sqlao.mapped_column(sqla.Text, nullable=False, unique=True)
    passwd: sqlao.Mapped[str|None] = sqlao.mapped_column(sqla.Text, nullable=True)
    do_after_cr: sqlao.Mapped[bytes|None] = sqlao.mapped_column(sqla.LargeBinary, nullable=True)
    approved: sqlao.Mapped[bool] = sqlao.mapped_column(sqla.Boolean, nullable=False, default=False)

    __table_args__ = (
        sqla.CheckConstraint(sqla.or_(
            nick!=None,
            approved==False,
        ), name='usr_invited_is_not_approved'),
        sqla.CheckConstraint(sqla.or_(
            nick==None,
            do_after_cr==None,
        ), name='usr_created_has_nothing_in_after_created'),
    )
    groups: sqlao.Mapped[list["UsersGroups"]]=sqlao.relationship(back_populates='user')

    def get_id(self) -> str:
        return f'{self.id}'
    def get_nick(self) -> str:
        return '' if self.nick is None else self.nick
    
    def approve(self) -> None:
        self.approved=True
    def __pass(self, passwd: str) -> bytes:
        return self.__PEPPER__+bytes(passwd, 'utf8')
    def verify_pass(self, passwd: str) -> bool:
        time.sleep(0.3+(random.random()/4))
        if (self.passwd is None):
            time.sleep(0.3)
            return False
        ret=sha256_crypt.verify(self.__pass(passwd), self.passwd)
        if not ret:
            time.sleep(0.3)
        return ret
    def ch_pass(self, passwd: str) -> bool:
        if not validate_pass(passwd):
            return False
        self.passwd=sha256_crypt.hash(self.__pass(passwd))
        return True
    
class UsersGroups(db.Model):
    __tablename__ = 'users_groups'

    id: sqlao.Mapped[int]=sqlao.mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    user_id: sqlao.Mapped[int]=sqlao.mapped_column(sqla.ForeignKey(User.id), nullable=False)
    group_id: sqlao.Mapped[int]=sqlao.mapped_column(sqla.ForeignKey(UserGroup.id), nullable=False)

    __table_args__ = (
        sqla.UniqueConstraint(user_id, group_id),
    )

    user: sqlao.Mapped[User]=sqlao.relationship(back_populates='groups')
    group: sqlao.Mapped[UserGroup]=sqlao.relationship(foreign_keys=[group_id])

class User_params(Enum):
    self=auto()
    id=auto()
    nick=auto()
    email=auto()
