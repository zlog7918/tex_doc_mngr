import os
from src.services import user as su
from src.models.usr.User import User
from test_utils import TestingUnit as tu

@tu.test_resp_with_context
def add_user_ShouldNotAddIncorrectUser1():
    u=User()
    try:
        su.add_user(u)
        assert False
    except Exception: pass

@tu.test_resp_with_context
def add_user_ShouldNotAddIncorrectUser2():
    nick='adsadsad'
    u=User(**{'nick':nick})
    try:
        su.add_user(u)
        assert False
    except Exception: pass

@tu.test_resp_with_context
def add_user_ShouldNotAddIncorrectUser3():
    u=User()
    passwd=u.ch_pass('A@s#d4feffeq')
    u=User(**{'passwd':passwd})
    try:
        su.add_user(u)
        assert False
    except Exception: pass

@tu.test_resp_with_context
def add_user_ShouldNotAddIncorrectUser4():
    email='w@wp.pl'
    u=User(**{'email':email})
    try:
        su.add_user(u)
        assert False
    except Exception: pass

@tu.test_resp_with_context
def add_user_ShouldAddCorrectUser():
    u=User()
    u.ch_pass('A@s#d4feffeq')
    passwd=u.get_passwd()
    u=User(**{'nick':'adsadsad', 'passwd':passwd, 'email':'w@wp.pl'})
    try:
        su.add_user(u)
    except Exception as e:
        assert False
    # u=User(**{'nick':None, 'passwd':passwd, 'email':'a@wp.pl'})
    # try:
    #     su.add_user(u)
    # except Exception as e:
    #     assert False

@tu.test_resp_with_context
def get_user_by_nick_ShouldGetCorrectUser():
    nick='adsadsad'
    email='w@wp.pl'
    u=User()
    u.ch_pass('A@s#d4feffeq')
    passwd=u.get_passwd()
    u=User(**{'nick':nick, 'passwd':passwd, 'email':email})
    try:
        su.add_user(u)
    except Exception as e:
        assert False
    usr=su.get_user_by_nick(nick)
    assert usr is not None
    assert usr.get_nick()==nick
    assert usr.get_passwd()==passwd
    assert usr.get_email()==email

@tu.test_resp_with_context
def get_user_by_email_ShouldGetCorrectUser():
    nick='adsadsad'
    email='w@wp.pl'
    u=User()
    u.ch_pass('A@s#d4feffeq')
    passwd=u.get_passwd()
    u=User(**{'nick':nick, 'passwd':passwd, 'email':email})
    try:
        su.add_user(u)
    except Exception as e:
        assert False
    usr=su.get_user_by_email(email)
    assert usr is not None
    assert usr.get_nick()==nick
    assert usr.get_passwd()==passwd
    assert usr.get_email()==email
    # email='a@wp.pl'
    # u=User(**{'nick':None, 'passwd':passwd, 'email':email})
    # assert su.add_user(u)==True
    # usr=su.get_user_by_email(email)
    # assert usr is not None
    # print(usr.get_nick())
    # assert usr.get_nick()==nick
    # assert usr.get_passwd()==passwd
    # assert usr.get_email()==email

@tu.test_resp_with_context
def get_user_id_ShouldGetCorrectUserId():
    nick='adsadsad'
    email='w@wp.pl'
    u=User()
    u.ch_pass('A@s#d4feffeq')
    passwd=u.get_passwd()
    u=User(**{'nick':nick, 'passwd':passwd, 'email':email})
    try:
        su.add_user(u)
    except Exception as e:
        assert False
    usr=su.get_user_by_nick(nick)
    assert usr is not None
    assert usr.get_nick()==nick
    assert usr.get_passwd()==passwd
    assert usr.get_email()==email
    usr_id=su.get_user_id(nick)
    assert f'{usr_id}'==usr.get_id()

@tu.test_resp_with_context
def get_user_ShouldGetCorrectUser():
    nick='adsadsad'
    email='w@wp.pl'
    u=User()
    u.ch_pass('A@s#d4feffeq')
    passwd=u.get_passwd()
    u=User(**{'nick':nick, 'passwd':passwd, 'email':email})
    try:
        su.add_user(u)
    except Exception as e:
        assert False
    usr=su.get_user_by_email(email)
    assert usr is not None
    usr=su.get_user(int(usr.get_id()))
    assert usr is not None
    assert usr.get_nick()==nick
    assert usr.get_passwd()==passwd
    assert usr.get_email()==email
