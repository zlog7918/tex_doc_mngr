from flask import abort
from functools import wraps
from .services import user as su

def approve_required(f):
    @wraps(f)
    def func(*args, **kwargs):
        user=su.get_curr_user()
        if user is None:
            abort(401)
        if not user.is_approved():
            abort(401)
        return f(*args, **kwargs)
    return func