import os
from typing import Any, Self, Callable
from ..mail.Sender import SenderLoginOpt

class _Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class EnvConsts(metaclass=_Singleton):
    def __init__(self):
        self.__PEPPER__=self.__getenv_or_exception('PEPPER_VAL')
        for m_fun in self.__mandytory:
            m_fun(self)

    def getFlaskKey(self) -> str:
        return self.__getenv_or_exception('FLASK_KEY')
    def getAppDir(self) -> str:
        return self.__getenv_or_exception('APP_DIR')
    def getHttpsPort(self) -> int:
        return int(self.__getenv_or_exception('NGINX_HTTPS_OUTER_PORT'))
    def getServerName(self) -> str:
        return self.__getenv_or_exception('SERVER_NAME')
    
    def getDBString(self) -> str:
        return f'postgresql://{self.getDBUser()}:{self.getDBPass()}@{self.getDBHost()}/{self.getDB()}'
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
    def getMailData(self) -> tuple[str, int, str, str, str, SenderLoginOpt]:
        return (
            self.__getenv_or_exception('MAIL_HOST')
            ,int(self.__getenv_or_exception('MAIL_PORT'))
            ,self.__getenv_or_exception('MAIL_ADDRESS')
            ,self.__getenv_or_exception('MAIL_USERNAME')
            ,self.__getenv_or_exception('MAIL_PASSWORD')
            ,SenderLoginOpt(self.__getenv_or_exception('MAIL_AUTH_TYPE'))
        )
    
    def getPepper(self) -> str:
        return self.__PEPPER__
    
    __mandytory: set[Callable[[Self], Any]]={
        getFlaskKey
        ,getAppDir
        ,getHttpsPort
        ,getServerName
        ,getDBString
        ,getMailData
    }
    def __getenv_or_exception(self, name: str) -> str:
        ret=self.__getenv(name)
        if ret is None:
            raise Exception('Requested env does not exist')
        return ret
    def __getenv(self, name: str) -> str|None:
        return os.getenv(name)

envConsts=EnvConsts()
