from enum import member
from .LangBase import LangBase

class EngLang(LangBase):
    UserNotFoundErr=member(lambda e: f'User not found: {e}')
    UserNotLogged='No user logged'
    UserNotAdded='User is not added'
    UserNotApproved='User is not approved'
    UserNotDeleted='User is not deleted'
    PasswordNotChanged='Password is not changed'
    FuncNotExecuted='Function has not been executed'
    AccountNotCreated='Account has not been created'
