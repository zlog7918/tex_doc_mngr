from flask import Blueprint
from db.db_base import db
from flask import Blueprint, request, jsonify
from models.usr.User import User
from flask_login import login_required, current_user
import controllers.user_controller as uc

user_bp = Blueprint('user', __name__)


@user_bp.route('/login', methods=['POST'])
def login():
    nick = request.form.get('nick')
    passwd = request.form.get('passwd')
    return uc.login(nick, passwd)


@user_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    return uc.logout()


@user_bp.route('/signup', methods=['POST'])
def signup():
    nick = request.form.get('nick')
    email = request.form.get('email')
    passwd = request.form.get('passwd')
    rep_passwd = request.form.get('rep_passwd')

    return uc.signup_user(nick, email, passwd, rep_passwd)

@user_bp.route('/approve', methods=['POST'])
@login_required
def approve():
    code=request.form.get('code')
    uc.approve(code)


@user_bp.route('/ch_pass', methods=['POST'])
@login_required
def ch_pass():
    passwd = request.form.get('passwd')
    new_passwd = request.form.get('new_passwd')
    rep_passwd = request.form.get('rep_passwd')
    if new_passwd != rep_passwd:
        return jsonify({'error': True, 'message': 'Podane nowe hasła nie pasują do siebie'})
    user: User=current_user
    if not user.verify_pass(passwd):
        return jsonify({'error': True, 'message': 'Nieprawidłowe stare hasło'})
    passwd=user.ch_pass(new_passwd)
    del new_passwd, rep_passwd
    if passwd is False:
        return jsonify({'error': True, 'message': 'Hasło nie zostało zmienione'})
    db.session.commit()
    return jsonify({'error': False, 'data': True})
