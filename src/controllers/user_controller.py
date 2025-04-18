import re
import time
import random
import pickle as pkl
import email_validator as emailV
from models.usr.User import User
from db.db_base import log_activity
from models.utils import utils as util
from models.mail.SendMail import SendMail
from models.utils.Response import Response
from models.usr.Code import CodePurposeEnum
from services import user as su, code as sc
from models.utils.decors import log_if_error
from flask_login import login_user, logout_user
from models.utils.MessageException import MessageException
from typing import Callable, ParamSpec, Concatenate, TypeVar, TypeVarTuple

P=ParamSpec('P')

def validate_nick(nick: str) -> None:
  lang_pkg=util.get_lang_pkg()
  ret_mess=lang_pkg.NickDoesNotMeetCriteria.value
  try:
    nick.index('\n')
    raise MessageException(ret_mess)
  except ValueError:
    pass
  if re.match(r'^[a-zA-z][a-zA-Z0-9_-]{1,78}[a-zA-Z0-9]$', nick) is None:
    raise MessageException(ret_mess)


@log_if_error
def login(nick: str, passwd: str) -> Response:
  message=util.get_lang_pkg().IncorrectNickOrPassword.value
  validate_nick(nick)
  user=su.get_user_by_nick(nick)
  if user is None:
    raise MessageException(
      message,
      Exception('Incorrect login')
    )
  if not user.verify_pass(passwd):
    raise MessageException(
      message,
      Exception(f'Incorrect password for {nick}')
    )

  login_user(user)
  log_activity(True, {'details': f'Logged account: {user.get_nick()}'})
  return Response.success_response()

@log_if_error
def logout() -> Response:
  logout_user()
  return Response.success_response()

def validate_passwords(passwd: str, rep_passwd: str) -> None:
  if passwd != rep_passwd:
    raise MessageException(util.get_lang_pkg().NickDoesNotMeetCriteria.value)

def check_password(passwd: str) -> str:
  user=User()
  flag=user.ch_pass(passwd)
  if flag is False:
    raise MessageException(util.get_lang_pkg().AccountNotCreated.value)
  return user.get_passwd()

def send_code_by_email(send_func: Callable[Concatenate[SendMail, str, P], None], email, *args: P.args, **kwargs: P.kwargs) -> None:
  try:
    s=SendMail()
    send_func(s, email, *args, **kwargs)
  except MessageException as e:
    raise e from None
  except Exception as e:
    raise MessageException.from_exception(e, util.get_lang_pkg().UnsuccessfulMailSending.value)
      

def create_user(nick: str|None, email: str, passwd: str, do_after_create: bytes|None=None) -> None:
  if nick is not None:
    do_after_create=None
  user = User(**util.get_kwargs_for(User, {
    User.nick: nick,
    User.email: email,
    User.passwd: passwd,
    User.do_after_cr: do_after_create,
  }))
  su.add_user(user)

def validate_email(email: str) -> str:
  try:
    v=emailV.validate_email(email)
    return v.email
  except emailV.EmailNotValidError as e:
    raise MessageException.from_exception(e, util.get_lang_pkg().EmailDoesNotMeetCriteria.value)

T_ret=TypeVar('T_ret')
TVT=TypeVarTuple('TVT')
@log_if_error
def invite_user(email: str, message: str|None=None, do_after_create: list[tuple[Callable[P, T_ret], tuple[*TVT]]]=[]) -> Response:
  lang_pkg=util.get_lang_pkg()
  message=lang_pkg.UserCanAcceptInviteThroughMail.value
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is not None:
    if sc.active_codes(user, CodePurposeEnum.InviteUserMail) is not None:
      return Response.success_response(message=message)
    su.delete_user(user)

  do=pkl.dumps(do_after_create)
  create_user(None, email, '', do)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(lang_pkg.UserNotInvited.value)
  
  code, code_exp=sc.gen_code(user, CodePurposeEnum.InviteUserMail)
  send_code_by_email(SendMail.sendInvite, email, code, message)
  
  log_activity(True, {'details': f'Account created successfully: [{email}]'})
  return Response.success_response(message=message)

@log_if_error
def accept_invite(email: str, code: str) -> Response:
  lang_pkg=util.get_lang_pkg()
  message=lang_pkg.IncorrectCode.value
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(message)
  if user.get_nick()!='':
    raise MessageException(message)
  
  if sc.check_code(user, code, CodePurposeEnum.InviteUserMail, False) is None:
    raise MessageException(message)
  _code, _=sc.gen_code(user, CodePurposeEnum.InviteUser)
  return Response.success_response(_code.code)

@log_if_error
def accept_invite_cr_user(email: str, code: str, nick: str, passwd: str, rep_passwd: str) -> Response:
  lang_pkg=util.get_lang_pkg()
  message=lang_pkg.IncorrectCode.value
  validate_nick(nick)
  validate_passwords(passwd, rep_passwd)
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(message)
  if user.get_nick()!='':
    raise MessageException(message)
  if sc.check_code(user, code, CodePurposeEnum.InviteUser) is None:
    raise MessageException(message)
  _codes=sc.active_codes(user, CodePurposeEnum.InviteUserMail)

  su.set_user_nick(user, nick)
  if not su.change_user_pass(user, passwd):
    _code, _=sc.gen_code(user, CodePurposeEnum.InviteUser)
    return Response.error_response(message=lang_pkg.NickExistsOrInvalidPassword.value, data=_code.code)

  if _codes is not None:
    for _code in _codes:
      sc.deactivate_code(_code)
  _code, code_exp=sc.gen_code(user, CodePurposeEnum.ApproveUser)
  log_activity(True, {'details': f'Code successfuly generated for {user.get_nick()}'})
  send_code_by_email(SendMail.sendCode, email, _code)

  login_user(user)
  log_activity(True, {'details': f'Account succesfully created from invite: {user.get_nick()}'})
  return Response.success_response(
    message=lang_pkg.ConfirmAccountThroughCode.value(code_exp/60)
  )

@log_if_error
def signup_user(nick: str, email: str, passwd: str, rep_passwd: str) -> Response:
  lang_pkg=util.get_lang_pkg()
  message=lang_pkg.EmailOrNickExists.value
  validate_nick(nick)
  validate_passwords(passwd, rep_passwd)
  email=validate_email(email)
  _passwd=check_password(passwd)
  
  if su.get_user_by_nick(nick) is not None:
    raise MessageException(message)
  user=su.get_user_by_email(email)
  if user is None:
    create_user(nick, email, _passwd)
    user=su.get_user_by_nick(nick)
  elif user.get_nick()!='':
    raise MessageException(message)
  else:
    su.set_user_nick(user, nick)
    if not su.change_user_pass(user, passwd):
      raise MessageException(lang_pkg.AccountNotCreated.value)
  
  if user is None:
    raise MessageException(lang_pkg.AccountNotCreated.value)

  code, code_exp=sc.gen_code(user, CodePurposeEnum.ApproveUser)
  log_activity(True, {'details': f'Code successfuly generated for {user.get_nick()}'})
  send_code_by_email(SendMail.sendCode, email, code)
  
  login_user(user)
  log_activity(True, {'details': f'Account succesfully created: {nick}[{email}]'})
  return Response.success_response(
    message=lang_pkg.ConfirmAccountThroughCode.value(code_exp/60)
  )

@log_if_error
def approve(email: str, code: str) -> Response:
  lang_pkg=util.get_lang_pkg()
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(lang_pkg.UserAlreadyApproved.value)
  if user.is_approved():
    raise MessageException(lang_pkg.UserAlreadyApproved.value)
  if sc.check_code(user, code, CodePurposeEnum.ApproveUser) is None:
    raise MessageException(
      lang_pkg.UserNotApproved.value,
      Exception(f'Incorrect code given for: {user.get_nick()}')
    )
  su.approve_user(user)
  log_activity(True, {'details': f'Account succesfully approved: {user.get_nick()}'})
  return Response.success_response()

@log_if_error
def change_password(passwd: str, new_passwd: str, rep_passwd: str) -> Response:
  lang_pkg=util.get_lang_pkg()
  validate_passwords(new_passwd, rep_passwd)
  user=su.get_curr_user_or_err()
  if not user.verify_pass(passwd):
    raise MessageException(
      lang_pkg.IncorrectOldPassword.value,
      Exception(f'Incorrect old password for: {user.get_nick()}')
    )
  if su.change_user_pass(user, new_passwd):
    log_activity(True, {'details': f'Successful password change for: {user.get_nick()}'})
    return Response.success_response()
  raise MessageException(lang_pkg.PasswordDoesNotMeetCriteria.value)

@log_if_error
def request_pass_reset(email: str) -> Response:
  message=util.get_lang_pkg().CodeSent.value
  email=validate_email(email)
  user=su.get_user_by_email(email)
  time.sleep(0.1+(random.random()/5))
  if user is None:
    log_activity(False, {'err': f'Requested code for account of not known email: {email}'})
    return Response.success_response(message=message)
  code, _=sc.gen_code(user, CodePurposeEnum.ResetUserPassReq)
  log_activity(True, {'details': f'Code successfuly generated for {user.get_nick()}'})
  send_code_by_email(SendMail.sendResetReqest, email, code)
  return Response.success_response(message=message)

@log_if_error
def pass_reset(email: str, code: str) -> Response:
  message=util.get_lang_pkg().IncorrectCode.value
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(
      message,
      Exception(f'Requested code for account of not known email: {email}')
    )
  if sc.check_code(user, code, CodePurposeEnum.ResetUserPassReq) is None:
    raise MessageException(message)
  _code, _=sc.gen_code(user, CodePurposeEnum.ResetUserPass)
  return Response.success_response(_code.code)

@log_if_error
def pass_reset_new_pass(email: str, code: str, passwd: str, rep_passwd: str) -> Response:
  lang_pkg=util.get_lang_pkg()
  message=lang_pkg.IncorrectCode.value
  validate_passwords(passwd, rep_passwd)
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(
      message,
      Exception(f'Requested code for account of not known email: {email}')
    )
  if sc.check_code(user, code, CodePurposeEnum.ResetUserPass) is None:
    raise MessageException(message)
  if su.change_user_pass(user, passwd):
    log_activity(True, {'details': f'Successful password change for: {user.get_nick()}'})
    return Response.success_response()
  _code, _=sc.gen_code(user, CodePurposeEnum.ResetUserPass)
  return Response.error_response(
    lang_pkg.PasswordDoesNotMeetCriteria.value,
    _code.code
  )
