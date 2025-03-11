import re
from typing import Callable
import email_validator as emailV
from models.usr.User import User
from models.mail.SendMail import SendMail
from models.utils.Response import Response
from models.utils.utils import get_function
from services import user as su, code as sc
from db.db_base import log_activity, log_err
from models.usr.Code import Code, CodePurposeEnum
from flask_login import login_user, logout_user, current_user

def validate_nick(nick: str) -> None:
  ret_mess='Nick nie spełnia wymagań'
  try:
    nick.index('\n')
    raise Exception(ret_mess)
  except ValueError:
    pass
  if re.match(r'^[a-zA-z][a-zA-Z0-9_-]{1,78}[a-zA-Z0-9]$', nick) is None:
    raise Exception(ret_mess)


def login(nick: str, passwd: str) -> Response:
  try:
    validate_nick(nick)
  except Exception as e:
    return Response.error_response(message=str(e))
  user = su.user_loader_by_nick(nick)
  if user is None:
    log_activity(get_function(), False, {'err': 'Nie prawidłowy login'})
    return Response.error_response(message = 'Nieprawidłowy login lub hasło')
  if not user.verify_pass(passwd):
    log_activity(get_function(), False, {'err': f'Nie prawidłowe hasło dla: {nick}'})
    return Response.error_response(message = 'Nieprawidłowy login lub hasło')

  login_user(user)
  log_activity(get_function(), True, {'details': f'Poprawnie zalogowano konto: {user.get_nick()}'})
  return Response.success_response()

def logout() -> Response:
  logout_user()
  return Response.success_response()

def validate_passwords(passwd: str, rep_passwd: str) -> None:
  if passwd != rep_passwd:
    raise Exception('Podane nowe hasła nie pasują do siebie')

def check_password(passwd: str) -> str:
  user=User()
  flag=user.ch_pass(passwd)
  if flag is False:
    raise Exception('Konto nie zostało utworzone')
  return user.get_passwd()

def check_user_existence(nick: str, email: str) -> None:
  if su.is_user_existing(nick, email):
    raise Exception('Użytkownik o podanym nicku lub e-mailu już istnieje')

def send_code_by_email(send_func: Callable[[SendMail, str, Code], bool], email: str, code: Code) -> None:
  try:
    flag=False
    s=SendMail()
    if not send_func(s, email, code):
      log_activity(get_function(), False, {'err': f'Nie prawidłowo wysłany kod do: {email}'})
      flag=True
  except Exception as e:
    log_err(get_function(), e)
    flag=True
  finally:
    if flag:
      raise Exception('Nie udało sie wysłać e-maila weryfikującego')

def create_user(nick: str, email: str, passwd: str) -> None:
  user = User(nick=nick, email=email, passwd=passwd)
  if not su.add_user(user):
    raise Exception('Konto nie zostało utworzone')
  
def validate_email(email: str) -> str:
  try:
    v=emailV.validate_email(email)
    return v.email
  except emailV.EmailNotValidError as e:
    raise Exception('E-mail nie przeszedł weryfikacji')

def signup_user(nick: str, email: str, passwd: str, rep_passwd: str) -> Response:
  try:
    validate_nick(nick)
    validate_passwords(passwd, rep_passwd)
    email=validate_email(email)
    passwd=check_password(passwd)
    check_user_existence(nick, email)
    
    create_user(nick, email, passwd)
    user=su.user_loader_by_nick(nick)
    if user is None:
      return Response.error_response(message='Konto nie zostało utworzone')
    
    code=sc.gen_code(user, CodePurposeEnum.ApproveUser)
    send_code_by_email(SendMail.sendCode, email, code)
    
    login_user(user)
    log_activity(get_function(), True, {'details': f'Poprawnie stworzono konto: {nick}[{email}]'})
    return Response.success_response(
      message = f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code.code_exp/60}min'
    )
  except Exception as e:
    return Response.error_response(message=str(e))

def approve(email: str, code: str) -> Response:
  try:
    email=validate_email(email)
    user=su.user_loader_by_email(email)
    if user is None:
      return Response.error_response(message = 'Konto nie wymaga potwierdzenia')
    if user.is_approved():
      return Response.error_response(message = 'Konto nie wymaga potwierdzenia')
    if sc.check_code(user, code, CodePurposeEnum.ApproveUser):
      su.approve_user(user)
      log_activity(get_function(), True, {'details': f'Poprawnie potwierdzono konto: {user.get_nick()}'})
      return Response.success_response()
    log_activity(get_function(), False, {'err': f'Wprowadzono nie prawidłowy kod dla: {user.get_nick()}'})
    return Response.error_response(message = 'Konto nie zostało potwierdzone')
  except Exception as e:
    return Response.error_response(message = str(e))

def change_password(passwd: str, new_passwd: str, rep_passwd: str) -> Response:
  try:
    validate_passwords(new_passwd, rep_passwd)
    user=su.get_curr_user_or_err()
    if not user.verify_pass(passwd):
      log_activity(get_function(), False, {'err': f'Wprowadzono nie prawidłowe stare hasło dla: {user.get_nick()}'})
      return Response.error_response(message = 'Nieprawidłowe stare hasło')

    if su.change_user_pass(user, new_passwd):
      log_activity(get_function(), True, {'details': f'Poprawnie zmieniono hasło konta: {user.get_nick()}'})
      return Response.success_response()
    return Response.error_response(message = 'Hasło nie spełnia wymogów')
  except Exception as e:
    return Response.error_response(message = str(e))

def request_pass_reset(email: str) -> Response:
  message='Wiadmość została pomyślnie wysłana'
  try:
    email=validate_email(email)
    user=su.user_loader_by_email(email)
    if user is None:
      log_activity(get_function(), False, {'err': f'Żądany kod dla konta o nieistniejącym email: {email}'})
      # TODO: add sleep
      return Response.success_response(message=message)
    code=sc.gen_code(user, CodePurposeEnum.ResetUserPassReq)
    send_code_by_email(SendMail.sendResetReqest, email, code)
    return Response.success_response(message=message)
  except Exception as e:
    return Response.error_response(message=str(e))

def pass_reset(email: str, code: str) -> Response:
  message='Nie prawidłowy kod'
  try:
    email=validate_email(email)
    user=su.user_loader_by_email(email)
    if user is None:
      log_activity(get_function(), False, {'err': f'Próba zmiany hasła konta o nieistniejącym email: {email}'})
      return Response.error_response(message=message)
    if sc.check_code(user, code, CodePurposeEnum.ResetUserPassReq):
      _code=sc.gen_code(user, CodePurposeEnum.ResetUserPass)
      return Response.success_response(data=_code.code)
    return Response.error_response(message=message)
  except Exception as e:
    return Response.error_response(message=str(e))

def pass_reset_new_pass(email: str, code: str, passwd: str, rep_passwd: str) -> Response:
  message='Nie prawidłowy kod'
  try:
    validate_passwords(passwd, rep_passwd)
    email=validate_email(email)
    user=su.user_loader_by_email(email)
    if user is None:
      log_activity(get_function(), False, {'err': f'Próba zmiany hasła konta o nieistniejącym email: {email}'})
      return Response.error_response(message=message)
    if sc.check_code(user, code, CodePurposeEnum.ResetUserPass):
      if su.change_user_pass(user, passwd):
        log_activity(get_function(), True, {'details': f'Poprawnie zmieniono hasło konta: {user.get_nick()}'})
        return Response.success_response()
      _code=sc.gen_code(user, CodePurposeEnum.ResetUserPass)
      return Response.error_response(message='Hasło nie spełnia wymogów', data=_code.code)
    return Response.error_response(message=message)
  except Exception as e:
    return Response.error_response(message=str(e))  
