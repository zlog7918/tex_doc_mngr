import string
import random
from .User import User
from db.db_base import db
from sqlalchemy import or_
from typing import Optional
from ..utils import consts as c
from enum import Enum as PyEnum, auto
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index

class CodePurposeEnum(PyEnum):
    __ALPHABET__=string.digits+string.ascii_letters
    ApproveUser=auto()
    ResetUserPassReq=auto()
    ResetUserPass=auto()
    def gen_code(self) -> tuple[str, int]:
        return ''.join(random.choice(self.__ALPHABET__) for _ in range(c.CODE_GEN_LEN)), c.TIME_TO_EXPIRE
    
class CodePurpose(db.Model):
    __tablename__ = 'code_purpose'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purpose: Mapped[CodePurposeEnum] = mapped_column(Enum(CodePurposeEnum), nullable=False, unique=True)

class Code(db.Model):
    __tablename__ = 'codes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usr_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    purpose_id: Mapped[int] = mapped_column(ForeignKey(CodePurpose.id), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    timest: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    code_exp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    purpose = relationship(CodePurpose.__name__, foreign_keys=[purpose_id])
    usr = relationship(User.__name__, foreign_keys=[usr_id])
    __table_args__ = (
        UniqueConstraint(code, is_active),
        CheckConstraint(or_(
            is_active==None
            ,is_active==True
        ), name='codes_active_true_or_null'),
        CheckConstraint(timest<code_exp, name='codes_timest_before_exp'),
        Index("code_idx_code_exp", code_exp),
    )

    def deactivate(self) -> None:
        self.is_active=None