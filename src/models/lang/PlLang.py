from enum import member
from .LangBase import LangBase

class PlLang(LangBase):
    UserNotFoundErr=member(lambda e:f'Nie znaleziono użytkownika: {e}')
    UserNotLogged='Nie jest zalogowany żaden użytkownik'
    UserNotAdded='Użytkownik nie został dodany'
    LaTeXtoPDFconvertError='Błąd konwertowania LaTeX to PDF'
