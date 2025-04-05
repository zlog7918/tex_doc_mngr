import requests
# from src.routes.users import users as ru
from test_utils import TestingUnitBlueprint

route_user_bluebrint=TestingUnitBlueprint()

@route_user_bluebrint.test_resp
def logout_ShouldReturnCorrectly():
    req=requests.request('GET', 'http://localhost:5000/user/logout')
    assert req.status_code==200
    req=req.json()
    assert req=={'data':None,'message':'OK','success':True}

@route_user_bluebrint.test_resp
def login_ShouldCorrectlyLogIn():
    req=lambda passwd: requests.request('POST', 'http://localhost:5000/user/login', data={
        'nick': 'aaaa',
        'passwd': passwd
    })
    req=req('aaaa')
    assert req.status_code==200
    req=req.json()
    assert req=={'data':None,'message':'OK','success':True}
