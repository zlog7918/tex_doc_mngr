import json
import random
import inspect
import traceback
from flask import request
from typing import Callable
from .DB_Queries import DB_Queries
from datetime import datetime,timezone
from .db_drivers.DB_Driver import DB_Driver
from ..utils.consts import TIME_TO_EXPIRE

class DBQ_Users(DB_Queries):
    def __init__(self, db_conn_fun: Callable[[],DB_Driver]):
        try:
            self.__db=db_conn_fun()
        except Exception as e:
            self.__db=None

    def get_user(self, nick: str) -> tuple[str, str, str, bool]:
        try:
            ret=self.__db.query('SELECT nick, email, passwd, approved FROM usr WHERE nick=%(nick)s', {'nick':nick})[0]
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            raise err.with_traceback(err.__traceback__)
        return ret
    
    def change_user_passwd(self, nick: str, passwd: str) -> bool:
        try:
            self.__db.query('UPDATE usr SET passwd=%(passwd)s WHERE nick=%(nick)s', {'nick':nick, 'passwd':passwd}, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def add_user(self, nick: str, email: str, passwd: str) -> tuple[str, int]|None:
        r=random.Random()
        code=r.randint(0, 999999)
        code=f"{code:06d}"
        code_exp=TIME_TO_EXPIRE
        try:
            self.__db.query('''
                INSERT INTO usr(nick, email, passwd, code, code_exp) VALUES
                    (%(nick)s, %(email)s, %(passwd)s, %(code)s, (NOW()+((interval \'1 second\')*%(code_exp)s)))
            ''', {
                'nick': nick
                ,'email': email
                ,'passwd': passwd
                ,'code': code
                ,'code_exp': code_exp
            }, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return None
        return code, code_exp

    def approve_user(self, nick: str, code: str) -> bool:
        try:
            ret=self.__db.query('''
                UPDATE usr SET
                    code=''
                    ,approved=TRUE
                WHERE nick=%(nick)s
                    AND code=%(code)s
                    AND approved=FALSE
                    AND code_exp>=NOW()
                RETURNING approved
            ''', {'nick': nick, 'code': code})
            ret=len(ret)>0
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return ret

    def del_user(self, nick: str) -> bool:
        try:
            self.__db.query('DELETE FROM usr WHERE nick=%(nick)s', {'nick': nick}, False)
        except Exception as err:
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': f'{err}', 'traceback': ''.join(traceback.format_tb(err.__traceback__))}
            )
            return False
        return True

    def is_connection(self) -> bool:
        return self.__db is not None

    def __log_activity(self, action: str, is_success: bool, log: dict) -> None:
        try:
            self.__db.query('''
                INSERT INTO log(ip, is_success, "action", timest, "log") VALUES
                    (%(ip)s, %(is_success)s, %(act)s, %(timest)s, %(log)s)
            ''', {
                'ip':request.environ['REMOTE_ADDR'],
                'is_success':is_success,
                'act':action,
                'timest':self.__get_timestamp(),
                'log':json.dumps(log),
            }, False)
        except Exception as e:
            print('<h1>Operation failed, please inform an administrator.</h1>', action, log, self.__get_timestamp())

    def __get_timestamp(self) -> datetime:
        return datetime.today().astimezone(tz=timezone.utc)
