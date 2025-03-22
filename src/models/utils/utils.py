import sys
import random
import os.path
from . import consts as c
from flask import render_template
from datetime import datetime
from .EnvConsts import envConsts as ec
from tzlocal import get_localzone
from datetime import datetime,tzinfo

def url_last_edit(path: str) -> str:
    if not path.startswith('/static/'):
        return f'{path}?t=ERROR'
    if '/..' in path:
        return f'{path}?t=ERROR'
    path_abs=f'{ec.getAppDir()}{path}'
    return f'{path}?t={int(os.path.getmtime(path_abs))}'

def render_base_template(name: str, **kwargs) -> str:
    return render_template(name, url_last_edit=url_last_edit, **kwargs)

def get_upload_folder() -> str:
    return os.getenv('DOC_FILES_DIR', '/var/www/uploads')

def get_temp_folder() -> str:
    return os.getenv('TEMP_FOLDER', '/tmp')

def generate_code() -> tuple[str, int]:
    r=random.Random()
    code=r.randint(0, 999999)
    code=f"{code:06d}"
    return code, c.TIME_TO_EXPIRE

def unifide_timezone() -> tzinfo:
    return get_localzone()

def get_timestamp(tz: tzinfo=unifide_timezone()) -> datetime:
    return datetime.now(tz)

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
