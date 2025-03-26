import requests
# from src.routes import users as ru
from test_utils import TestingUnit as tu

@tu.test_resp
def add_user_ShouldNotAddIncorrectUser1():
    req=requests.request('GET', 'http://localhost:5000/user/logout')
    assert req.status_code==200
    req=req.json()
    assert req=={'data':None,'message':'OK','success':True}
