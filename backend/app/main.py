from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings

# Enforce PostgreSQL guard on application startup
from backend.app.core.database import engine

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.workspaces import router as workspaces_router
from backend.app.api.v1.conversations import router as conversations_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.workflows import router as workflows_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.analyst import router as analyst_router
from backend.app.api.v1.telegram import router as telegram_router
from backend.app.api.v1.customers import router as customers_router
from backend.app.api.v1.tickets import router as tickets_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.intel import router as intel_router
from backend.app.api.v1.api_keys import router as api_keys_router
from backend.app.api.internal.v1.api import router as internal_v1_router
from backend.app.core.exceptions import OmniFlowError
from backend.app.core.response import error_response
from backend.app.core.scheduler import BackgroundScheduler
from backend.app.services.telegram_service import TelegramService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await BackgroundScheduler.start(interval_seconds=3600)  # run once an hour
    await TelegramService.setup_webhook()
    yield
    # Shutdown
    await BackgroundScheduler.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],  # Explicit origins required when allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.api.v1.router import router as router_router

# Register routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(workspaces_router, prefix=settings.API_V1_STR)
app.include_router(customers_router, prefix=settings.API_V1_STR)
app.include_router(conversations_router, prefix=settings.API_V1_STR)
app.include_router(tickets_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(datasets_router, prefix=settings.API_V1_STR)
app.include_router(workflows_router, prefix=settings.API_V1_STR)
app.include_router(router_router, prefix=settings.API_V1_STR)
app.include_router(api_keys_router, prefix=settings.API_V1_STR)
app.include_router(
    analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"]
)
app.include_router(
    analyst_router, tags=["analyst"]
)  # Mounts /api/query and /api/limits
from backend.app.api.public.v1.router import router as public_v1_router

app.include_router(telegram_router, prefix=settings.API_V1_STR)
app.include_router(intel_router, prefix=settings.API_V1_STR)
app.include_router(internal_v1_router, prefix="/api/internal/v1")
app.include_router(public_v1_router, prefix="/api/public/v1", tags=["public"])


from backend.app.core.public_errors import (
    PublicAPIException,
    public_api_exception_handler,
    public_validation_exception_handler,
    public_http_exception_handler,
    public_generic_exception_handler
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Register Public API Handlers
app.add_exception_handler(PublicAPIException, public_api_exception_handler)
app.add_exception_handler(RequestValidationError, public_validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, public_http_exception_handler)

# Global custom exception handler (Fallback for internal APIs)
@app.exception_handler(OmniFlowError)
async def omniflow_exception_handler(request: Request, exc: OmniFlowError):
    # Map exception types to HTTP status codes
    status_code = 400
    if exc.code == "AUTHENTICATION_ERROR":
        status_code = 401
    elif exc.code == "AUTHORIZATION_ERROR":
        status_code = 403
    elif exc.code == "NOT_FOUND":
        status_code = 404

    return JSONResponse(
        status_code=status_code,
        content=error_response(code=exc.code, message=exc.message),
    )


# Fallback general exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Let public exception handler process it if it's a public route
    if request.url.path.startswith("/api/public"):
        return await public_generic_exception_handler(request, exc)
    
    return JSONResponse(
        status_code=500,
        content=error_response(code="INTERNAL_SERVER_ERROR", message=str(exc)),
    )


from fastapi import Response
import httpx
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

@app.get("/")
def read_root():
    return {
        "message": "Welcome to OmniFlow AI-Native Customer Operations Platform API",
        "version": settings.VERSION,
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/ready")
async def readiness_check(response: Response):
    services = {"database": "unverified", "supabase": "unverified", "gemini": "unverified"}
    is_ready = True

    # 1. Database Connectivity (Supabase PostgreSQL)
    try:
        from backend.app.core.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        services["database"] = "ok"
    except Exception as e:
        services["database"] = f"error: {str(e)}"
        is_ready = False

    # 2. Supabase API Connectivity
    try:
        async with httpx.AsyncClient() as client:
            headers = {"apikey": settings.SUPABASE_ANON_KEY}
            api_resp = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/", headers=headers, timeout=5.0
            )
            if api_resp.status_code in [200, 204, 401]:
                services["supabase"] = "ok"
            else:
                services["supabase"] = f"error: status {api_resp.status_code}"
                is_ready = False
    except Exception as e:
        services["supabase"] = f"error: {str(e)}"
        is_ready = False

    # 3. Gemini Client Initialization
    try:
        key = settings.GEMINI_API_KEY
        if not key or key == "your-gemini-api-key" or key == "":
            services["gemini"] = "error: missing key"
            is_ready = False
        else:
            from google import genai
            # Just verify client initialization succeeds
            _client = genai.Client(api_key=key)
            services["gemini"] = "ok"
    except Exception as e:
        services["gemini"] = f"error: {str(e)}"
        is_ready = False

    if not is_ready:
        response.status_code = 503
        return {"status": "unavailable", "services": services}

    return {"status": "ready", "services": services}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
