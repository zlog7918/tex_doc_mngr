import os
import html
from models.usr.Code import Code
from .Sender import Sender, SenderLoginOpt
from models.utils.MessageException import MessageException

def __get_link(url: str) -> str:
    port=int(os.getenv('NGINX_HTTPS_OUTER_PORT', '443'))
    return f'https://{os.getenv('SERVER_NAME', 'SERVER_NAME')}{'' if port==443 else f':{port}'}/{url}'

class SendMail:
    __ERROR_MESSAGE='Błąd przy wysyłaniu mail\'a'
    def __init__(self):
        (host, port, addr, usr, passwd, auth_type)=(
            os.environ.get('MAIL_HOST')
            ,os.environ.get('MAIL_PORT')
            ,os.environ.get('MAIL_ADDRESS')
            ,os.environ.get('MAIL_USERNAME')
            ,os.environ.get('MAIL_PASSWORD')
            ,os.environ.get('MAIL_AUTH_TYPE')
        )
        self.__sender=Sender(host, port, addr, usr, passwd, SenderLoginOpt(auth_type))

    def sendInvite(self, reciever: str, code: Code, message: str|None=None) -> None:
        link=__get_link(f'user/accept_inv/{reciever}/{code.code}')
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
        link=__get_link(f'user/approve/{reciever}/{code.code}')
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
        link=__get_link(f'user/pass_reset/{reciever}/{code.code}')
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

