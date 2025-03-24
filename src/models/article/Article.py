from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Round import Round
from db.db_base import db
from enum import Enum as PyEnum
from models.usr.User import User
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, Text, Enum, CheckConstraint

class ArticleStatusEnum(PyEnum):
    Submitted='Submitted'
    Accepted='Accepted'
    InReview='In review'
    Reviewed='Reviewed'
    Rejected='Rejected'
    NeedsCorrections='Needs Corrections'
    Final='Final'

class ArticleStatus(db.Model):
    __tablename__ = 'article_status'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat: Mapped[ArticleStatusEnum] = mapped_column(Enum(ArticleStatusEnum), nullable=False, unique=True)

class Article(db.Model):
    __tablename__ = 'articles'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    editor_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey(ArticleStatus.id), nullable=False)
    
    author: Mapped[User] = relationship(foreign_keys=[author_id])
    editor: Mapped[User] = relationship(foreign_keys=[editor_id])
    status: Mapped[ArticleStatus] = relationship(foreign_keys=[status_id])

    rounds: Mapped[list["Round"]] = relationship(back_populates='article')
    
    __table_args__ = (
        CheckConstraint(author_id != editor_id, name='check_author_not_editor'),
    )

    def update_status(self, new_status: ArticleStatus) -> None:
        self.status_id = new_status.id

