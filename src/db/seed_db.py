from models.usr.User import User
from flask_sqlalchemy import SQLAlchemy
from models.usr.Code import CodePurpose, CodePurposeEnum
from models.article.Article import Article, ArticleStatus, ArticleStatusEnum
from models.article.Questions import Question, QuestionA, QuestionSet, QuestionSetQuestions

def seed_data(db: SQLAlchemy) -> None:
    if not User.query.first():
        users = [
            User(nick='aaaa', email='a@wp.pl', passwd='$5$rounds=535000$wuEj7JxeY4UcsyOi$gQJ9v/eCcHdbrbLAriGeRQVSJfnzAzQoOMkQeiJvprC', approved=True),
            User(nick='bbbb', email='b@wp.pl', passwd='$5$rounds=535000$wuEj7JxeY4UcsyOi$gQJ9v/eCcHdbrbLAriGeRQVSJfnzAzQoOMkQeiJvprC', approved=True),
            User(nick='cccc', email='c@wp.pl', passwd='$5$rounds=535000$wuEj7JxeY4UcsyOi$gQJ9v/eCcHdbrbLAriGeRQVSJfnzAzQoOMkQeiJvprC', approved=True),
        ]
        db.session.add_all(users)
    
    if not CodePurpose.query.first():
        purposes = [
            CodePurpose(purpose=p) for p in CodePurposeEnum
        ]
        db.session.add_all(purposes)
    
    if not ArticleStatus.query.first():
        statuses = [
            ArticleStatus(stat=e) for e in ArticleStatusEnum
        ]
        db.session.add_all(statuses)
    
    if not Article.query.first():
        status_id=ArticleStatus.query.where(ArticleStatus.stat==ArticleStatusEnum.Submitted).first().id
        articles = [
            Article(title='Introduction to Flask', author_id=1, content='This is a beginner-friendly guide to Flask.', status_id=status_id, editor_id=1),
            Article(title='Understanding REST APIs', author_id=2, content='Explores RESTful APIs and their best practices.', status_id=status_id, editor_id=1),
            Article(title='Advanced Flask Techniques', author_id=3, content='Delves into advanced techniques in Flask.', status_id=status_id, editor_id=1),
            Article(title='Advanced Flask Techniques2', author_id=3, content='Further techniques in Flask for experienced users.', status_id=status_id, editor_id=1),
            Article(title='Common Pitfalls', author_id=2, content='Discusses common pitfalls to avoid in Flask.', status_id=status_id, editor_id=1),
        ]
        db.session.add_all(articles)
    
    if not Question.query.first():
        questions = [
            Question(question='Comments', is_abc=False),
            Question(question='Rating', is_abc=True),
        ]
        db.session.add_all(questions)
    
    if not QuestionA.query.first():
        question_as = [
            QuestionA(question_id=2, answer='Fine as it is'),
            QuestionA(question_id=2, answer='Requires small changes'),
            QuestionA(question_id=2, answer='Needs major revisions'),
            QuestionA(question_id=2, answer='Rejected'),
        ]
        db.session.add_all(question_as)
    
    if not QuestionSet.query.first():
        question_sets = [QuestionSet(name='Default Question Set')]
        db.session.add_all(question_sets)
    
    if not QuestionSetQuestions.query.first():
        question_set_questions = [
            QuestionSetQuestions(question_set_id=1, question_id=1),
            QuestionSetQuestions(question_set_id=1, question_id=2),
        ]
        db.session.add_all(question_set_questions)
    
    db.session.commit()