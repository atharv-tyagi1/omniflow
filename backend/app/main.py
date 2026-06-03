from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.workspaces import router as workspaces_router
from backend.app.api.v1.conversations import router as conversations_router
from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.workflows import router as workflows_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.analyst import router as analyst_router
from backend.app.api.v1.telegram import router as telegram_router
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
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(workspaces_router, prefix=settings.API_V1_STR)
app.include_router(conversations_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(datasets_router, prefix=settings.API_V1_STR)
app.include_router(workflows_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(analyst_router, tags=["analyst"])  # Mounts /api/query and /api/limits
app.include_router(telegram_router, prefix=settings.API_V1_STR)
# Global custom exception handler
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
        content=error_response(code=exc.code, message=exc.message)
    )

# Fallback general exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=error_response(code="INTERNAL_SERVER_ERROR", message=str(exc))
    )

@app.get("/")
def read_root():
    return {
        "message": "Welcome to OmniFlow AI-Native Customer Operations Platform API",
        "version": settings.VERSION,
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "unverified",
        "gemini": "unverified"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
