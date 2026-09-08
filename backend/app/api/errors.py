from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = {}


def error(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}
