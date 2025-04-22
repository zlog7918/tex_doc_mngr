from enum import member
from .LangBase import LangBase

class EngLang(LangBase):
    UserNotFoundErr=member(lambda e: f'User not found: {e}')
    ConfirmAccountThroughCode=member(lambda time: f'Confirm account through code from email in: {time}min')
    UserNotLogged='No user logged'
    UserNotAdded='User is not added'
    UserNotApproved='User is not approved'
    UserNotDeleted='User is not deleted'
    PasswordNotChanged='Password is not changed'
    FuncNotExecuted='Function has not been executed'
    AccountNotCreated='Account has not been created'
    CodeNotGenerated='Code has not been generated'
    CodeNotDeactivated='Code is not deactivated'
    CodeNotApproved='Code is not approved'
    NickDoesNotMeetCriteria='Nick does not meet criteria'
    IncorrectNickOrPassword='Incorrect nick or password'
    PasswordsDoNotMatch='Given passwords do not match'
    UnsuccessfulMailSending='Unsuccessful email sending'
    EmailDoesNotMeetCriteria='Email does not meet criteria'
    UserCanAcceptInviteThroughMail='User can accept invite through email'
    UserNotInvited='User not invited'
    NickExistsOrInvalidPassword='Password does not meet criteria or user with this nick already exists'
    IncorrectCode='Code is incorrect'
    EmailOrNickExists='User with given nick or email already exists'
    UserAlreadyApproved='Account does not need approval'
    IncorrectOldPassword='Incorrect old password'
    PasswordDoesNotMeetCriteria='Password does not meet criteria'
    UnknownErr='Occured unpredicted error, sorry for the difficulties'
    UnknownDBErr='Occured serious unpredicted error, sorry for the difficulties'
    CodeSent='Message successfuly sent'
