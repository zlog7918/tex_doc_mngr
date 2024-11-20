import os
from threading import Lock
from enum import Enum, auto
from typing import Callable
from .DB_Queries import DB_Queries
from .db_drivers.DB_PgSQL import DB_PgSQL
from .db_drivers.DB_Driver import DB_Driver

class DB_QueriesOpt(Enum):
    DB_Queries=auto()
    def get_fun(self) -> Callable[[],DB_Driver]:
        driver=self.__get_driver()
        return lambda: driver(self.__get_host(), self.__get_port(), self.__get_db_name(), self.__get_user(), self.__get_pass())

    def __get_driver(self) -> DB_Driver:
        match self:
            case DB_QueriesOpt.DB_Queries:
                return DB_PgSQL
    
    def __get_host(self) -> str:
        match self:
            case DB_QueriesOpt.DB_Queries:
                return 'psql'

    def __get_port(self) -> str:
        match self:
            case DB_QueriesOpt.DB_Queries:
                return '5432'

    def __get_db_name(self) -> str:
        match self:
            case DB_QueriesOpt.DB_Queries:
                return os.environ.get('POSTGRES_DB', 'POSTGRES_DB')

    def __get_user(self) -> str:
        match self:
            case DB_QueriesOpt.DB_Queries:
                return os.environ.get('POSTGRES_USER', 'POSTGRES_USER')

    def __get_pass(self) -> str:
        match self:
            case DB_QueriesOpt.DB_Queries:
                return os.environ.get('POSTGRES_PASSWORD', 'POSTGRES_PASSWORD')

class DB_Factory:
    __dbs: dict[DB_QueriesOpt, DB_Queries]={}
    __lock=Lock()

    @staticmethod
    def get_db(opt: DB_QueriesOpt) -> DB_Queries:
        try:
            DB_Factory.__lock.acquire()
        except:
            pass
        db=DB_Factory.__get_db_fun(opt)
        DB_Factory.__lock.release()
        return db

    @staticmethod
    def __get_db_fun(opt: DB_QueriesOpt) -> DB_Queries:
        if opt in DB_Factory.__dbs:
            return DB_Factory.__dbs[opt]
        db=opt.get_fun()
        db=DB_Factory.__dbs[opt]=DB_Queries(db)
        return db
