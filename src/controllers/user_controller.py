import re
import email_validator as emailV
from models.usr.User import User
from db.db_base import db, log_activity
from models.mail.SendMail import SendMail
from models.utils.Response import Response
from models.usr.Code import CodePurposeEnum
from services import user as su, code as sc
from models.utils.decors import log_if_error
from flask_login import login_user, logout_user
from typing import Callable, ParamSpec, Concatenate
from models.utils.MessageException import MessageException

P=ParamSpec('P')

def validate_nick(nick: str) -> None:
  ret_mess='Nick nie spełnia wymagań'
  try:
    nick.index('\n')
    raise MessageException(ret_mess)
  except ValueError:
    pass
  if re.match(r'^[a-zA-z][a-zA-Z0-9_-]{1,78}[a-zA-Z0-9]$', nick) is None:
    raise MessageException(ret_mess)


@log_if_error
def login(nick: str, passwd: str) -> Response:
  message='Nieprawidłowy login lub hasło'
  validate_nick(nick)
  user=su.get_user_by_nick(nick)
  if user is None:
    raise MessageException(
      message,
      Exception('Nie prawidłowy login')
    )
  if not user.verify_pass(passwd):
    raise MessageException(
      message,
      Exception(f'Nie prawidłowe hasło dla: {nick}')
    )

  login_user(user)
  log_activity(True, {'details': f'Poprawnie zalogowano konto: {user.get_nick()}'})
  return Response.success_response()

@log_if_error
def logout() -> Response:
  logout_user()
  return Response.success_response()

def validate_passwords(passwd: str, rep_passwd: str) -> None:
  if passwd != rep_passwd:
    raise MessageException('Podane nowe hasła nie pasują do siebie')

def check_password(passwd: str) -> str:
  user=User()
  flag=user.ch_pass(passwd)
  if flag is False:
    raise MessageException('Konto nie zostało utworzone')
  return user.get_passwd()

def check_user_existence(nick: str, email: str) -> None:
  if su.is_user_existing(nick, email):
    raise MessageException('Użytkownik o podanym nicku lub e-mailu już istnieje')

def send_code_by_email(send_func: Callable[Concatenate[SendMail, str, P], bool], email, *args: P.args, **kwargs: P.kwargs) -> None:
  flag=False
  try:
    s=SendMail()
    if not send_func(s, email, *args, **kwargs):
      raise Exception(f'Nie prawidłowo wysłany kod do: {email}')
  except MessageException as e:
    raise e from None
  except Exception as e:
    raise MessageException('Nie udało sie wysłać e-maila', e)
      

def create_user(nick: str|None, email: str, passwd: str) -> None:
  user = User(**{
    User.nick: nick,
    User.email: email,
    User.passwd: passwd,
  })
  su.add_user(user)

def validate_email(email: str) -> str:
  try:
    v=emailV.validate_email(email)
    return v.email
  except emailV.EmailNotValidError as e:
    raise MessageException('E-mail nie przeszedł weryfikacji')

@log_if_error
def signup_user(nick: str, email: str, passwd: str, rep_passwd: str) -> Response:
  db.session.begin()
  validate_nick(nick)
  validate_passwords(passwd, rep_passwd)
  email=validate_email(email)
  passwd=check_password(passwd)
  check_user_existence(nick, email)
  
  create_user(nick, email, passwd)
  user=su.get_user_by_nick(nick)
  if user is None:
    raise MessageException('Konto nie zostało utworzone')

  code, code_exp=sc.gen_code(user, CodePurposeEnum.ApproveUser)
  log_activity(True, {'details': f'Poprawnie wygenerowano kod dla {user.get_nick()}'})
  send_code_by_email(SendMail.sendCode, email, code)
  
  login_user(user)
  log_activity(True, {'details': f'Poprawnie stworzono konto: {nick}[{email}]'})
  return Response.success_response(
    message = f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code_exp/60}min'
  )

@log_if_error
def approve(email: str, code: str) -> Response:
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException('Konto nie wymaga potwierdzenia')
  if user.is_approved():
    raise MessageException('Konto nie wymaga potwierdzenia')
  if sc.check_code(user, code, CodePurposeEnum.ApproveUser):
    su.approve_user(user)
    log_activity(True, {'details': f'Poprawnie potwierdzono konto: {user.get_nick()}'})
    return Response.success_response()
  raise MessageException(
    'Konto nie zostało potwierdzone',
    Exception(f'Wprowadzono nie prawidłowy kod dla: {user.get_nick()}')
  )

@log_if_error
def change_password(passwd: str, new_passwd: str, rep_passwd: str) -> Response:
  validate_passwords(new_passwd, rep_passwd)
  user=su.get_curr_user_or_err()
  if not user.verify_pass(passwd):
    raise MessageException(
      'Nieprawidłowe stare hasło',
      Exception(f'Wprowadzono nie prawidłowe stare hasło dla: {user.get_nick()}')
    )
  if su.change_user_pass(user, new_passwd):
    log_activity(True, {'details': f'Poprawnie zmieniono hasło konta: {user.get_nick()}'})
    return Response.success_response()
  raise MessageException('Hasło nie spełnia wymogów')

@log_if_error
def request_pass_reset(email: str) -> Response:
  message='Wiadmość została pomyślnie wysłana'
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    log_activity(False, {'err': f'Żądany kod dla konta o nieistniejącym email: {email}'})
    # TODO: add sleep
    return Response.success_response(message=message)
  code, _=sc.gen_code(user, CodePurposeEnum.ResetUserPassReq)
  log_activity(True, {'details': f'Poprawnie wygenerowano kod dla {user.get_nick()}'})
  send_code_by_email(SendMail.sendResetReqest, email, code)
  return Response.success_response(message=message)

@log_if_error
def pass_reset(email: str, code: str) -> Response:
  message='Nie prawidłowy kod'
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(
      message,
      Exception(f'Próba zmiany hasła konta o nieistniejącym email: {email}')
    )
  if sc.check_code(user, code, CodePurposeEnum.ResetUserPassReq):
    _code, _=sc.gen_code(user, CodePurposeEnum.ResetUserPass)
    return Response.success_response(data=_code.code)
  raise MessageException(message)

@log_if_error
def pass_reset_new_pass(email: str, code: str, passwd: str, rep_passwd: str) -> Response:
  message='Nie prawidłowy kod'
  validate_passwords(passwd, rep_passwd)
  email=validate_email(email)
  user=su.get_user_by_email(email)
  if user is None:
    raise MessageException(
      message,
      Exception(f'Próba zmiany hasła konta o nieistniejącym email: {email}')
    )
  if sc.check_code(user, code, CodePurposeEnum.ResetUserPass):
    if su.change_user_pass(user, passwd):
      log_activity(True, {'details': f'Poprawnie zmieniono hasło konta: {user.get_nick()}'})
      return Response.success_response()
    _code, _=sc.gen_code(user, CodePurposeEnum.ResetUserPass)
    return Response.error_response(message='Hasło nie spełnia wymogów', data=_code.code)
  raise MessageException(message)
