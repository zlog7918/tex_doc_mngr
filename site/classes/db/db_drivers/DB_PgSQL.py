import sys
import psycopg2
import psycopg2._psycopg
from typing import Callable
from .DB_Driver import DB_Driver

class DB_PgSQL(DB_Driver):
    def __init__(self, host: str, port: str, dbname: str, user: str, passwd: str):
        super().__init__(host,port,dbname,user,passwd)
        self.conn_fun: Callable[[],psycopg2._T_conn]=lambda: psycopg2.connect(
            host=self._host
            ,port=self._port
            ,dbname=self._dbname
            ,user=self._user
            ,password=self._passwd
        )
        conn=err=traceback=None
        try:
            conn=self.conn_fun()
        except (Exception, psycopg2.DatabaseError) as error:
            _,_,traceback=sys.exc_info()
            err=error
        finally:
            if conn is not None:
                conn.close()
            if err is not None:
                raise err.with_traceback(traceback)

    def query(self, sql: str, data: list|dict|tuple=()) -> list[tuple]:
        if type(data) is list:
            if len(data)>0:
                if data[0] is list or data[0] is tuple or data[0] is dict:
                    raise AttributeError('query does not support multiple datas')
            data=tuple(data)

        conn=ret=None
        try:
            conn=self.conn_fun()
            cur: psycopg2._psycopg.cursor=conn.cursor()

            cur.execute(sql, data)
            ret=cur.fetchall()

            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return ret if ret is not None else []
