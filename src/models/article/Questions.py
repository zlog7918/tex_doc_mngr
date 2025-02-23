from db.db_base import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint, Integer, Boolean, Text

class Question(db.Model):
    __tablename__ = 'questions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    is_abc: Mapped[bool] = mapped_column(Boolean, nullable=False)

class QuestionSet(db.Model):
    __tablename__ = 'question_set'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

class QuestionSetQuestions(db.Model):
    __tablename__ = 'question_set_questions'
    
    question_set_id: Mapped[int] = mapped_column(ForeignKey('question_set.id'), primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), primary_key=True)

class QuestionA(db.Model):
    __tablename__ = 'question_a'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    __table_args__ = (UniqueConstraint('question_id', 'answer'),)

class Answer(db.Model):
    __tablename__ = 'answers'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey('reviews.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    __table_args__ = (UniqueConstraint('review_id', 'question_id'),)
