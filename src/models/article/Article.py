import typing as t
from enum import Enum
from .Round import Round
import sqlalchemy as sqla
from db.db_base import db
from models.usr.User import User
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ArticleStatusEnum(Enum):
    Submitted = 'Submitted'
    Accepted = 'Accepted'
    InReview = 'In review'
    Reviewed = 'Reviewed'
    Rejected = 'Rejected'
    NeedsCorrections = 'Needs Corrections'
    Final = 'Final'

class ArticleStatus(db.Model):
    __tablename__ = 'article_status'
    
    id: Mapped[int] = mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    stat: Mapped[ArticleStatusEnum] = mapped_column(sqla.Enum(ArticleStatusEnum), nullable=False, unique=True)

class Article(db.Model):
    __tablename__ = 'articles'
    
    id: Mapped[int] = mapped_column(sqla.Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(sqla.ForeignKey(User.id), nullable=False)
    editor_id: Mapped[int] = mapped_column(sqla.ForeignKey(User.id), nullable=True)
    title: Mapped[str] = mapped_column(sqla.String(255), nullable=False)
    status_id: Mapped[int] = mapped_column(sqla.ForeignKey(ArticleStatus.id), nullable=False)
    
    author: Mapped[User] = relationship(foreign_keys=[author_id])
    editor: Mapped[User] = relationship(foreign_keys=[editor_id])
    status: Mapped[ArticleStatus] = relationship(foreign_keys=[status_id])
    rounds: Mapped[list[Round]] = relationship(back_populates='article', cascade="all, delete-orphan", order_by=Round.round_number.asc())

    __table_args__ = (
        sqla.UniqueConstraint('author_id', 'title', name='uq_author_title'),
        sqla.CheckConstraint('author_id != editor_id', name='check_author_not_editor'),
    )

    def update_status(self, new_status: ArticleStatus) -> None:
        self.status_id = new_status.id

    def to_dict(self) -> dict[str, t.Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author.get_nick() if self.author else None,
            "status": self.status.stat.value if self.status else None,
        }
