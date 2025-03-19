from db.db_base import db
from .Review import Review
from .Article import Article
from .Questions import QuestionSet
from sqlalchemy import ForeignKey, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.relationships import _RelationshipDeclared

class Round(db.Model):
    __tablename__ = 'rounds'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey(Article.id), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    q_set_id: Mapped[int] = mapped_column(ForeignKey(QuestionSet.id), nullable=False)
    deadline_confirm: Mapped[Date] = mapped_column(Date, nullable=False)
    deadline_submit: Mapped[Date] = mapped_column(Date, nullable=False)

    article: _RelationshipDeclared[Article] = relationship(Article, back_populates=str(Article.rounds))
    status: _RelationshipDeclared[QuestionSet] = relationship(QuestionSet, foreign_keys=[q_set_id])

    reviews: _RelationshipDeclared[Review] = relationship(Review, back_populates=str(Review.round))
