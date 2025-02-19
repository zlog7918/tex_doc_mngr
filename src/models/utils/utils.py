import os.path
from flask import render_template

def url_last_edit(path: str) -> str:
    if not path.startswith('/static/'):
        return f'{path}?t=ERROR'
    if '/..' in path:
        return f'{path}?t=ERROR'
    path_abs=f'{os.environ.get('APP_DIR')}{path}'
    return f'{path}?t={int(os.path.getmtime(path_abs))}'

def render_base_template(name: str, **kwargs) -> str:
    return render_template(name, url_last_edit=url_last_edit, **kwargs)

def get_upload_folder():
    return os.getenv('DOC_FILES_DIR', '/var/www/uploads')

def get_temp_folder():
    return os.getenv('TEMP_FOLDER', '/tmp')