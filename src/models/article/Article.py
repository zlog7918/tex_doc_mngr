from db.db_base import db, log_activity, log_err
from models.utils.utils import get_function
from enum import Enum as PyEnum
from sqlalchemy import ForeignKey, String, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    def update_status(self, new_status: ArticleStatusEnum) -> bool:
        try:
            status = ArticleStatus.query.where(ArticleStatus.stat == new_status).first()
            if status:
                self.status_id = status.id
                log_activity(get_function(), True, {'details': f'Changed article status with id: {self.id} to: {new_status.value}'})
                return True
            log_activity(get_function(), False, {'err': f'Article {self.id} status not changed to: {new_status.value} '})
            return False
        except Exception as e:
            db.session.rollback()
            log_err(get_function(), e)
            return False