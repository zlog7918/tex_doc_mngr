from ...db.db_base import db
from sqlalchemy import ForeignKey, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Round(db.Model):
    __tablename__ = 'rounds'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey('articles.id'), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    q_set_id: Mapped[int] = mapped_column(ForeignKey('question_set.id'), nullable=False)
    deadline_confirm: Mapped[Date] = mapped_column(Date, nullable=False)
    deadline_submit: Mapped[Date] = mapped_column(Date, nullable=False)
    
    article = relationship('Article', backref='rounds')
    question_set = relationship('QuestionSet', backref='rounds')