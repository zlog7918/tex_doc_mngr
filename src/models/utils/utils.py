import sys
import random
import os.path
from flask import render_template
from .consts import TIME_TO_EXPIRE
from datetime import datetime,timezone

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
    frame = sys._getframe(back+1)
    return f'{frame.f_code.co_filename}:{frame.f_lineno} {frame.f_code.co_name}()'
