import datetime
from db.queries.user import user_loader_by_nick, is_user_existing, add_user
from models.mail.SendMail import SendMail
from models.utils.Response import Response
from models.utils.utils import generate_code
from models.usr.User import User
from models.utils.Response import Response
from flask_login import login_user, logout_user, current_user 

def login(nick: str, passwd: str) -> Response:
  user = user_loader_by_nick(nick)
  if user is None or not user.verify_pass(passwd):
    return Response.error_response(message = 'Nieprawidłowy login lub hasło')

  login_user(user)
  return Response.success_response()

def logout() -> Response:
  logout_user()
  return Response.success_response()

def validate_passwords(passwd: str, rep_passwd: str) -> None:
  if passwd != rep_passwd:
    raise Exception('Podane nowe hasła nie pasują do siebie')

def check_password(passwd: str) -> None:
  user=User()
  passwd=user.ch_pass(passwd)
  if passwd is False:
    raise Exception('Konto nie zostało utworzone')

def check_user_existence(nick: str, email: str) -> None:
    existing_user = is_user_existing(nick, email)
    if existing_user:
      raise Exception('Użytkownik o podanym nicku lub e-mailu już istnieje')

def send_validation_email(email: str, code: str) -> None:
  try:
    flag=False
    s=SendMail()
    if not s.sendCode([email], code):
      flag=True
  except Exception as e:
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
    check_password(passwd)
    check_user_existence(nick, email)
    
    code, code_exp=generate_code()
    send_validation_email(email, code)
    
    create_user(nick, email, passwd, code, code_exp)
    user=user_loader_by_nick(nick)
    login_user(user)
    return Response.success_response(
      message = f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code_exp/60}min'
    )
  except Exception as e:
    return Response.error_response(message=str(e))

def approve(code: str) -> Response:
  user: User=current_user
  if user.is_approved():
    return Response.error_response(message = 'Konto nie wymaga potwierdzenia')
  flag=user.approve(code)
  if flag:
    return Response.success_response()
  return Response.error_response(message = 'Konto nie zostało potwierdzone')

def change_password(passwd: str, new_passwd: str, rep_passwd: str) -> Response:
  try:
    validate_passwords(new_passwd, rep_passwd)
    user: User=current_user
    if not user.verify_pass(passwd):
      return Response.error_response(message = 'Nieprawidłowe stare hasło')
    if not user.ch_pass(new_passwd):
      return Response.error_response(message = 'Nieprawidłowe stare hasło')
    return Response.success_response()
  except Exception as e:
    return Response.error_response(message = str(e))