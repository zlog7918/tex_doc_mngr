from src.models.usr.User import User
from test_utils import TestingUnit as tu

@tu.test_resp
def user_shouldCheckPassword():
    u=User()
    assert u.ch_pass('A@s#d4feffq')==False
    assert u.ch_pass('asddhcalslaa')==False
    assert u.ch_pass('464645434354')==False
    assert u.ch_pass('cs6d45354aa5')==False
    assert u.ch_pass('!#@$#@#@@!@#')==False
    assert u.ch_pass('ADSAFGRGRWGR')==False
    assert u.ch_pass('DADSA654fFAD')==False
    assert u.ch_pass('FDADA5343das')==False
    assert u.ch_pass('FDADA#Q$#das')==False
    assert u.ch_pass('43353#$#dfas')==False
    assert u.ch_pass('43353#$#DADF')==False
    assert u.ch_pass('A@s#d4feffeq')==True

@tu.test_resp
def user_created_with_nick():
    nick='adsadsad'
    u=User(**{'nick':nick})
    assert u.get_nick()==nick

@tu.test_resp
def user_created_with_password():
    u=User()
    passwd=u.ch_pass('A@s#d4feffeq')
    u=User(**{'passwd':passwd})
    assert u.get_passwd()==passwd

@tu.test_resp_with_context
def user_created_with_email():
    email='w@wp.pl'
    u=User(**{'email':email})
    assert u.get_email()==email

@tu.test_resp_with_context
def user_created_with_all():
    nick='adsadsad'
    email='w@wp.pl'
    u=User()
    passwd=u.ch_pass('A@s#d4feffeq')
    u=User(**{'nick':nick, 'passwd':passwd, 'email':email})
    assert u.get_nick()==nick
    assert u.get_passwd()==passwd
    assert u.get_email()==email
