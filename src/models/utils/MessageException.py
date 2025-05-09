from typing import Any, Self

class MessageException(RuntimeError):
    def __init__(self, message: str, data: Any=None, err: Exception|None=None) -> None:
        super().__init__(message)
        self.err=err
        self.data=data

    @classmethod
    def from_exception(cls, err: Exception, message: str|None=None, data: Any=None, log_message_exception: bool=False) -> Self:
        message=str(err) if message is None else message
        if isinstance(err, MessageException):
            return cls(
                message,
                data,
                err if log_message_exception else (
                    err.get_err_to_log() if err.is_to_log() else None
                )
            )
        return cls(message, data, err)

    def get_data(self) -> Any:
        return self.data

    def is_to_log(self) -> bool:
        return self.err is not None
    
    def get_err_to_log(self) -> Exception:
        if self.err is None:
            raise RuntimeError('Tried to access unset value')
        return self.err
