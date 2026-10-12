"""Health check route for CalcAI Backend."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    api_key_configured: bool
    model: str
    environment: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def check_health():
    """Verify backend status, Gemini configuration, and active AI model."""
    return HealthResponse(
        status="healthy",
        api_key_configured=settings.is_api_key_valid,
        model=settings.active_model,
        environment=settings.environment,
        version="0.1.0",
    )
