import os
import html
from models.usr.Code import Code
from .Sender import Sender, SenderLoginOpt
from models.utils.MessageException import MessageException
from models.utils.utils import get_function
from models.utils.EnvConsts import envConsts as ec

def _get_link(url: str) -> str:
    port=ec.getHttpsPort()
    return f'https://{ec.getServerName()}{'' if port==443 else f':{port}'}/{url}'

class SendMail:
    __ERROR_MESSAGE='Błąd przy wysyłaniu mail\'a'
    def __init__(self):
        (host, port, addr, usr, passwd, auth_type)=ec.getMailData()
        self.__sender=Sender(host, port, addr, usr, passwd, auth_type)

    def sendInvite(self, reciever: str, code: Code, message: str|None=None) -> None:
        link=_get_link(f'user/accept_inv/{reciever}/{code.code}')
        try:
            self.__sender.send_mess('Zaproszenie', [reciever], f'''
                <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                    </head>
                    <body>
                        <h1>Hello, zostałeś(aś) zaproszony(a) do naszego programu!</h1>
                        {'' if message is None else f'Wiadomość: {html.escape(message)}<br>'}
                        Tu jest Twój link do autoryzacji: <a href="{link}">link</a><br>
                        Lub jeżeli wolisz własnoręcznie przekopiować link: {link}
                    </body>
                </html>
            ''')
        except Exception as e:
            raise MessageException.from_exception(e, self.__ERROR_MESSAGE)

    def sendCode(self, reciever: str, code: Code) -> None:
        link=_get_link(f'user/approve/{reciever}/{code.code}')
        try:
            self.__sender.send_mess('Kod do autoryzacji', [reciever], f'''
                <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                    </head>
                    <body>
                        <h1>Hello!</h1>
                        Tu jest Twój link do autoryzacji: <a href="{link}">link</a><br>
                        Lub jeżeli wolisz własnoręcznie przekopiować link: {link}
                    </body>
                </html>
            ''')
        except Exception as e:
            raise MessageException.from_exception(e, self.__ERROR_MESSAGE)

    def sendResetReqest(self, reciever: str, code: Code) -> None:
        link=_get_link(f'user/pass_reset/{reciever}/{code.code}')
        try:
            self.__sender.send_mess('Reset hasła', [reciever], f'''
                <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                    </head>
                    <body>
                        <h1>Hello!</h1>
                        Tu jest Twój link do resetu hasła: <a href="{link}">link</a><br>
                        Lub jeżeli wolisz własnoręcznie przekopiować link: {link}
                    </body>
                </html>
            ''')
        except Exception as e:
            raise MessageException.from_exception(e, self.__ERROR_MESSAGE)

