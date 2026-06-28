from fastapi import APIRouter

from backend.app.api.public.v1.chat import router as chat_router
from backend.app.api.public.v1.conversations import router as conversations_router
from backend.app.api.public.v1.customers import router as customers_router
from backend.app.api.public.v1.analytics import router as analytics_router
from backend.app.api.public.v1.intel import router as intel_router
from backend.app.api.public.v1.webhooks import router as webhooks_router
from backend.app.api.public.v1.voice import router as voice_router
from backend.app.api.public.v1.agents import router as public_agents_router

router = APIRouter()

router.include_router(chat_router)
router.include_router(conversations_router)
router.include_router(customers_router)
router.include_router(analytics_router)
router.include_router(intel_router)
router.include_router(webhooks_router)
router.include_router(voice_router)
router.include_router(public_agents_router)
