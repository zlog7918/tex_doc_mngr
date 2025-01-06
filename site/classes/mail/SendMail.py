import os

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
        pass

    def sendCode(self, recievers: list[str], code: str) -> bool:
        try:
            print(recievers, f'code: "{code}"')
        except:
            return False
        return True

