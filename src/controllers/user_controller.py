import datetime
from db.queries.user import user_loader_by_nick, is_user_existing, add_user
from models.mail.SendMail import SendMail
from models.utils.Response import Response
from models.utils.utils import get_function
from db.db_base import log_activity, log_err
from models.utils.utils import generate_code
from models.usr.User import User
from models.utils.Response import Response
from flask_login import login_user, logout_user, current_user 

def login(nick: str, passwd: str) -> Response:
  user = user_loader_by_nick(nick)
  if user is None:
    log_activity(get_function(), False, {'err': 'Nie prawidłowy login'})
    return Response.error_response(message = 'Nieprawidłowy login lub hasło')
  if not user.verify_pass(passwd):
    log_activity(get_function(), False, {'err': f'Nie prawidłowe hasło dla: {nick}'})
    return Response.error_response(message = 'Nieprawidłowy login lub hasło')

  login_user(user)
  return Response.success_response()

def logout() -> Response:
  logout_user()
  return Response.success_response()

def validate_passwords(passwd: str, rep_passwd: str) -> None:
  if passwd != rep_passwd:
    raise Exception('Podane nowe hasła nie pasują do siebie')

def check_password(passwd: str) -> str:
  user=User()
  passwd=user.ch_pass(passwd)
  if passwd is False:
    raise Exception('Konto nie zostało utworzone')
  return user.get_passwd()

def check_user_existence(nick: str, email: str) -> None:
    if is_user_existing(nick, email):
      raise Exception('Użytkownik o podanym nicku lub e-mailu już istnieje')

def send_validation_email(email: str, code: str) -> None:
  try:
    flag=False
    s=SendMail()
    if not s.sendCode([email], code):
      log_activity(get_function(), False, {'err': f'Nie prawidłowo wysłany kod do: {email}'})
      flag=True
  except Exception as e:
    log_err(get_function(), e)
    flag=True
  finally:
    if flag:
      raise Exception('Nie udało sie wysłać e-maila weryfikującego')

def create_user(nick: str, email: str, passwd: str, code: str, code_exp: int) -> None:
  user = User(nick=nick, email=email, passwd=passwd, approved=False,
              code=code, code_exp=datetime.datetime.now() + datetime.timedelta(seconds=code_exp))
  if not add_user(user):
    raise Exception('Konto nie zostało utworzone')

def signup_user(nick: str, email: str, passwd: str, rep_passwd: str) -> Response:
  try:
    validate_passwords(passwd, rep_passwd)
    passwd=check_password(passwd)
    check_user_existence(nick, email)
    
    code, code_exp=generate_code()
    send_validation_email(email, code)
    
    create_user(nick, email, passwd, code, code_exp)
    user=user_loader_by_nick(nick)
    login_user(user)
    log_activity(get_function(), True, {'details': f'Poprawnie stworzono konto: {nick}[{email}]'})
    return Response.success_response(
      message = f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code_exp/60}min'
    )
  except Exception as e:
    return Response.error_response(message=str(e))

def approve(code) -> Response:
  user: User=current_user
  if user.is_approved():
    return Response.error_response(message = 'Konto nie wymaga potwierdzenia')
  flag=user.approve(code)
  if flag:
    log_activity(get_function(), True, {'details': f'Poprawnie potwierdzono konto: {user.get_nick()}'})
    return Response.success_response()
  log_activity(get_function(), False, {'err': f'Wprowadzono nie prawidłowy kod dla: {user.get_nick()}'})
  return Response.error_response(message = 'Konto nie zostało potwierdzone')

def change_password(passwd, new_passwd, rep_passwd) -> Response:
  try:
    validate_passwords(new_passwd, rep_passwd)
    user: User=current_user
    if not user.verify_pass(passwd):
      log_activity(get_function(), False, {'err': f'Wprowadzono nie prawidłowe stare hasło dla: {user.get_nick()}'})
      return Response.error_response(message = 'Nieprawidłowe stare hasło')
    if not user.ch_pass(new_passwd):
      return Response.error_response(message = 'Nieprawidłowe stare hasło')
    log_activity(get_function(), True, {'details': f'Poprawnie zmieniono hasło konta: {user.get_nick()}'})
    return Response.success_response()
  except Exception as e:
    return Response.error_response(message = str(e))
