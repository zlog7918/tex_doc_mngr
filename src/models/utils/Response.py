from typing import Any, Self

class Response:
    def __init__(self, success: bool, message: str = "", data: Any = None):
        self.success = success
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        response = {
            "success": self.success,
            "data": self.data,
            "message": self.message
        }
        return response

    @classmethod
    def success_response(cls, data: Any = None, message: str = "OK") -> Self:
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, data: Any = None) -> Self:
        return cls(success=False, message=message, data=data)