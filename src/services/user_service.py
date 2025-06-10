import typing as t
import pickle as pkl
import sqlalchemy as sqla
from db.db_base import db
from models.usr import User as U
from flask_login import current_user
from models.utils import utils as util
from models.utils.MessageException import MessageException

def __get_user_group_or_err(group: U.UserGroupEnum) -> U.UserGroup:
    _group=U.UserGroup.query.where(U.UserGroup.group==group).first()
    if _group is None:
        raise ValueError(f'Given user group: {group.name} does not exist in db')
    return _group

def get_user(id: int) -> U.User|None:
    return U.User.query.where(U.User.id==id).first()

def get_user_by_nick(nick: str) -> U.User|None:
    return U.User.query.where(U.User.nick==nick).first()

def get_user_by_email(email: str) -> U.User|None:
    return U.User.query.where(U.User.email==email).first()

def get_user_id(nick: str) -> int:
    # TODO: split handling exceptions and handling non-existing user
    try:
        user=get_user_by_nick(nick)
        if user is None:
            raise MessageException(f'{nick}')
        return user.id
    except MessageException as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.UserNotFoundErr.value(e)) from None

def get_curr_user() -> U.User|None:
    try:
        u=current_user._get_current_object() # type: ignore[private_access]
    except RuntimeError:
        return None
    if u is None:
        return None
    if isinstance(u, U.User):
        return u
    return None

def get_curr_user_or_err() -> U.User:
    u=get_curr_user()
    if u is None:
        lang_pkg=util.get_lang_pkg()
        raise MessageException(lang_pkg.UserNotLogged.value)
    return u

def get_usr0_or_err() -> U.User:
    u=get_user(0)
    if u is None:
        lang_pkg=util.get_lang_pkg()
        raise MessageException(lang_pkg.User0NotFound.value, Exception('U.User id: 0 is not found'))
    return u

def add_user(user: U.User) -> None:
    try:
        db.session.add(user)
        db.session.flush()
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.UserNotAdded.value)

def add_user_to_group(user: U.User, _group: U.UserGroupEnum) -> None:
    group=__get_user_group_or_err(_group)
    ug=U.UsersGroups(**util.get_kwargs_for(U.UsersGroups, {
        U.UsersGroups.user_id: user.id,
        U.UsersGroups.group_id: group.id,
    }))
    try:
        db.session.add(ug)
        db.session.flush()
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.UserNotAddedToGroup.value)

def approve_user(user: U.User) -> None:
    try:
        user.approve()
        db.session.flush()
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.UserNotApproved.value)

def delete_user(user: U.User) -> None:
    try:
        db.session.delete(user)
        db.session.flush()
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.UserNotDeleted.value)

def change_user_pass(user: U.User, passwd: str) -> bool:
    try:
        if user.ch_pass(passwd):
            db.session.flush()
            return True
        return False
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.PasswordNotChanged.value)

TVT=t.TypeVarTuple('TVT')
def map_args(user: U.User, args: tuple[*TVT]) -> tuple[*TVT]:
    l: list=[]
    for v in args:
        if isinstance(v, U.User_params):
            if v==U.User_params.self:
                v=user
            elif v==U.User_params.id:
                v=user.id
            elif v==U.User_params.nick:
                v=user.nick
            elif v==U.User_params.email:
                v=user.email
        l.append(v)
    return tuple(l)

P=t.ParamSpec('P')
def _exec_funcs(do: t.Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> None:
    try:
        do(*args, **kwargs)
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.FuncNotExecuted.value)

def set_user_nick(user: U.User, nick: str) -> None:
    try:
        if user.do_after_cr is not None:
            todo: list[tuple[t.Callable[..., object], tuple[object, ...]]]=pkl.loads(user.do_after_cr)
            for do, args in todo:
                _exec_funcs(do, *map_args(user, args))
            user.do_after_cr=None
        db.session.flush()
        user.nick=nick
        db.session.flush()
    except Exception as e:
        lang_pkg=util.get_lang_pkg()
        raise MessageException.from_exception(e, lang_pkg.AccountNotCreated.value)

def get_group_users_and_not(user_group: U.UserGroupEnum) -> tuple[list[U.User], list[U.User]]:
    usr0=get_usr0_or_err()
    users=db.session.execute(
        sqla.select(U.User)
            .where(U.User.id!=usr0.id)
            .where(U.User.nick!=None)
    ).scalars().all()
    is_arr=[]
    is_not_arr=[]
    for user in users:
        if user_group in {ug.group.group for ug in user.groups}:
            is_arr.append(user)
        else:
            is_not_arr.append(user)
    return is_arr, is_not_arr
def get_editors_and_not() -> tuple[list[U.User], list[U.User]]:
    return get_group_users_and_not(U.UserGroupEnum.Editor)
def get_reviewers_and_not() -> tuple[list[U.User], list[U.User]]:
    return get_group_users_and_not(U.UserGroupEnum.Reviewer)
