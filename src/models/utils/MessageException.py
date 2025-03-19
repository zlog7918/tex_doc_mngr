from typing import Self

class MessageException(RuntimeError):
    def __init__(self, message: str, err: Exception|None=None) -> None:
        super().__init__(message)
        self.err=err
    
    def is_to_log(self) -> bool:
        return self.err is not None
    
    def get_err_to_log(self) -> Exception:
        if self.err is None:
            raise RuntimeError('Tried to access unset value')
        return self.err
