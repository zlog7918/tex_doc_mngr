import time
from db.db_base import db
from typing import Awaitable
from db.seed_db import seed_data
from models.lang import LangEnum
from models.usr.User import User
from flask_login import LoginManager
from flask.typing import RouteCallable
from routes.users.users import user_bp
from models.utils import utils as util
from services import user_service as su
from werkzeug.exceptions import NotFound
from routes.reviewer.reviews import review_bp
from routes.author.articles import articles_bp
from routes.editor.questions import questions_bp
from models.utils.EnvConsts import envConsts as ec
from routes.editor.articles import editor_articles_bp
from flask import abort, Flask, Request as flRequest, request, current_app
from werkzeug.routing import RequestRedirect, MapAdapter, BaseConverter, ValidationError

class LangEnumConverter(BaseConverter):

    def to_python(self, value: str) -> LangEnum:
        _map: dict[str, LangEnum]=LangEnum._member_map_ # type: ignore
        if value not in _map:
            raise ValidationError()
        lang_enum=_map[value]
        return lang_enum

    def to_url(self, value: LangEnum) -> str:
        try:
            return value.name
        except ValueError as err:
            raise ValidationError()

app = Flask(__name__)
app.url_map.converters.update({'lang_enum': LangEnumConverter})

app.config['SQLALCHEMY_DATABASE_URI'] = ec.getDBString()
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

app.secret_key=ec.getFlaskKey()

app.register_blueprint(editor_articles_bp, url_prefix="/editor/articles")
app.register_blueprint(questions_bp, url_prefix="/questions")
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

# async def choose_lang(path: str):
@app.route('/<lang_enum:lang>', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<lang_enum:lang>/<path:path>', methods=['GET', 'POST'])
def choose_lang(lang: LangEnum, path: str):
    util.set_lang_pkg(lang)

    def get_path_from_url(url: str) -> str:
        _url=url.split('/', maxsplit=3)
        return f'/{_url[3]}' if len(_url)==4 else '/'
    def get_func(map: MapAdapter, list: dict[str, RouteCallable], url: str, i: int=0) -> tuple[RouteCallable, dict[str, object]]:
        if i>=5:
            raise NotFound()
        try:
            func_name, mapping=map.match(url)
            func=list[func_name]
            return func, dict(mapping)
        except RequestRedirect as e:
            url=get_path_from_url(e.new_url)
        return get_func(map, list, url, i+1)
    func, kwargs=get_func(current_app.url_map.bind_to_environ(request), current_app.view_functions, path)
    if func==choose_lang:
        abort(404)
    ret=func(**kwargs)
    if isinstance(ret, Awaitable):
        # return await ret
        # TODO: perhaps to change with above, but we don't have any Awaitable values for now
        print(f'\n\nFOUND Awaitable: on path: {path}, with arguments: {request.form.to_dict()}\n\n')
        raise NotFound()
    return ret

@app.route('/')
def index():
    user=su.get_curr_user()
    return util.render_base_template('login_form.html' if user is None else ('logged.html' if user.approved else 'check_approval.html'))

if __name__=='__main__':
    app.run(debug=True)
