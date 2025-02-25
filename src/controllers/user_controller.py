import datetime
from models.mail.SendMail import SendMail
from models.utils.Response import Response
from models.utils.utils import generate_code
from models.usr.User import User, user_loader
from flask_login import login_user, logout_user, current_user 
import db.queries.user as uq

def login(nick: str, passwd: str):
  user = user_loader(nick)
  if user is None or not user.verify_pass(passwd):
    return Response.error_response(message = 'Nieprawidłowy login lub hasło')

  login_user(user)
  return Response.success_response()

def logout():
  logout_user()
  return Response.success_response()

def validate_passwords(passwd, rep_passwd):
  if passwd != rep_passwd:
    raise ValueError('Podane nowe hasła nie pasują do siebie')

def check_password(passwd):
  user=User()
  passwd=user.ch_pass(passwd)
  if passwd is False:
    raise ValueError('Konto nie zostało utworzone')

def check_user_existence(nick, email):
    existing_user = uq.is_user_existing(nick, email)
    if existing_user:
      raise ValueError('Użytkownik o podanym nicku lub e-mailu już istnieje')

def send_validation_email(email, code):
  try:
    flag=False
    s=SendMail()
    if not s.sendCode([email], code):
      flag=True
  except Exception as e:
    flag=True
  finally:
    if flag:
      raise ValueError('Nie udało sie wysłać e-maila weryfikującego')

def create_user(nick, email, passwd, code, code_exp):
  user = User(nick=nick, email=email, passwd=passwd, approved=False,
              code=code, code_exp=datetime.datetime.now() + datetime.timedelta(seconds=code_exp))
  if not uq.add_user(user):
    raise ValueError('Konto nie zostało utworzone')

def signup_user(nick, email, passwd, rep_passwd):
  try:
    validate_passwords(passwd, rep_passwd)
    check_password(passwd)
    check_user_existence(nick, email)
    
    code, code_exp=generate_code()
    send_validation_email(email, code)
    
    create_user(nick, email, passwd, code, code_exp)
    user=user_loader(nick)
    login_user(user)
    return Response.success_response(
      message = f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {code_exp/60}min'
    )
  except ValueError as e:
    return Response.error_response(message=str(e))

def approve(code):
  user: User=current_user
  if user.is_approved():
    return Response.error_response(message = 'Konto nie wymaga potwierdzenia')
  flag=user.approve(code)
  if flag:
    return Response.success_response()
  return Response.error_response(message = 'Konto nie zostało potwierdzone')
