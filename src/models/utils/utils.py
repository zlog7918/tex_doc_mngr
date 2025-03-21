import sys
import os.path
from . import consts as c
from flask import render_template, g
from datetime import datetime,timezone
from models.lang import LangEnum, LangBase

def url_last_edit(path: str) -> str:
    if not path.startswith('/static/'):
        return f'{path}?t=ERROR'
    if '/..' in path:
        return f'{path}?t=ERROR'
    path_abs=f'{os.environ.get('APP_DIR')}{path}'
    return f'{path}?t={int(os.path.getmtime(path_abs))}'

def render_base_template(name: str, **kwargs) -> str:
    return render_template(name, url_last_edit=url_last_edit, **kwargs)

def set_lang_pkg(lang: LangEnum) -> None:
    g.lang=lang.value

def get_lang_pkg() -> type[LangBase]:
    if 'lang' not in g:
        lang=LangEnum.EN.value
        g.lang=lang
    return g.lang

def get_upload_folder() -> str:
    return os.getenv('DOC_FILES_DIR', '/var/www/uploads')

def get_temp_folder() -> str:
    return os.getenv('TEMP_FOLDER', '/tmp')

def get_timestamp() -> datetime:
    return datetime.now(timezone.utc)

def get_function(back: int=0) -> str:
    frame=sys._getframe(back+1)
    return f'{frame.f_code.co_filename}:{frame.f_lineno} {frame.f_code.co_name}()'

def validate_pass(passwd: str) -> bool:
    SpecialSym=set(c.ALLOWED_SPECIAL_CHARS_IN_PASSWORDS)
    p_n=len(passwd)
    if p_n<c.MIN_PWD_LEN or p_n>c.MAX_PWD_LEN:
        return False

    is_digit=is_upper=is_lower=is_special=0
    for char in passwd:
        if char.isdigit():
            is_digit=1
        if char.isupper():
            is_upper=1
        if char.islower():
            is_lower=1
        if char in SpecialSym:
            is_special=1
        if not (char.islower() or char.isdigit() or char.isupper() or (char in SpecialSym)):
            return False
    if (is_digit+is_lower+is_special+is_upper)<4:
        return False
    return True
