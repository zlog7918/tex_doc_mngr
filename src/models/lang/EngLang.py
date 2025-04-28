from enum import member
from .LangBase import LangBase

class EngLang(LangBase):
    UserNotFoundErr=member(lambda e:f'User not found: {e}')
    UserNotLogged='No user logged'
    UserNotAdded='User is not added'
