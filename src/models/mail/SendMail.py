import os
from db.db_base import log_err
from models.usr.Code import Code
from .Sender import Sender, SenderLoginOpt
from models.utils.utils import get_function

class SendMail:
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

    def sendCode(self, reciever: str, code: Code) -> bool:
        port=int(os.getenv('NGINX_HTTPS_OUTER_PORT', '443'))
        link=f'https://{os.getenv('SERVER_NAME', 'SERVER_NAME')}{'' if port==443 else f':{port}'}/user/approve/{reciever}/{code.code}'
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
            log_err(get_function(), e)
            return False
        return True

    def sendResetReqest(self, reciever: str, code: Code) -> bool:
        port=int(os.getenv('NGINX_HTTPS_OUTER_PORT', '443'))
        link=f'https://{os.getenv('SERVER_NAME', 'SERVER_NAME')}{'' if port==443 else f':{port}'}/user/pass_reset/{reciever}/{code.code}'
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
            log_err(get_function(), e)
            return False
        return True

