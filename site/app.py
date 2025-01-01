import os
# from collections import deque
from classes.usr.User import User
from classes.utils.utils import url_last_edit
from classes.db.DB_Queries import DB_Queries
from flask import Flask, render_template, request, jsonify
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app=Flask(__name__)

login_manager=LoginManager()
login_manager.init_app(app)

app.secret_key=os.environ.get('FLASK_KEY', 'FLASK_KEY')

@login_manager.user_loader
def user_loader(nick: str|None) -> User|None:
    if nick is None:
        return None

    db: DB_Queries=DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
    try:
        nick, passwd=db.get_user(nick)
    except:
        return None
    user=User(nick, passwd)
    return user

@login_manager.request_loader
def request_loader(request):
    nick=request.form.get('nick')
    user=user_loader(nick)
    return user

@app.route('/do/login', methods=['POST'])
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

@app.route('/do/logout')
def logout():
    logout_user()
    return jsonify({'error': False, 'data': True})

@app.route('/do/ch_pass', methods=['POST'])
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
        db: DB_Queries=DB_Factory.get_db(DB_QueriesOpt.DB_Queries)
        try:
            flag=db.change_user_passwd(user.get_nick(), passwd)
        except:
            return jsonify(ret)
        return jsonify({'error': False, 'data': True} if flag else ret)
    else:
        return jsonify({'error': True, 'message': 'Nieprawidłowe stare hasło'})

@app.route('/')
def index():
    return render_template('logged.html' if current_user.is_authenticated else 'login_form.html', url_last_edit=url_last_edit)

if __name__=='__main__':
    app.run(debug=True)
