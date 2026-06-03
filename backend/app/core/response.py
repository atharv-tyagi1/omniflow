"""Standardised API response wrappers for OmniFlow."""

from typing import Any, Optional
from pydantic import BaseModel


def success_response(data: Any = None) -> dict:
    """Wrap data in the standard success envelope."""
    return {"success": True, "data": data}


def error_response(code: str, message: str, status_code: int = 400) -> dict:
    """Build the standard error envelope (status_code is for the caller)."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


class SuccessResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
