from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import MetaData, ForeignKey, UniqueConstraint, String, Integer, Boolean, Text, Date, DateTime

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    __tablename__ = 'usr'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nick: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    passwd: Mapped[str] = mapped_column(Text, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    code_exp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

class Log(db.Model):
    __tablename__ = 'log'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(Text, nullable=False)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    timest: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    log: Mapped[str] = mapped_column(Text, nullable=False)

class ArticleStatus(db.Model):
    __tablename__ = 'article_status'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat: Mapped[str] = mapped_column(String(50), nullable=False)

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

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey('rounds.id'), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey('usr.id'), nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    round = relationship('Round', backref='reviews')
    reviewer = relationship('User', backref='reviews')

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