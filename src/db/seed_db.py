from models.usr import User as U
from sqlalchemy import and_, select
from models.article.Round import Round
from models.utils import utils as util
from flask_sqlalchemy import SQLAlchemy
from models.article import Questions as Q
from models.usr.Code import CodePurpose, CodePurposeEnum
from models.article.Review import ReviewStatus, ReviewStatusEnum
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum

def seed_data(db: SQLAlchemy) -> None:
    if U.UserGroup.query.first() is None:
        user_groups = [
            U.UserGroup(**util.get_kwargs_for(U.UserGroup, {U.UserGroup.group: g})) for g in U.UserGroupEnum
        ]
        db.session.add_all(user_groups)
        del user_groups

    default_usr_nick='Default user'
    if U.User.query.where(and_(U.User.nick==default_usr_nick, U.User.id==0)).first() is None:
        # WARNING: password here is "aaaa" for randomly generated pepper, to use those accounts please generate for own pepper and replace passwd entries below
        users = [
            U.User(**util.get_kwargs_for(U.User, {U.User.id: 0, U.User.nick: default_usr_nick, U.User.email: '', U.User.passwd: None, U.User.approved: True})),
            U.User(**util.get_kwargs_for(U.User, {U.User.nick: 'aaaa', U.User.email: 'a@a.a', U.User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', U.User.approved: True})),
            U.User(**util.get_kwargs_for(U.User, {U.User.nick: 'bbbb', U.User.email: 'b@b.b', U.User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', U.User.approved: True})),
            U.User(**util.get_kwargs_for(U.User, {U.User.nick: 'cccc', U.User.email: 'c@c.c', U.User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', U.User.approved: True})),
            U.User(**util.get_kwargs_for(U.User, {U.User.nick: 'dddd', U.User.email: 'd@d.d', U.User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', U.User.approved: True})),
            U.User(**util.get_kwargs_for(U.User, {U.User.nick: 'eeee', U.User.email: 'e@e.e', U.User.passwd: '$5$rounds=535000$GFRsRdCT1wAJynUx$DJJRdHK/wY1LZdj0sA8enCtWGpCkBlYfwSN0PYKvcHD', U.User.approved: True})),
        ]
        db.session.add_all(users)
        del users
    user_0_id=db.session.execute(select(U.User.id).where(U.User.nick==default_usr_nick, U.User.id==0)).scalar_one()

    if U.UsersGroups.query.first() is None:
        users_groups={ug.group: ug.id for ug in db.session.execute(select(U.UserGroup)).scalars().all()}
        users_groups=[
            *[
                U.UsersGroups(**util.get_kwargs_for(U.UsersGroups, {
                    U.UsersGroups.user_id: u,
                    U.UsersGroups.group_id: users_groups[U.UserGroupEnum.Author],
                })) for u in db.session.execute(select(U.User.id)).scalars().all()
            ],
            U.UsersGroups(**util.get_kwargs_for(U.UsersGroups, {
                U.UsersGroups.user_id: user_0_id,
                U.UsersGroups.group_id: users_groups[U.UserGroupEnum.Editor],
            })),
            U.UsersGroups(**util.get_kwargs_for(U.UsersGroups, {
                U.UsersGroups.user_id: user_0_id,
                U.UsersGroups.group_id: users_groups[U.UserGroupEnum.Reviewer],
            })),
            *[
                U.UsersGroups(**util.get_kwargs_for(U.UsersGroups, {
                    U.UsersGroups.user_id: id,
                    U.UsersGroups.group_id: users_groups[U.UserGroupEnum.Editor],
                })) for id in (1, 2)
            ],
            *[
                U.UsersGroups(**util.get_kwargs_for(U.UsersGroups, {
                    U.UsersGroups.user_id: id,
                    U.UsersGroups.group_id: users_groups[U.UserGroupEnum.Reviewer],
                })) for id in (3, 4, 5)
            ],
        ]
        db.session.add_all(users_groups)
        del users_groups

    if CodePurpose.query.first() is None:
        purposes = [
            CodePurpose(**util.get_kwargs_for(CodePurpose, {CodePurpose.purpose: p})) for p in CodePurposeEnum
        ]
        db.session.add_all(purposes)
        del purposes
    
    if ArticleStatus.query.first() is None:
        statuses = [
            ArticleStatus(**util.get_kwargs_for(ArticleStatus, {ArticleStatus.stat: e})) for e in ArticleStatusEnum
        ]
        db.session.add_all(statuses)
        del statuses

    if ReviewStatus.query.first() is None:
        statuses = [
            ReviewStatus(**util.get_kwargs_for(ReviewStatus, {ReviewStatus.stat: e})) for e in ReviewStatusEnum
        ]
        db.session.add_all(statuses)
        del statuses
    
    if Article.query.first() is None:
        status_id=db.session.execute(select(ArticleStatus.id).where(ArticleStatus.stat==ArticleStatusEnum.Submitted).limit(1)).scalar_one()
        articles = [
            Article(**util.get_kwargs_for(Article, {Article.title: 'Introduction to Flask', Article.author_id: 1, Article.status_id: status_id, Article.editor_id: 2})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Understanding REST APIs', Article.author_id: 2, Article.status_id: status_id, Article.editor_id: 1})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Advanced Flask Techniques', Article.author_id: 3, Article.status_id: status_id, Article.editor_id: 1})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Advanced Flask Techniques2', Article.author_id: 3, Article.status_id: status_id, Article.editor_id: 1})),
            Article(**util.get_kwargs_for(Article, {Article.title: 'Common Pitfalls', Article.author_id: 2, Article.status_id: status_id, Article.editor_id: 1})),
        ]
        db.session.add_all(articles)
        del status_id, articles
    
    if Q.Question.query.first() is None:
        questions = [
            Q.Question(**util.get_kwargs_for(Q.Question, {Q.Question.user_id: user_0_id, Q.Question.question: 'Comments', Q.Question.is_abc: False})),
            Q.Question(**util.get_kwargs_for(Q.Question, {Q.Question.user_id: user_0_id, Q.Question.question: 'Rating', Q.Question.is_abc: True})),
        ]
        db.session.add_all(questions)
        del questions
    
    if Q.QuestionA.query.first() is None:
        question_as = [
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Fine as it is'})),
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Requires small changes'})),
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Needs major revisions'})),
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: 2, Q.QuestionA.answer: 'Rejected'})),
        ]
        db.session.add_all(question_as)
        del question_as
    
    if Q.QuestionGroup.query.first() is None:
        question_groups = [
            Q.QuestionGroup(**util.get_kwargs_for(Q.QuestionGroup, {Q.QuestionGroup.user_id: user_0_id, Q.QuestionGroup.name: 'Default Question Group'})),
        ]
        db.session.add_all(question_groups)
        del question_groups
    
    if Q.QuestionGroupQuestions.query.first() is None:
        question_group_questions = [
            Q.QuestionGroupQuestions(**util.get_kwargs_for(Q.QuestionGroupQuestions, {Q.QuestionGroupQuestions.question_group_id: 1, Q.QuestionGroupQuestions.question_id: 1})),
            Q.QuestionGroupQuestions(**util.get_kwargs_for(Q.QuestionGroupQuestions, {Q.QuestionGroupQuestions.question_group_id: 1, Q.QuestionGroupQuestions.question_id: 2})),
        ]
        db.session.add_all(question_group_questions)
        del question_group_questions
        
    if Round.query.first() is None:
        rounds = [
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'This is a beginner-friendly guide to Flask.', Round.article_id: 1, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Explores RESTful APIs and their best practices.', Round.article_id: 2, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Delves into advanced techniques in Flask.', Round.article_id: 3, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Further techniques in Flask for experienced users.', Round.article_id: 4, Round.round_number: 1})),
            Round(**util.get_kwargs_for(Round, {Round.article_content: 'Discusses common pitfalls to avoid in Flask.', Round.article_id: 5, Round.round_number: 1})),
        ]
        db.session.add_all(rounds)
        del rounds
    
    db.session.commit()