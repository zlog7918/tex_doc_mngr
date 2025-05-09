from flask import abort
from functools import wraps
from . import utils as util
from .Response import Response
from services import user as su
from db.db_base import db, log_err
from flask.typing import ResponseReturnValue
from .MessageException import MessageException
from typing import Callable, ParamSpec, TypeVar, Generic
from .FormNotFilledException import FormNotFilledException

_PWrapped=ParamSpec('_PWrapped')
_RWrapped=TypeVar('_RWrapped')
_PWrapper=ParamSpec('_PWrapper')
_RWrapper=TypeVar('_RWrapper')
class _Wrapped(Generic[_PWrapped, _RWrapped, _PWrapper, _RWrapper]):
    __wrapped__: Callable[_PWrapped, _RWrapped]
    def __call__(self, *args: _PWrapper.args, **kwargs: _PWrapper.kwargs) -> _RWrapper: ...
    __name__: str
    __qualname__: str
def __ret_wrapped(f: Callable[_PWrapped, _RWrapped]) -> Callable[[Callable[_PWrapper, _RWrapper]], _Wrapped[_PWrapped, _RWrapped, _PWrapped, _RWrapper]]:
    def _func(fun: Callable[_PWrapper, _RWrapper]) -> _Wrapped[_PWrapped, _RWrapped, _PWrapped, _RWrapper]:
        @wraps(f)
        def func(*args: _PWrapper.args, **kwargs: _PWrapper.kwargs) -> _RWrapper:
            return fun(*args, **kwargs)
        return func # type: ignore
    return _func


P=ParamSpec('P')
def approve_required(f: Callable[P, ResponseReturnValue]) -> _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]:
    @__ret_wrapped(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        user=su.get_curr_user()
        if user is None:
            abort(401)
        if not user.is_approved():
            abort(401)
        return f(*args, **kwargs)
    return func

def log_if_error(f: Callable[P, Response]) -> _Wrapped[P, Response, P, Response]:
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
                return Response.error_response(message='Wystąpił nie przewidziany błąd, przepraszamy za utrudnienia')
        except Exception as e:
            db.session.rollback()
            print(f'{type(e)} {e}\nTimestamp: {util.get_timestamp().isoformat()}\nTraceback:\n{util.get_traceback(e)}')
            return Response.error_response(message='Wystąpił poważny błąd serwera, przepraszamy za utrudnienia')
    return func

def handle_form_not_filled(f: Callable[P, ResponseReturnValue]) -> _Wrapped[P, ResponseReturnValue, P, ResponseReturnValue]:
    @__ret_wrapped(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        try:
            return f(*args, **kwargs)
        except FormNotFilledException as e:
            return Response.error_response(message=str(e)).to_dict()
    return func
