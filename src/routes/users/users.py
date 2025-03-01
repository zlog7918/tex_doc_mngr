from flask import Blueprint, request
from flask_login import login_required
import controllers.user_controller as uc

user_bp = Blueprint('user', __name__)


@user_bp.route('/login', methods=['POST'])
def login():
    nick = request.form.get('nick')
    passwd = request.form.get('passwd')
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
    return uc.signup_user(nick, email, passwd, rep_passwd).to_dict()


@user_bp.route('/approve', methods=['POST'])
@login_required
def approve():
    code=request.form.get('code')
    return uc.approve(code).to_dict()


@user_bp.route('/ch_pass', methods=['POST'])
@login_required
def ch_pass():
    passwd = request.form.get('passwd')
    new_passwd = request.form.get('new_passwd')
    rep_passwd = request.form.get('rep_passwd')
    return uc.change_password(passwd, new_passwd, rep_passwd).to_dict()
