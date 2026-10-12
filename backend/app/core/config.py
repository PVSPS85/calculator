"""Application settings and environment configuration for CalcAI Backend."""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Locate .env in backend directory or parent project directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Strongly typed application configuration."""

    # Gemini API Settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.8-flash"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    log_level: str = "info"

    # CORS Configuration
    allowed_origins: str = "*"

    # Validation Guardrails
    max_message_length: int = 4000
    max_history_turns: int = 20

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def active_model(self) -> str:
        """Map legacy or retired model names to the currently supported Gemini model."""
        deprecated = {"gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.0-pro"}
        if self.gemini_model in deprecated:
            return "gemini-3.8-flash"
        return self.gemini_model

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated allowed origins."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_api_key_valid(self) -> bool:
        """Check if a genuine, non-placeholder API key is configured."""
        if not self.gemini_api_key:
            return False
        cleaned = self.gemini_api_key.strip()
        return bool(cleaned and cleaned != "your_gemini_api_key_here")


settings = Settings()
