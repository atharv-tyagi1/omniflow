import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.schemas.public_api import PublicResponse

logger = logging.getLogger(__name__)

class PublicAPIException(Exception):
    """Base exception for explicit Public API errors."""
    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST", metadata: dict = None):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.metadata = metadata or {}
        super().__init__(self.message)

def create_public_error_response(status_code: int, message: str, code: str, metadata: dict = None) -> JSONResponse:
    content = PublicResponse(
        success=False,
        error={"message": message, "code": code},
        metadata=metadata or {}
    ).model_dump()
    return JSONResponse(status_code=status_code, content=content)

async def public_api_exception_handler(request: Request, exc: PublicAPIException):
    """Handle explicit public API errors."""
    if request.url.path.startswith("/api/public"):
        return create_public_error_response(exc.status_code, exc.message, exc.code, exc.metadata)
    # If thrown outside public, just return a generic error (though this shouldn't happen)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

async def public_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Sanitize FastAPI validation errors for public endpoints."""
    from fastapi.encoders import jsonable_encoder
    errors = jsonable_encoder(exc.errors())
    if request.url.path.startswith("/api/public"):
        return create_public_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Invalid request payload.",
            "VALIDATION_ERROR",
            {"details": errors}
        )
    # Re-raise or let the default handler take over if not public (FastAPI automatically handles unless we override globally)
    # For global override, we need to return the default format for internal APIs.
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )

async def public_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Sanitize generic HTTP exceptions (e.g. 404, 401)."""
    if request.url.path.startswith("/api/public"):
        # Map some common statuses
        code = "HTTP_ERROR"
        if exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 429:
            code = "RATE_LIMIT_EXCEEDED"
            
        return create_public_error_response(exc.status_code, str(exc.detail), code)
    
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

async def public_generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected 500s on public routes."""
    if request.url.path.startswith("/api/public"):
        logger.error(f"Unexpected error on public API: {exc}", exc_info=True)
        return create_public_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred.",
            "INTERNAL_SERVER_ERROR"
        )
    
    # Internal routes
    logger.error(f"Unexpected internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
