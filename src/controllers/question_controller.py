from models.usr.User import User
from db.db_base import log_activity
from models.utils.Response import Response
from models.utils import utils as util, decors as decor
from models.utils.MessageException import MessageException
from services import user_service as su, question_service as sq

def _does_user_has_access(user: User, owner_id: int) -> bool:
    return owner_id==user.id or owner_id==su.get_usr0_or_err().id

@decor.log_if_error
def get_all_questions() -> Response:
    return Response.success_response(
        sq.get_all_questions(su.get_curr_user_or_err())
    )

@decor.log_if_error
def get_question(q_id: int) -> Response:
    usr=su.get_curr_user_or_err()
    lang_pkg=util.get_lang_pkg()
    q=sq.get_question(q_id)
    if q is None:
        raise MessageException(lang_pkg.QuestionNotFound.value)
    if not _does_user_has_access(usr, q.user_id):
        raise MessageException(lang_pkg.QuestionNotFound.value, Exception(f'Illegal access attempt on guestion [id: {q_id}]'))
    return Response.success_response(q)

@decor.log_if_error
def cr_question(question: str, abc_s: list[str]|None) -> Response:
    usr=su.get_curr_user_or_err()
    sq.cr_question(usr, question, abc_s)
    log_activity(True, {'message': f'Successfully created question [{question}]'})
    return Response.success_response()

@decor.log_if_error
def get_all_question_groups() -> Response:
    return Response.success_response(
        sq.get_all_question_groups(su.get_curr_user_or_err())
    )

@decor.log_if_error
def get_question_group(qg_id: int) -> Response:
    usr=su.get_curr_user_or_err()
    lang_pkg=util.get_lang_pkg()
    qg=sq.get_question_group(qg_id)
    if qg is None:
        raise MessageException(lang_pkg.QuestionGroupNotFound.value)
    if not _does_user_has_access(usr, qg.user_id):
        raise MessageException(lang_pkg.QuestionGroupNotFound.value, Exception(f'Illegal access attempt on guestion group [id: {qg_id}]'))
    return Response.success_response(qg)

@decor.log_if_error
def cr_question_group(name: str, questions: list[int]) -> Response:
    usr=su.get_curr_user_or_err()
    lang_pkg=util.get_lang_pkg()
    if not all(
        False if q is None else _does_user_has_access(usr, q.user_id) for q in (
            sq.get_question(q_id) for q_id in questions
        )
    ):
        raise MessageException(lang_pkg.QuestionNotFound.value, Exception(f'Illegal access attempt with guestions [{questions}]'))
    sq.cr_question_group(usr, name, questions)
    log_activity(True, {'message': f'Successfully created question group [name: {name}]'})
    return Response.success_response()
