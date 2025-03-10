import os
from typing import Any, Callable
from .Singleton import Singleton

class EnvConsts(metaclass=Singleton):
    def __init__(self):
        self.__PEPPER__=self.__getenv_or_exception('PEPPER_VAL')
        for m_fun in self.__mandytory:
            m_fun()

    def getFlaskKey(self) -> str:
        return self.__getenv_or_exception('FLASK_KEY')
    def getAppDir(self) -> str:
        return self.__getenv_or_exception('APP_DIR')
    def getDBHost(self) -> str:
        return 'psql'
    def getDB(self) -> str:
        return self.__getenv_or_exception('POSTGRES_DB')
    def getDBUser(self) -> str:
        return self.__getenv_or_exception('POSTGRES_USER')
    def getDBPass(self) -> str:
        return self.__getenv_or_exception('POSTGRES_PASSWORD')
    def getDocFilesDir(self) -> str:
        ret=self.__getenv('DOC_FILES_DIR')
        return '/var/uploads' if ret is None else ret
    def getTempDir(self) -> str:
        ret=self.__getenv('TEMP_FOLDER')
        return '/tmp/uploads' if ret is None else ret
    def getMailData(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.__getenv_or_exception('MAIL_HOST')
            ,self.__getenv_or_exception('MAIL_PORT')
            ,self.__getenv_or_exception('MAIL_ADDRESS')
            ,self.__getenv_or_exception('MAIL_USERNAME')
            ,self.__getenv_or_exception('MAIL_PASSWORD')
            ,self.__getenv_or_exception('MAIL_AUTH_TYPE')
        )
    
    def getPepper(self) -> str:
        return self.__PEPPER__
    
    __mandytory: set[Callable[[], Any]]={getFlaskKey, getAppDir, getDBHost, getDB, getDBUser, getDBPass, getMailData}
    def __getenv_or_exception(self, name: str) -> str:
        ret=self.__getenv(name)
        if ret is None:
            raise Exception('Requested env does not exist')
        return ret
    def __getenv(self, name: str) -> str|None:
        return os.getenv(name)

envConsts=EnvConsts()     