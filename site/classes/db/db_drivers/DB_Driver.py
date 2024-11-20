class DB_Driver:
    def __init__(self, host: str, port: str, dbname: str, user: str, passwd: str):
        (self._host,self._port,self._dbname,self._user,self._passwd)=(host,port,dbname,user,passwd)
    def query(self, sql: str, data: list|dict|tuple=()) -> list[tuple]:
        pass
