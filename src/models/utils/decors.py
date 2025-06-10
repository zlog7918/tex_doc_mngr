import typing as t
from flask import abort
from functools import wraps
from . import utils as util
from ..usr import User as U
from .Response import Response
from db.db_base import db, log_err
from services import user_service as su
from flask.typing import ResponseReturnValue
from .MessageException import MessageException
from .FormNotFilledException import FormNotFilledException

_PWrapped=t.ParamSpec('_PWrapped')
_RWrapped=t.TypeVar('_RWrapped')
_PWrapper=t.ParamSpec('_PWrapper')
_RWrapper=t.TypeVar('_RWrapper')
class _Wrapped(t.Generic[_PWrapped, _RWrapped, _PWrapper, _RWrapper]):
    __wrapped__: t.Callable[_PWrapped, _RWrapped]
    def __call__(self, *args: _PWrapper.args, **kwargs: _PWrapper.kwargs) -> _RWrapper: ...
    __name__: str
    __qualname__: str
def __ret_wrapped(f: t.Callable[_PWrapped, _RWrapped]) -> t.Callable[[t.Callable[_PWrapper, _RWrapper]], _Wrapped[_PWrapped, _RWrapped, _PWrapped, _RWrapper]]:
    def _func(fun: t.Callable[_PWrapper, _RWrapper]) -> _Wrapped[_PWrapped, _RWrapped, _PWrapped, _RWrapper]:
        @wraps(f)
        def func(*args: _PWrapper.args, **kwargs: _PWrapper.kwargs) -> _RWrapper:
            return fun(*args, **kwargs)
        return func # type: ignore
    return _func

def __is_loggedin() -> U.User:
    user=su.get_curr_user()
    if user is None:
        abort(401)
    return user

def __is_approved() -> U.User:
    user=__is_loggedin()
    if not user.approved:
        abort(401)
    return user

def __is_group(get_user_func: t.Callable[[], U.User], group: U.UserGroupEnum) -> U.User:
    user=get_user_func()
    user_groups={ug.group.group for ug in user.groups}
    if group not in user_groups:
        abort(401)
    return user

P=t.ParamSpec('P')
def login_required(f: t.Callable[P, ResponseReturnValue]) -> _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]:
    @__ret_wrapped(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        __is_loggedin()
        return f(*args, **kwargs)
    return func

def approve_required(f: t.Callable[P, ResponseReturnValue]) -> _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]:
    @__ret_wrapped(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        __is_approved()
        return f(*args, **kwargs)
    return func

def group_required(group: U.UserGroupEnum, is_approve_req: bool=True) -> t.Callable[[t.Callable[P, ResponseReturnValue]], _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]]:
    def group_required(f: t.Callable[P, ResponseReturnValue]) -> _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]:
        @__ret_wrapped(f)
        def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
            __is_group(__is_approved if is_approve_req else __is_loggedin, group)
            return f(*args, **kwargs)
        return func
    return group_required

def log_if_error(f: t.Callable[P, Response]) -> _Wrapped[P, Response, P, Response]:
    @__ret_wrapped(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> Response:
        try:
            try:
                try: db.session.begin()
                except Exception: pass
                ret=f(*args, **kwargs)
                db.session.commit()
                return ret
            except MessageException as e:
                db.session.rollback()
                if e.is_to_log():
                    # print(type(e), e, util.get_traceback(e))
                    # l=e.get_err_to_log()
                    # print(type(l), l, util.get_traceback(l))
                    log_err(e.get_err_to_log())
                    db.session.commit()
                return Response.error_response(str(e), e.get_data())
            except Exception as e:
                db.session.rollback()
                log_err(e)
                db.session.commit()
                return Response.error_response(message=util.get_lang_pkg().UnknownErr.value)
        except Exception as e:
            db.session.rollback()
            print(f'{type(e)} {e}\nTimestamp: {util.get_timestamp().isoformat()}\nTraceback:\n{util.get_traceback(e)}')
            return Response.error_response(message=util.get_lang_pkg().UnknownDBErr.value)
    return func

def handle_form_not_filled(f: t.Callable[P, ResponseReturnValue]) -> _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]:
    @__ret_wrapped(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        try:
            return f(*args, **kwargs)
        except FormNotFilledException as e:
            return Response.error_response(message=str(e)).to_dict()
    return func
