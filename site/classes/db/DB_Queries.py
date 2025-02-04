from abc import abstractmethod

class DB_Queries:
    @abstractmethod
    def is_connection(self) -> bool:
        pass
