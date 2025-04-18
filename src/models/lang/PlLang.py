from enum import member
from .LangBase import LangBase

class PlLang(LangBase):
    UserNotFoundErr=member(lambda e: f'Nie znaleziono użytkownika: {e}')
    ConfirmAccountThroughCode=member(lambda time: f'Proszę potwierdzić konto za pomocą kodu z mail\'a w: {time}min')
    UserNotLogged='Nie jest zalogowany żaden użytkownik'
    UserNotAdded='Użytkownik nie został dodany'
    UserNotApproved='Konto nie zostało potwierdzone'
    UserNotDeleted='Konto nie zostało usunięte'
    PasswordNotChanged='Hasło nie zostało zmienione'
    FuncNotExecuted='Nie wykonano funkcji'
    AccountNotCreated='Konto nie zostało utworzone'
    CodeNotGenerated='Nie można wygenerować kodu'
    CodeNotDeactivated='Nie można deaktywować kodu'
    CodeNotApproved='Nie można potwierdzić kodu'
    NickDoesNotMeetCriteria='Nick nie spełnia wymagań'
    IncorrectNickOrPassword='Nieprawidłowy login lub hasło'
    PasswordsDoNotMatch='Podane nowe hasła nie pasują do siebie'
    UnsuccessfulMailSending='Nie udało sie wysłać e-maila'
    EmailDoesNotMeetCriteria='E-mail nie przeszedł weryfikacji'
    UserCanAcceptInviteThroughMail='Dana osoba będzie mogła przyjąć zaproszenie za pomocą kodu z mail\'a'
    UserNotInvited='Użytkownik nie został zaproszony'
    NickExistsOrInvalidPassword='Hasło nie spełnia wymogów lub użytkownik o podanym nick\'u już istnieje'
    IncorrectCode='Nieprawidłowy kod'
    EmailOrNickExists='Użytkownik o podanym nicku lub e-mailu już istnieje'
    UserAlreadyApproved='Konto nie wymaga potwierdzenia'
    IncorrectOldPassword='Nieprawidłowe stare hasło'
    PasswordDoesNotMeetCriteria='Hasło nie spełnia wymagań'
    UnknownErr='Wystąpił nie przewidziany błąd, przepraszamy za utrudnienia'
    UnknownDBErr='Wystąpił poważny błąd serwera, przepraszamy za utrudnienia'
    CodeSent='Wiadmość została pomyślnie wysłana'
