"""CalcAI FastAPI Backend Service Entrypoint.

Exposes RESTful endpoints for health verification and Gemini AI chat interactions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router

app = FastAPI(
    title="CalcAI Backend Service",
    description="High-performance backend API bridging CalcAI mobile clients to Google Gemini models.",
    version="0.1.0",
)

# Explicit CORS configuration for mobile and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register route controllers with /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Service status and API documentation entry point."""
    return {
        "service": "CalcAI Backend",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.environment == "development"),
    )
