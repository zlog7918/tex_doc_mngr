from classes.db.DB_Factory import DB_Factory, DB_QueriesOpt
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    db=DB_Factory.get_db(DB_QueriesOpt.DB_Queries)

    return f'Returned: {db.get_test()}, {request.environ['REMOTE_ADDR']}\n'

if __name__ == "__main__":
    app.run(debug=True)
