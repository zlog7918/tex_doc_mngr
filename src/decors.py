from flask import abort
from functools import wraps
from models.usr.User import User
from flask_login import current_user

def approve_required(f):
    @wraps(f)
    def func(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        user: User=current_user
        if not user.is_approved():
            abort(401)
        return f(*args, **kwargs)
    return func