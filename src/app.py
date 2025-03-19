import os
import time
from db.db_base import db
from services import user as su
from db.seed_db import seed_data
from models.usr.User import User
from flask_login import LoginManager
from routes.users.users import user_bp
from flask import Flask, Request as flRequest
from routes.reviewer.reviews import review_bp
from routes.author.articles import articles_bp
from models.utils.utils import render_base_template
from routes.editor.articles import editor_articles_bp

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@psql/{os.getenv('POSTGRES_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    for _ in range(10):
        try:
            db.engine.connect()
            break
        except Exception:
            time.sleep(0.2)
    db.create_all()
    seed_data(db)

login_manager=LoginManager()
login_manager.init_app(app)

app.secret_key=os.environ.get('FLASK_KEY', 'FLASK_KEY')

app.register_blueprint(editor_articles_bp, url_prefix="/editor/articles")
app.register_blueprint(articles_bp, url_prefix="/articles")
app.register_blueprint(review_bp, url_prefix="/reviews")
app.register_blueprint(user_bp, url_prefix="/user")

@login_manager.user_loader
def ul(id: str|None) -> User|None:
    if id is None:
        return None
    return su.get_user(int(id))

@login_manager.request_loader
def request_loader(request: flRequest):
    nick=request.form.get('nick')
    if nick is None:
        return None
    user=su.get_user_by_nick(nick)
    return user

@app.route('/')
def index():
    user=su.get_curr_user()
    return render_base_template('login_form.html' if user is None else ('logged.html' if user.is_approved() else 'check_approval.html'))

if __name__=='__main__':
    app.run(debug=True)
