from enum import Enum, member

class LangBaseEx(Enum):
    UserNotFoundErr=\
    ConfirmAccountThroughCode=\
        member(lambda e:f'')
    UserNotLogged=\
    UserNotAdded=\
    UserNotApproved=\
    UserNotDeleted=\
    PasswordNotChanged=\
    FuncNotExecuted=\
    AccountNotCreated=\
    CodeNotGenerated=\
    CodeNotDeactivated=\
    CodeNotApproved=\
    NickDoesNotMeetCriteria=\
    IncorrectNickOrPassword=\
    PasswordsDoNotMatch=\
    UnsuccessfulMailSending=\
    EmailDoesNotMeetCriteria=\
    UserCanAcceptInviteThroughMail=\
    UserNotInvited=\
    NickExistsOrInvalidPassword=\
    IncorrectCode=\
    EmailOrNickExists=\
    UserAlreadyApproved=\
    IncorrectOldPassword=\
    PasswordDoesNotMeetCriteria=\
    UnknownErr=\
    UnknownDBErr=\
    CodeSent=\
        member('')