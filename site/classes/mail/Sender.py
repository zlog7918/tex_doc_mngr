import smtplib
from enum import StrEnum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SenderLoginOpt(StrEnum):
    TSL='tsl'
    SSL='ssl'
    PLAIN='plain'

class Sender:
    def __init__(self, host: str, port: int, sender: str, user: str, passwd: str, auth_type: SenderLoginOpt):
        (
            self.__host
            ,self.__port
            ,self.__sender
            ,self.__user
            ,self.__passwd
            ,self.__auth_type
        )=(
            host
            ,port
            ,sender
            ,user
            ,passwd
            ,auth_type
        )

    def send_mess(self, subject: str, recievers: list[str], content_html: str, content_text: str|None=None):
        if content_text is None:
            msg=MIMEText(content_html, 'html')
        else:
            msg=MIMEMultipart('alternative')
            part1=MIMEText(content_text, 'plain')
            part2=MIMEText(content_html, 'html')
            msg.attach(part1)
            msg.attach(part2)
        
        msg['Subject']=subject
        msg['From']=self.__sender
        msg['To']=','.join(recievers)

        mail=smtplib.SMTP(self.__host, self.__port)
        match self.__auth_type:
            case SenderLoginOpt.TSL:
                mail.ehlo()
                mail.starttls()
                mail.login(self.__user, self.__passwd)
            case _:
                # TODO
                pass
        mail.sendmail(self.__sender, recievers, msg.as_string())
        mail.quit()

