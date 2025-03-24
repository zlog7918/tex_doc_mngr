from typing import List
from db.db_base import db
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, String, Integer, Text, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.article.Round import Round

class ArticleStatusEnum(PyEnum):
    Submitted = 'Submitted'
    Accepted = 'Accepted'
    InReview = 'In review'
    Reviewed = 'Reviewed'
    Rejected = 'Rejected'
    NeedsCorrections = 'Needs Corrections'
    Final = 'Final'

class ArticleStatus(db.Model):
    __tablename__ = 'article_status'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat: Mapped[ArticleStatusEnum] = mapped_column(Enum(ArticleStatusEnum), nullable=False, unique=True)

class Article(db.Model):
    __tablename__ = 'articles'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey('usr.id'), nullable=False)
    editor_id: Mapped[int] = mapped_column(ForeignKey('usr.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey('article_status.id'), nullable=False)
    
    author = relationship('User', foreign_keys=[author_id])
    editor = relationship('User', foreign_keys=[editor_id])
    status = relationship('ArticleStatus', backref='articles')
    rounds: Mapped[List[Round]] = relationship('Round', back_populates='article', cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint(author_id, title),)

    def update_status(self, new_status: ArticleStatusEnum) -> bool:
        try:
            status = ArticleStatus.query.filter_by(stat=new_status).first()
            if status:
                self.status_id = status.id
                db.session.commit()
                return True
            return False
        except Exception as err:
            print("exception:", str(err))
            db.session.rollback()
            return False