from typing import Generic, TypeVar, Optional, Dict

T = TypeVar("T")

class Response(Generic[T]):
    def __init__(self, success: bool, message: str = "", data: Optional[T] = None):
        self.success = success
        self.message = message
        self.data = data

    def to_dict(self) -> Dict:
        response = {
            "success": self.success,
            "data": self.data,
            "message": self.message
        }
        return response

    @staticmethod
    def success_response(data: Optional[T] = None, message: str = "OK") -> "Response[T]":
        return Response(success=True, message=message, data=data).to_dict()

    @staticmethod
    def error_response(message: str, data: Optional[T] = None) -> "Response[T]":
        return Response(success=False, message=message, data=data).to_dict()