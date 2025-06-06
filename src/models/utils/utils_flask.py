import os.path
import typing as t
from . import utils as util
from ..usr import User as U
from models.lang import LangEnum
from .EnvConsts import envConsts as ec
from services import user_service as us
from flask import render_template, url_for

def url_last_edit(path: str) -> str:
    if not path.startswith('/static/'):
        return f'{path}?t=ERROR'
    if '/..' in path:
        return f'{path}?t=ERROR'
    path_abs=f'{ec.getAppDir()}{path}'
    return f'{path}?t={int(os.path.getmtime(path_abs))}'

P=t.ParamSpec('P')

def _url_with_lang_for(_: t.Callable[t.Concatenate[str, P], str]=url_for) -> t.Callable[t.Concatenate[str, P], str]:
    def func(endpoint: str, *args: P.args, **kwargs: P.kwargs) -> str:
        path=url_for(endpoint, *args, **kwargs)
        return url_for('choose_lang', lang=LangEnum(util.get_lang_pkg()), path=path.removeprefix('/'))
    return func
url_with_lang_for=_url_with_lang_for()
del _url_with_lang_for

def _render_base_template(url_with_lang_for: t.Callable[..., str], _: t.Callable[t.Concatenate[str, P], str]=render_template) -> t.Callable[t.Concatenate[str, P], str]:
    def func(name: str, *args: P.args, **kwargs: P.kwargs) -> str:
        curr_user=us.get_curr_user()
        return render_template(
            name,
            *args,
            curr_user_groups=set() if curr_user is None else {ug.group.group for ug in curr_user.groups},
            user_group_enum=U.UserGroupEnum,
            url_last_edit=url_last_edit,
            url_with_lang_for=url_with_lang_for,
            lang_pkg=util.get_lang_pkg(),
            **kwargs
        )
    return func
render_base_template=_render_base_template(url_with_lang_for)
del _render_base_template