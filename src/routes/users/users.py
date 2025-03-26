from flask_login import login_required
from ...models.utils.Response import Response
from flask import Blueprint, redirect, request
from ...controllers import user_controller as uc
from ...models.utils.utils import render_base_template

user_bp = Blueprint('user', __name__)


@user_bp.route('/login', methods=['POST'])
def login():
    nick = request.form.get('nick')
    passwd = request.form.get('passwd')
    if (nick is None) or (passwd is None):
        return Response.error_response(message='Nie pełny formularz').to_dict()
    return uc.login(nick, passwd).to_dict()


@user_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    return uc.logout().to_dict()


@user_bp.route('/signup', methods=['POST'])
def signup():
    nick = request.form.get('nick')
    email = request.form.get('email')
    passwd = request.form.get('passwd')
    rep_passwd = request.form.get('rep_passwd')
    if (nick is None) or (email is None) or (passwd is None) or (rep_passwd is None):
        return Response.error_response(message='Nie pełny formularz').to_dict()
    return uc.signup_user(nick, email, passwd, rep_passwd).to_dict()


@user_bp.route('/approve/<email>/<code>', methods=['GET', 'POST'])
def approve(email: str, code: str):
    ret=uc.approve(email, code)
    if ret.success:
        return redirect('/')
    # return render_base_template('error.html', err=ret.to_dict())
    return ret.to_dict()

@user_bp.route('/ch_pass', methods=['POST'])
@login_required
def ch_pass():
    passwd = request.form.get('passwd')
    new_passwd = request.form.get('new_passwd')
    rep_passwd = request.form.get('rep_passwd')
    if (passwd is None) or (new_passwd is None) or (rep_passwd is None):
        return Response.error_response(message='Nie pełny formularz').to_dict()
    return uc.change_password(passwd, new_passwd, rep_passwd).to_dict()

@user_bp.route('/pass_reset', methods=['POST'])
def pass_reset_request():
    email=request.form.get('email')
    code=request.form.get('code')
    if email is None:
        return Response.error_response(message='Nie pełny formularz').to_dict()
    if code is None:
        return uc.request_pass_reset(email).to_dict()
    passwd = request.form.get('passwd')
    rep_passwd = request.form.get('rep_passwd')
    if (passwd is None) or (rep_passwd is None):
        return Response.error_response(message='Nie pełny formularz').to_dict()
    return uc.pass_reset_new_pass(email, code, passwd, rep_passwd).to_dict()

@user_bp.route('/pass_reset/<email>/<code>', methods=['GET', 'POST'])
def pass_reset(email: str, code: str):
    ret=uc.pass_reset(email, code)
    if ret.success:
        return render_base_template('pass_reset.html', email=email, code=ret.data)
    # return render_base_template('error.html', err=ret.to_dict())
    return ret.to_dict()

@user_bp.route('/pass_reset_form')
def pass_reset_form():
    return render_base_template('request_pass_change.html')
