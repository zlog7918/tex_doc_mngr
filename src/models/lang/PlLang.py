from enum import member
from .LangBase import LangBase

class PlLang(LangBase):
    UserNotFoundErr=member(lambda e: f'Nie znaleziono użytkownika: {e}')
    UserNotLogged='Nie jest zalogowany żaden użytkownik'
    UserNotAdded='Użytkownik nie został dodany'
    UserNotApproved='Konto nie zostało potwierdzone'
    UserNotDeleted='Konto nie zostało usunięte'
    PasswordNotChanged='Hasło nie zostało zmienione'
    FuncNotExecuted='Nie wykonano funkcji'
    AccountNotCreated='Konto nie zostało utworzone'
