import os
from .Sender import Sender, SenderLoginOpt

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

    def sendCode(self, recievers: list[str], code: str) -> bool:
        try:
            self.__sender.send_mess('Kod do autoryzacji', recievers, f'''
                <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                    </head>
                    <body>
                        <h1>Hello!</h1>
                        Tu jest Twój kod do autoryzacji: <h3 style="margin:0;">{code}<h3>
                    </body>
                </html>
            ''')
        except Exception as e:
            return False
        return True

