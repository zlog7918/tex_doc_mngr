from db.db_base import db
from sqlalchemy import and_, or_
from models.usr.User import User
from . import user_service as su
from models.utils import utils as util
from models.article import Questions as Q
from models.utils.MessageException import MessageException

def _cr_or_err(q: Q.Question|Q.QuestionA|Q.QuestionGroup|Q.QuestionGroupQuestions, err_str: str) -> None:
    try:
        db.session.add(q)
        db.session.flush()
    except Exception as e:
        if 'unique constraint' not in str(e):
            raise e.with_traceback(e.__traceback__) from None
        else:
            raise MessageException(err_str, e)

def get_all_questions(usr: User) -> list[Q.Question]:
    usr0=su.get_usr0_or_err()
    return Q.Question.query.where(or_(
        Q.Question.user_id==usr.id,
        Q.Question.user_id==usr0.id,
    )).all()

def get_all_question_groups(usr: User) -> list[Q.QuestionGroup]:
    usr0=su.get_usr0_or_err()
    return Q.QuestionGroup.query.where(or_(
        Q.QuestionGroup.user_id==usr.id,
        Q.QuestionGroup.user_id==usr0.id,
    )).all()

def get_question(q_id: int) -> Q.Question|None:
    return Q.Question.query.where(Q.Question.id==q_id).first()

def get_question_group(qg_id: int) -> Q.QuestionGroup|None:
    return Q.QuestionGroup.query.where(Q.QuestionGroup.id==qg_id).first()

def get_question_by_q(usr: User, question: str) -> Q.Question|None:
    return Q.Question.query.where(and_(
        Q.Question.user_id==usr.id,
        Q.Question.question==question,
    )).first()

def get_question_group_by_n(usr: User, name: str) -> Q.QuestionGroup|None:
    return Q.QuestionGroup.query.where(and_(
        Q.QuestionGroup.user_id==usr.id,
        Q.QuestionGroup.name==name,
    )).first()

def cr_question(usr: User, question: str, abc_s: list[str]|None) -> None:
    lang_pkg=util.get_lang_pkg()
    usr_id=usr.id
    abc_s=[] if abc_s is None else abc_s
    flag=len(abc_s)!=0
    if len(abc_s)==1:
        raise MessageException(lang_pkg.QuestionNeedAtLeastTwoOptions.value)
    _cr_or_err(
        Q.Question(**util.get_kwargs_for(Q.Question, {Q.Question.user_id: usr_id, Q.Question.question: question, Q.Question.is_abc: flag})),
        lang_pkg.QuestionAlreadyExists.value,
    )
    q=get_question_by_q(usr, question)
    if q is None:
        raise MessageException(lang_pkg.QuestionNotCreated.value, Exception('Question not created, but has gone through try...except'))
    if not flag:
        return
    abc_s=list(set(abc_s))
    for abc in abc_s:
        _cr_or_err(
            Q.QuestionA(**util.get_kwargs_for(Q.QuestionA, {Q.QuestionA.question_id: q.id, Q.QuestionA.answer: abc})),
            lang_pkg.QuestionAnsAlreadyExists.value,
        )

def cr_question_group(usr: User, name: str, questions: list[int]) -> None:
    lang_pkg=util.get_lang_pkg()
    usr_id=usr.id
    _cr_or_err(
        Q.QuestionGroup(**util.get_kwargs_for(Q.QuestionGroup, {Q.QuestionGroup.user_id: usr_id, Q.QuestionGroup.name: name})),
        lang_pkg.QuestionGroupAlreadyExists.value,
    )
    qg=get_question_group_by_n(usr, name)
    if qg is None:
        raise MessageException(lang_pkg.QuestionGroupNotCreated.value, Exception('Question group not created, but has gone through try...except'))
    questions=list(set(questions))
    for q in questions:
        _cr_or_err(
            Q.QuestionGroupQuestions(**util.get_kwargs_for(Q.QuestionGroupQuestions, {Q.QuestionGroupQuestions.question_group_id: qg.id, Q.QuestionGroupQuestions.question_id: q})),
            lang_pkg.QuestionInQuestionGroupAlreadyExists.value,
        )
