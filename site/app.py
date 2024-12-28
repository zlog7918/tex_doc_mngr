import os
# from collections import deque
from classes.usr.User import User
from classes.db.DB_Queries import DB_Queries
from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from flask import Flask, render_template, request, redirect, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app=Flask(__name__)

login_manager=LoginManager()
login_manager.init_app(app)

app.secret_key=os.environ.get('FLASK_KEY', 'FLASK_KEY')
    
# recent_users=deque(maxlen=3)

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
    user: User=current_user
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
    return render_template('logged.html' if current_user.is_authenticated else 'login_form.html')

if __name__=='__main__':
    app.run(debug=True)



# from flask import Flask, render_template, request, make_response, redirect
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# import markdown
# from collections import deque
# from passlib.hash import sha256_crypt
# import sqlite3

# @app.route('/hello', methods=['GET'])
# @login_required
# def hello():
#     if request.method=='GET':
#         print(current_user.id)
#         nick=current_user.id

#         db=sqlite3.connect(DATABASE)
#         sql=db.cursor()
#         sql.execute(f'SELECT id FROM notes WHERE nick==?', (nick, ))
#         notes=sql.fetchall()

#         return render_template('hello.html', nick=nick, notes=notes)

# @app.route('/render', methods=['POST'])
# @login_required
# def render():
#     md=request.form.get('markdown','')
#     rendered=markdown.markdown(md)
#     nick=current_user.id
#     db=sqlite3.connect(DATABASE)
#     sql=db.cursor()
#     sql.execute(f'INSERT INTO notes (nick, note) VALUES (?, ?)', (nick, rendered))
#     db.commit()
#     return render_template('markdown.html', rendered=rendered)

# # @app.route('/render/<rendered_id>')
# # @login_required
# # def render_old(rendered_id):
# #     db=sqlite3.connect(DATABASE)
# #     sql=db.cursor()
# #     sql.execute(f'SELECT nick, note FROM notes WHERE id==?', (rendered_id, ))

# #     try:
# #         nick, rendered=sql.fetchone()
# #         if nick != current_user.id:
# #             return 'Access to note forbidden', 403
# #         return render_template('markdown.html', rendered=rendered)
# #     except:
# #         return 'Note not found', 404
