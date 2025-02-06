import os
from paths.users.users import user_bp
from flask import Flask, render_template
from paths.routes.reviews import review_bp
from classes.utils.utils import url_last_edit, render_base_template
from paths.routes.articles import articles_bp
from classes.usr.User import User, user_loader
from flask_login import LoginManager, current_user

app=Flask(__name__)

login_manager=LoginManager()
login_manager.init_app(app)

app.secret_key=os.environ.get('FLASK_KEY', 'FLASK_KEY')

app.config['UPLOAD_FOLDER'] = os.getenv('DOC_FILES_DIR', '/var/www/uploads')
app.config['TEMP_FOLDER'] = os.getenv('TEMP_FOLDER', '/var/www/uploads/tmp')
app.register_blueprint(articles_bp, url_prefix="/articles")
app.register_blueprint(review_bp, url_prefix="/reviews")
app.register_blueprint(user_bp, url_prefix="/user")

@login_manager.user_loader
def ul(nick: str|None) -> User|None:
    return user_loader(nick)

@login_manager.request_loader
def request_loader(request):
    nick=request.form.get('nick')
    user=user_loader(nick)
    return user

@app.route('/')
def index():
    user: User=current_user
    return render_base_template(('logged.html' if user.is_approved() else 'check_approval.html') if current_user.is_authenticated else 'login_form.html')

if __name__=='__main__':
    app.run(debug=True)
