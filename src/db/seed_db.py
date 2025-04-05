from src.models.usr.User import User
from flask_sqlalchemy import SQLAlchemy
from src.models.utils import utils as util
from src.models.usr.Code import CodePurpose, CodePurposeEnum
from src.models.article.Article import Article, ArticleStatus, ArticleStatusEnum
from src.models.article.Questions import Question, QuestionA, QuestionSet, QuestionSetQuestions

def seed_data(db: SQLAlchemy) -> None:
    if not User.query.first():
        # WARNING: password here is "aaaa" for randomly generated pepper, to use those accounts please generate for own pepper and replace passwd entries below
        users = [
            User(**util.get_kwargs_for(User, {User.nick: 'aaaa', User.email: 'a@a.a', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'bbbb', User.email: 'b@b.b', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'cccc', User.email: 'c@c.c', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'dddd', User.email: 'd@d.d', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'eeee', User.email: 'e@e.e', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
        ]
        db.session.add_all(users)
    
    if not CodePurpose.query.first():
        purposes = [
            CodePurpose(**util.get_kwargs_for(CodePurpose, {CodePurpose.purpose: p})) for p in CodePurposeEnum
        ]
        db.session.add_all(purposes)
    
    if not ArticleStatus.query.first():
        statuses = [
            ArticleStatus(**util.get_kwargs_for(ArticleStatus, {ArticleStatus.stat: e})) for e in ArticleStatusEnum
        ]
        db.session.add_all(statuses)
    
    if not Article.query.first():
        status=ArticleStatus.query.where(ArticleStatus.stat==ArticleStatusEnum.Submitted).first()
        if status is not None:
            _status: ArticleStatus=status
            status_id=_status.id
            del status, _status
            articles = [
                Article(**util.get_kwargs_for(Article, {Article.title: 'Introduction to Flask', Article.author_id: 1, Article.content: 'This is a beginner-friendly guide to Flask.', Article.status_id: status_id, Article.editor_id: 2})),
                Article(**util.get_kwargs_for(Article, {Article.title: 'Understanding REST APIs', Article.author_id: 2, Article.content: 'Explores RESTful APIs and their best practices.', Article.status_id: status_id, Article.editor_id: 1})),
                Article(**util.get_kwargs_for(Article, {Article.title: 'Advanced Flask Techniques', Article.author_id: 3, Article.content: 'Delves into advanced techniques in Flask.', Article.status_id: status_id, Article.editor_id: 1})),
                Article(**util.get_kwargs_for(Article, {Article.title: 'Advanced Flask Techniques2', Article.author_id: 3, Article.content: 'Further techniques in Flask for experienced users.', Article.status_id: status_id, Article.editor_id: 1})),
                Article(**util.get_kwargs_for(Article, {Article.title: 'Common Pitfalls', Article.author_id: 2, Article.content: 'Discusses common pitfalls to avoid in Flask.', Article.status_id: status_id, Article.editor_id: 1})),
            ]
            db.session.add_all(articles)
        else:
            raise Exception(f'ArticleStatus not added')
    
    if not Question.query.first():
        questions = [
            Question(**util.get_kwargs_for(Question, {Question.question: 'Comments', Question.is_abc: False})),
            Question(**util.get_kwargs_for(Question, {Question.question: 'Rating', Question.is_abc: True})),
        ]
        db.session.add_all(questions)
    
    if not QuestionA.query.first():
        question_as = [
            QuestionA(**util.get_kwargs_for(QuestionA, {QuestionA.question_id: 2, QuestionA.answer: 'Fine as it is'})),
            QuestionA(**util.get_kwargs_for(QuestionA, {QuestionA.question_id: 2, QuestionA.answer: 'Requires small changes'})),
            QuestionA(**util.get_kwargs_for(QuestionA, {QuestionA.question_id: 2, QuestionA.answer: 'Needs major revisions'})),
            QuestionA(**util.get_kwargs_for(QuestionA, {QuestionA.question_id: 2, QuestionA.answer: 'Rejected'})),
        ]
        db.session.add_all(question_as)
    
    if not QuestionSet.query.first():
        question_sets = [
            QuestionSet(**util.get_kwargs_for(QuestionSet, {QuestionSet.name: 'Default Question Set'})),
        ]
        db.session.add_all(question_sets)
    
    if not QuestionSetQuestions.query.first():
        question_set_questions = [
            QuestionSetQuestions(**util.get_kwargs_for(QuestionSetQuestions, {QuestionSetQuestions.question_set_id: 1, QuestionSetQuestions.question_id: 1})),
            QuestionSetQuestions(**util.get_kwargs_for(QuestionSetQuestions, {QuestionSetQuestions.question_set_id: 1, QuestionSetQuestions.question_id: 2})),
        ]
        db.session.add_all(question_set_questions)
    
    db.session.commit()