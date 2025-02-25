from db.db_base import db
from sqlalchemy import ForeignKey, String, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum

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
    author_id: Mapped[int] = mapped_column(ForeignKey('usr.id'), nullable=False)
    editor_id: Mapped[int] = mapped_column(ForeignKey('usr.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey('article_status.id'), nullable=False)
    
    author = relationship('User', foreign_keys=[author_id])
    editor = relationship('User', foreign_keys=[editor_id])
    status = relationship('ArticleStatus', backref='articles')
