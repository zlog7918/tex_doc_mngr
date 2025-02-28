import sys
import random
import os.path
from flask import render_template
from datetime import datetime,timezone
from .consts import TIME_TO_EXPIRE, ALLOWED_SPECIAL_CHARS_IN_PASSWORDS

def url_last_edit(path: str) -> str:
    if not path.startswith('/static/'):
        return f'{path}?t=ERROR'
    if '/..' in path:
        return f'{path}?t=ERROR'
    path_abs=f'{os.environ.get('APP_DIR')}{path}'
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
    return code, TIME_TO_EXPIRE

def get_timestamp() -> datetime:
    return datetime.today().astimezone(tz=timezone.utc)

def get_function(back: int=0) -> str:
    frame=sys._getframe(back+1)
    return f'{frame.f_code.co_filename}:{frame.f_lineno} {frame.f_code.co_name}()'

def validate_pass(passwd: str) -> bool:
    SpecialSym=set(ALLOWED_SPECIAL_CHARS_IN_PASSWORDS)
    p_n=len(passwd)
    if p_n<8 or p_n>50:
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
            is_upper=1
        if not (char.islower() or char.isdigit() or char.isupper() or (char in SpecialSym)):
            return False
    if (is_digit+is_lower+is_special+is_upper)<3:
        return False
    return True
