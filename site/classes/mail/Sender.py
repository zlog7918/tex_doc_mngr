import smtplib
from enum import StrEnum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SenderLoginOpt(StrEnum):
    TSL='tsl'
    SSL='ssl'
    PLAIN='plain'
    NONE='none'

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

        mail=self.__prep_mail_sender()
        mail.sendmail(self.__sender, recievers, msg.as_string())
        mail.quit()

    def __prep_mail_sender(self) -> smtplib.SMTP|smtplib.SMTP_SSL:
        mail=smtplib.SMTP(self.__host, self.__port)
        match self.__auth_type:
            case SenderLoginOpt.SSL:
                # Not tested yet
                mail=smtplib.SMTP_SSL(self.__host, self.__port)
            case SenderLoginOpt.TSL:
                mail.ehlo()
                mail.starttls()
            case SenderLoginOpt.NONE:
                # Not tested yet
                return mail
            case _:
                # Not tested yet
                pass
        mail.login(self.__user, self.__passwd)
        return mail

