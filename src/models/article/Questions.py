from db.db_base import db
from .Review import Review
from ..usr.User import User
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint, Integer, Boolean, Text

class Question(db.Model):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    is_abc: Mapped[bool] = mapped_column(Boolean, nullable=False)

    qa_s: Mapped[list["QuestionA"]] = relationship(back_populates='q')
    user: Mapped[User] = relationship(foreign_keys=[user_id])

    __table_args__ = (UniqueConstraint(user_id, question),)

class QuestionA(db.Model):
    __tablename__ = 'question_a'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey(Question.id), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    q: Mapped[Question] = relationship(back_populates='qa_s')

    __table_args__ = (UniqueConstraint(question_id, answer),)

class QuestionGroup(db.Model):
    __tablename__ = 'question_group'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    qgq: Mapped[list["QuestionGroupQuestions"]] = relationship(back_populates='qg')

    __table_args__ = (UniqueConstraint(user_id, name),)

class QuestionGroupQuestions(db.Model):
    __tablename__ = 'question_group_questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_group_id: Mapped[int] = mapped_column(ForeignKey(QuestionGroup.id))
    question_id: Mapped[int] = mapped_column(ForeignKey(Question.id))
    
    qg: Mapped[QuestionGroup] = relationship(back_populates='qgq')
    q: Mapped[Question] = relationship(foreign_keys=[question_id])

    __table_args__ = (UniqueConstraint(question_group_id, question_id),)

class Answer(db.Model):
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey(Review.id), nullable=False)
    question_group_id: Mapped[int] = mapped_column(ForeignKey(QuestionGroup.id), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey(Question.id), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (UniqueConstraint(review_id, question_group_id, question_id),)
