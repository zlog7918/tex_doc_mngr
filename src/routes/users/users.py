import datetime
from sqlalchemy import or_
from flask import Blueprint
from db.db_base import db
from models.mail.SendMail import SendMail
from models.utils.utils import generate_code
from flask import Blueprint, request, jsonify
from models.usr.User import User, user_loader
from flask_login import login_user, logout_user, login_required, current_user

user_bp = Blueprint('user', __name__)


@user_bp.route('/login', methods=['POST'])
def login():
    nick = request.form.get('nick')
    passwd = request.form.get('passwd')
    user = user_loader(nick)
    if user is None:
        return jsonify({'error': True, 'message': 'Nieprawidłowy login lub hasło'})
    if user.verify_pass(passwd):
        login_user(user)
        return jsonify({'error': False, 'data': True})
    else:
        return jsonify({'error': True, 'message': 'Nieprawidłowy login lub hasło'})


@user_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return jsonify({'error': False, 'data': True})


@user_bp.route('/signup', methods=['POST'])
def signup():
    nick = request.form.get('nick')
    email = request.form.get('email')
    passwd = request.form.get('passwd')
    rep_passwd = request.form.get('rep_passwd')
    if passwd != rep_passwd:
        return jsonify({'error': True, 'message': 'Podane nowe hasła nie pasują do siebie'})
    user=User()
    passwd=user.ch_pass(passwd)
    ret={'error': True, 'message': 'Konto nie zostało utworzone'}
    if passwd is False:
        return jsonify(ret)
    q=User.query.where(or_(User.nick==nick, User.email==email))
    ret=db.session.execute(q).first()
    if ret is not None:
        return jsonify(ret)
    
    code, code_exp=generate_code()
    try:
        flag=False
        s=SendMail()
        if not s.sendCode([email], code):
            flag=True
    except Exception as e:
        flag=True
    finally:
        if flag:
            return jsonify(ret)
    
    db.session.add(User(nick=nick, email=email, passwd=passwd, approved=False, code=code, code_exp=datetime.datetime.now()+datetime.timedelta(seconds=code_exp)))
    db.session.commit()
    user=user_loader(nick)
    login_user(user)
    return jsonify({'error': False,
                    'data': {'message': f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code_exp/60}min'}})


@user_bp.route('/approve', methods=['POST'])
@login_required
def approve():
    user: User=current_user
    if user.is_approved():
        # return jsonify({'error': False, 'data': True})
        return jsonify({'error': True, 'message': 'Konto nie wymaga potwierdzenia'})
    code=request.form.get('code')
    flag=user.approve(code)
    db.session.commit()
    if flag:
        db.session.commit()
        return jsonify({'error': False, 'data': True})
    return jsonify({'error': True, 'message': 'Konto nie zostało potwierdzone'})


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
