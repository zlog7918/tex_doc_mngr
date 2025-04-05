import traceback
from flask import Flask
from pathlib import Path
from src import app as a
from functools import wraps
from threading import Thread
from werkzeug.serving import make_server
from test_utils import testing_consts as tconst
from typing import Callable, ParamSpec, TypeVar, Generic, Self

_PWrapped=ParamSpec('_PWrapped')
_RWrapped=TypeVar('_RWrapped')
_PWrapper=ParamSpec('_PWrapper')
_RWrapper=TypeVar('_RWrapper')
class _Wrapped(Generic[_PWrapped, _RWrapped, _PWrapper, _RWrapper]):
    __wrapped__: Callable[_PWrapped, _RWrapped]
    def __call__(self, *args: _PWrapper.args, **kwargs: _PWrapper.kwargs) -> _RWrapper: ...
    __name__: str
    __qualname__: str
def _ret_wrapped(f: Callable[_PWrapped, _RWrapped]) -> Callable[[Callable[_PWrapper, _RWrapper]], _Wrapped[_PWrapped, _RWrapped, _PWrapper, _RWrapper]]:
    def _func(fun: Callable[_PWrapper, _RWrapper]) -> _Wrapped[_PWrapped, _RWrapped, _PWrapper, _RWrapper]:
        @wraps(f)
        def func(*args: _PWrapper.args, **kwargs: _PWrapper.kwargs) -> _RWrapper:
            return fun(*args, **kwargs)
        return func # type: ignore
    return _func

class _ServerThread(Thread):
    def __init__(self, app: Flask):
        super().__init__()
        self.server=make_server(tconst.HOST, tconst.PORT, app)
        self.__get_ctx=app.app_context
        self.ctx=app.app_context()
        self.ctx.push()
    def run(self):
        self.server.serve_forever()
    def get_context(self):
        return self.__get_ctx()
    def shutdown(self):
        self.server.shutdown()


def _build_server(f: Callable[[_ServerThread], None]) -> _Wrapped[[_ServerThread], None, [], None]:
    @_ret_wrapped(f)
    def func() -> None:
        db_path=Path('./testdb.db')
        if db_path.exists():
            if db_path.is_file():
                db_path.unlink()
            else:
                raise Exception(f'On path: {db_path} is directory')
        app=a.cr_app()
        config_name='SQLALCHEMY_DATABASE_URI'
        old_val=app.config[config_name]
        app.config[config_name]=f'sqlite:///{db_path.absolute()}'
        a.init_app(app)
        server=_ServerThread(app)
        server.start()

        flag=True
        try:
            f(server)
            flag=False
        except Exception as e:
            print(type(e), e, ''.join(traceback.format_tb(e.__traceback__)))

        server.shutdown()
        if db_path.is_file():
            db_path.unlink()
        app.config[config_name]=old_val
        if flag:
            raise Exception('Cause given above^')
    return func

class _TestingUnit:
    def __init__(self) -> None:
        self._tests: list[_Wrapped[[_ServerThread], None, [], None]]=[]
    
    def add_blueprint(self, tub: "_TestingUnit") -> None:
        self._tests.extend(tub._tests)
    def test_resp_with_context(self, f: Callable[[], None]) -> _Wrapped[[_ServerThread], None, [], None]:
        @_build_server
        def func(server: _ServerThread) -> None:
            with server.get_context():
                f()
        self._tests.append(func)
        return func
    def test_resp(self, f: Callable[[], None]) -> _Wrapped[[_ServerThread], None, [], None]:
        @_build_server
        def func(server: _ServerThread) -> None:
            f()
        self._tests.append(func)
        return func

class TestingUnitBlueprint(_TestingUnit):
    def __init__(self, *args: "TestingUnitBlueprint") -> None:
        super().__init__()
        for arg in args:
            self.add_blueprint(arg)

class TestingUnit(_TestingUnit):
    def __init__(self) -> None:
        super().__init__()
    def exec(self) -> None:
        for t in self._tests:
            t()

