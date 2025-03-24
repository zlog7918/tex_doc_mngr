import pickle as pkl
from db.db_base import db
from flask_login import current_user
from models.usr.User import User, User_params
from typing import Callable, ParamSpec, TypeVarTuple
from models.utils.MessageException import MessageException

def get_user(id: int) -> User|None:
    return User.query.where(User.id==id).first()

def get_user_by_nick(nick: str) -> User|None:
    return User.query.where(User.nick==nick).first()

def get_user_by_email(email: str) -> User|None:
    return User.query.where(User.email==email).first()

def get_user_id(nick: str) -> int:
    # TODO: split handling exceptions and handling non-existing user
    try:
        user=get_user_by_nick(nick)
        if user is None:
            raise MessageException(f'{nick}')
        return user.id
    except MessageException as e:
        raise MessageException.from_exception(e, f'Nie znaleziono użytkownika: {str(e)}') from None

def get_curr_user() -> User|None:
    try:
        u=current_user._get_current_object() # type: ignore[private_access]
    except RuntimeError:
        return None
    if u is None:
        return None
    if isinstance(u, User):
        return u
    return None

def get_curr_user_or_err() -> User:
    u=get_curr_user()
    if u is None:
        raise MessageException('Nie jest zalogowany, żaden użytkownik')
    return u

def add_user(user: User):
    try:
        db.session.add(user)
    except Exception as e:
        raise MessageException.from_exception(e, 'Użytkownik nie został dodany')

def approve_user(user: User) -> None:
    try:
        user.approve()
        db.session.flush()
    except Exception as e:
        raise MessageException.from_exception(e, 'Konto nie zostało potwierdzone')

def delete_user(user: User) -> None:
    try:
        db.session.delete(user)
    except Exception as e:
        raise MessageException.from_exception(e, 'Konto nie zostało potwierdzone')

def change_user_pass(user: User, passwd: str) -> bool:
    try:
        if user.ch_pass(passwd):
            db.session.flush()
            return True
        return False
    except Exception as e:
        raise MessageException.from_exception(e, 'Hasło nie zostało zmienione')

TVT=TypeVarTuple('TVT')
def map_args(user: User, args: tuple[*TVT]) -> tuple[*TVT]:
    l: list=[]
    for v in args:
        if isinstance(v, User_params):
            if v==User_params.self:
                v=user
            elif v==User_params.id:
                v=user.id
            elif v==User_params.nick:
                v=user.nick
            elif v==User_params.email:
                v=user.email
        l.append(v)
    return tuple(l)

P=ParamSpec('P')
def exec_funcs(do: Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> None:
    try:
        do(*args, **kwargs)
    except Exception as e:
        raise MessageException.from_exception(e, 'Nie wykonano funkcji')

def set_user_nick(user: User, nick: str) -> None:
    try:
        user.nick=nick
        if user.do_after_cr is not None:
            todo: list[tuple[Callable[..., object], tuple[object, ...]]]=pkl.loads(user.do_after_cr)
            for do, args in todo:
                exec_funcs(do, *map_args(user, args))
            user.do_after_cr=None
        db.session.flush()
    except Exception as e:
        raise MessageException.from_exception(e, 'Konto nie zostało utworzone')
