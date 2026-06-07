from fastapi import APIRouter
from backend.app.api.internal.v1 import business_analyst

router = APIRouter()

router.include_router(business_analyst.router, prefix="/business", tags=["internal-business"])
