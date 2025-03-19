from flask import abort
from functools import wraps
from . import utils as util
from .Response import Response
from services import user as su
from db.db_base import db, log_err
from typing import Callable, ParamSpec
from flask.typing import ResponseReturnValue
from .MessageException import MessageException

P=ParamSpec('P')

def approve_required(f: Callable[P, ResponseReturnValue]) -> Callable[P, ResponseReturnValue]:
    @wraps(f)
    def func(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
        user=su.get_curr_user()
        if user is None:
            abort(401)
        if not user.is_approved():
            abort(401)
        return f(*args, **kwargs)
    return func

def log_if_error(f: Callable[P, Response]) -> Callable[P, Response]:
    @wraps(f)
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
                    log_err(e.get_err_to_log())
                    db.session.commit()
                return Response.error_response(message=str(e))
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