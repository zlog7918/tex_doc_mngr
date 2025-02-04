from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from flask import Flask, request
from routes.articles import articles_bp
from routes.reviews import review_bp

app = Flask(__name__)

app.register_blueprint(articles_bp, url_prefix="/articles")
app.register_blueprint(review_bp, url_prefix="/reviews")

@app.route('/')
def index():
    db=DB_Factory.get_db(DB_QueriesOpt.DB_Queries)

    return f'Returned: {db.get_test()}, {request.environ['REMOTE_ADDR']}\n'

if __name__ == "__main__":
    app.run(debug=True)
