from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Review import Review
    from .Article import Article
from db.db_base import db
from .Questions import QuestionSet
from sqlalchemy import ForeignKey, Integer, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Round(db.Model):
    __tablename__ = 'rounds'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey('articles.id'), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    q_set_id: Mapped[int] = mapped_column(ForeignKey(QuestionSet.id), nullable=False)
    deadline_confirm: Mapped[Date] = mapped_column(Date, nullable=True)
    deadline_submit: Mapped[Date] = mapped_column(Date, nullable=True)

    article: Mapped["Article"] = relationship(back_populates='rounds')
    status: Mapped[QuestionSet] = relationship(foreign_keys=[q_set_id])

    reviews: Mapped[list["Review"]] = relationship(back_populates='round')
