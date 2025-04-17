from enum import Enum, member

class LangBaseEx(Enum):
    UserNotFoundErr=\
        member(lambda e:f'')
    UserNotLogged=\
    UserNotAdded=\
    UserNotApproved=\
    UserNotDeleted=\
    PasswordNotChanged=\
    FuncNotExecuted=\
    AccountNotCreated=\
        member('')