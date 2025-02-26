from typing import Optional, Dict, Self

class Response:
    def __init__(self, success: bool, message: str = "", data = None):
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
    def success_response(data = None, message: str = "OK") -> Self:
        return Response(success=True, message=message, data=data)

    @staticmethod
    def error_response(message: str, data = None) -> Self:
        return Response(success=False, message=message, data=data)