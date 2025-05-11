from typing import Any, Self

class Response:
    def __init__(self, success: bool, message: str = "", data: Any = None):
        self.success = success
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        if isinstance(self.data, list):
            serialized_data = [
                item.to_dict() if hasattr(item, 'to_dict') else item
                for item in self.data
            ]
        else:
            serialized_data = self.data.to_dict() if hasattr(self.data, 'to_dict') else self.data

        return {
            "success": self.success,
            "data": serialized_data,
            "message": self.message
        }

    @classmethod
    def success_response(cls, data: Any = None, message: str = "OK") -> Self:
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(cls, message: str, data: Any = None) -> Self:
        return cls(success=False, message=message, data=data)