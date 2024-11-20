import os
import sys
import json
import inspect
from flask import request
from typing import Callable
from datetime import datetime,timezone
from .db_drivers.DB_Driver import DB_Driver

class DB_Queries:
    def __init__(self, db_conn_fun: Callable[[],DB_Driver]):
        try:
            self.__db=db_conn_fun()
        except Exception as e:
            self.__db=None

    def get_test(self) -> str:
        try:
            ret=self.__db.query('SELECT t FROM test LIMIT 1')[0][0]
        except Exception as err:
            _,_,traceback=sys.exc_info()
            self.__log_activity(
                inspect.currentframe().f_code.co_name,
                False,
                {'err': err, 'traceback': traceback}
            )
            ret='ERROR'
        return ret

    def is_connection(self) -> bool:
        return self.__db is not None

    def __log_activity(self, action: str, is_success: bool, log: dict) -> None:
        try:
            q=self.__db.query('''
                INSERT INTO log(ip, is_success, action, timest, log) VALUES
                    (%(ip)s, %(is_success)s, %(act)s, %(timest)s, %(log)s)
            ''', {
                'ip':request.environ['REMOTE_ADDR'],
                'is_success':is_success,
                'act':action,
                'timest':self.__get_timestamp(),
                'log':json.dumps(log),
            })
        except Exception as e:
            print('<h1>Operation failed, please inform an administrator.</h1>', action, log, self.__get_timestamp())

    def __get_timestamp(self) -> datetime:
        return datetime.today().astimezone(tz=timezone.utc)
