from sqlalchemy import and_
from models.usr.User import User
from models.article.Round import Round
from models.utils import utils as util
from flask_sqlalchemy import SQLAlchemy
from models.article import Questions as Q
from models.usr.Code import CodePurpose, CodePurposeEnum
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum

def seed_data(db: SQLAlchemy) -> None:
    default_usr_nick='Default user'
    if not User.query.where(and_(User.nick==default_usr_nick, User.id==0)).first():
        # WARNING: password here is "aaaa" for randomly generated pepper, to use those accounts please generate for own pepper and replace passwd entries below
        users = [
            User(**util.get_kwargs_for(User, {User.id: 0, User.nick: default_usr_nick, User.email: '', User.passwd: None, User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'aaaa', User.email: 'a@a.a', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'bbbb', User.email: 'b@b.b', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'cccc', User.email: 'c@c.c', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'dddd', User.email: 'd@d.d', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
            User(**util.get_kwargs_for(User, {User.nick: 'eeee', User.email: 'e@e.e', User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', User.approved: True})),
        ]
        db.session.add_all(users)
    user_0_id=User.query.where(and_(User.nick==default_usr_nick, User.id==0)).first().id
    
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
        status_id=ArticleStatus.query.where(ArticleStatus.stat==ArticleStatusEnum.Submitted).first().id
        articles = [
            Article(**util.get_kwargs_for(Article, {Article.title: 'Introduction to Flask', Article.author_id: 1, Article.status_id: status_id, Article.editor_id: 2})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Understanding REST APIs', Article.author_id: 2, Article.status_id: status_id, Article.editor_id: 1})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Advanced Flask Techniques', Article.author_id: 3, Article.status_id: status_id, Article.editor_id: 1})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Advanced Flask Techniques2', Article.author_id: 3, Article.status_id: status_id, Article.editor_id: 1})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Common Pitfalls', Article.author_id: 2, Article.status_id: status_id, Article.editor_id: 1})),
        ]
        db.session.add_all(articles)
    
    if not Q.Question.query.first():
        questions = [
            Q.Question(**util.get_kwargs_for(Q.Question, {Q.Question.user_id: user_0_id, Q.Question.question: 'Comments', Q.Question.is_abc: False})),
            Q.Question(**util.get_kwargs_for(Q.Question, {Q.Question.user_id: user_0_id, Q.Question.question: 'Rating', Q.Question.is_abc: True})),
        ]
        db.session.add_all(questions)
    
    if not Q.QuestionA.query.first():
        question_as = [
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Fine as it is'})),
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Requires small changes'})),
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Needs major revisions'})),
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Rejected'})),
        ]
        db.session.add_all(question_as)
    
    if not Q.QuestionGroup.query.first():
        question_groups = [
            Q.QuestionGroup(**util.get_kwargs_for(Q.QuestionGroup, {Q.QuestionGroup.user_id: user_0_id, Q.QuestionGroup.name: 'Default Question Group'})),
        ]
        db.session.add_all(question_groups)
    
    if not Q.QuestionGroupQuestions.query.first():
        question_group_questions = [
            Q.QuestionGroupQuestions(**util.get_kwargs_for(Q.QuestionGroupQuestions, {Q.QuestionGroupQuestions.question_group_id: 1, Q.QuestionGroupQuestions.question_id: 1})),
            Q.QuestionGroupQuestions(**util.get_kwargs_for(Q.QuestionGroupQuestions, {Q.QuestionGroupQuestions.question_group_id: 1, Q.QuestionGroupQuestions.question_id: 2})),
        ]
        db.session.add_all(question_group_questions)
        
    if not Round.query.first():
        rounds = [
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'This is a beginner-friendly guide to Flask.', Round.article_id: 1, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Explores RESTful APIs and their best practices.', Round.article_id: 2, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Delves into advanced techniques in Flask.', Round.article_id: 3, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Further techniques in Flask for experienced users.', Round.article_id: 4, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Discusses common pitfalls to avoid in Flask.', Round.article_id: 5, Round.round_number: 1})),
        ]
        db.session.add_all(rounds)
    
    db.session.commit()