from flask import Blueprint
from classes.db.DBQ_Users import DBQ_Users
from classes.mail.SendMail import SendMail
from flask import Blueprint, request, jsonify
from classes.usr.User import User, user_loader
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from flask_login import login_user, logout_user, login_required, current_user

user_bp=Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    nick=request.form.get('nick')
    passwd=request.form.get('passwd')
    user=user_loader(nick)
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
    nick=request.form.get('nick')
    email=request.form.get('email')
    passwd=request.form.get('passwd')
    rep_passwd=request.form.get('rep_passwd')
    if passwd!=rep_passwd:
        return jsonify({'error': True, 'message': 'Podane nowe hasła nie pasują do siebie'})
    user=User(nick, email)
    passwd=user.ch_pass(passwd)
    ret={'error': True, 'message': 'Konto nie zostało utworzone'}
    if passwd is False:
        return jsonify(ret)
    db: DBQ_Users=DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Users)
    try:
        code, code_exp=db.add_user(nick, email, passwd)
    except Exception as e:
        return jsonify(ret)
    
    try:
        flag=False
        s=SendMail()
        if not s.sendCode([email], code):
            flag=True
    except Exception as e:
        flag=True
    finally:
        if flag:
            db.del_user(nick)
            return jsonify(ret)
    
    login_user(user)
    return jsonify({'error': False, 'data': {'message':f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code_exp/60}min'}})

@user_bp.route('/approve', methods=['POST'])
@login_required
def approve():
    user: User=current_user
    if user.is_approved():
        # return jsonify({'error': False, 'data': True})
        return jsonify({'error': True, 'message': 'Konto nie wymaga potwierdzenia'})
    code=request.form.get('code')
    db: DBQ_Users=DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Users)
    try:
        flag=db.approve_user(user.get_nick(), code)
    except:
        return jsonify({'error': True, 'message': 'Konto nie zostało potwierdzone'})
    if flag:
        user=user_loader(user.get_nick())
        login_user(user)
        return jsonify({'error': False, 'data': True})
    return jsonify({'error': True, 'message': 'Konto nie zostało potwierdzone'})

@user_bp.route('/ch_pass', methods=['POST'])
@login_required
def ch_pass():
    passwd=request.form.get('passwd')
    new_passwd=request.form.get('new_passwd')
    rep_passwd=request.form.get('rep_passwd')
    if new_passwd!=rep_passwd:
        return jsonify({'error': True, 'message': 'Podane nowe hasła nie pasują do siebie'})
    user: User=current_user._get_current_object()
    if user.verify_pass(passwd):
        passwd=user.ch_pass(new_passwd)
        del new_passwd, rep_passwd
        ret={'error': True, 'message': 'Hasło nie zostało zmienione'}
        if passwd is False:
            return jsonify(ret)
        db: DBQ_Users=DB_Factory.get_db(DB_QueriesOpt.DB_Queries, DBQ_Users)
        try:
            flag=db.change_user_passwd(user.get_nick(), passwd)
        except:
            return jsonify(ret)
        return jsonify({'error': False, 'data': True} if flag else ret)
    else:
        return jsonify({'error': True, 'message': 'Nieprawidłowe stare hasło'})