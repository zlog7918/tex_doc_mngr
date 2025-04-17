from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Review import Review
from db.db_base import db
from .Article import Article
from .Questions import QuestionSet
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, CheckConstraint, Integer, Date, Text

class Round(db.Model):
    __tablename__ = 'rounds'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey('articles.id'), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    q_set_id: Mapped[int|None] = mapped_column(ForeignKey(QuestionSet.id), nullable=True)
    deadline_confirm: Mapped[Date|None] = mapped_column(Date, nullable=True)
    deadline_submit: Mapped[Date|None] = mapped_column(Date, nullable=True)

    article: Mapped["Article"] = relationship(back_populates='rounds', order_by=round_number.asc())
    question_set: Mapped[QuestionSet] = relationship(foreign_keys=[q_set_id])
    reviews: Mapped[list["Review"]] = relationship(back_populates='round')

# Article.rounds=rounds
