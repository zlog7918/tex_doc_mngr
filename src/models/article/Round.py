from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Review import Review
    from .Article import Article
from db.db_base import db
from .Questions import QuestionGroup
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, Date, Text, UniqueConstraint

class Round(db.Model):
    __tablename__ = 'rounds'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey('articles.id'), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline_confirm: Mapped[Date|None] = mapped_column(Date, nullable=True)
    deadline_submit: Mapped[Date|None] = mapped_column(Date, nullable=True)

    article: Mapped["Article"] = relationship(back_populates='rounds', order_by=round_number.asc())
    rqg: Mapped[list["RoundQuestionGroups"]] = relationship(back_populates='round')
    reviews: Mapped[list["Review"]] = relationship(back_populates='round')

class RoundQuestionGroups(db.Model):
    __tablename__ = 'round_question_groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey(Round.id))
    question_group_id: Mapped[int] = mapped_column(ForeignKey(QuestionGroup.id))
    
    qg: Mapped[QuestionGroup] = relationship(foreign_keys=[question_group_id])
    round: Mapped[Round] = relationship(back_populates='rqg')

    __table_args__ = (UniqueConstraint(question_group_id, round_id),)
