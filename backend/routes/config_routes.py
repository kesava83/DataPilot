from typing import Optional, Literal
from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


class UpdateSettingsRequest(BaseModel):
    # AI Settings
    ai_provider: Optional[Literal["gemini", "openai", "ollama", "mock"]] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    
    # Execution Settings
    read_only_mode: Optional[bool] = None


def mask_key(k: Optional[str]) -> str:
    if not k:
        return ""
    if len(k) <= 8:
        return "********"
    return k[:4] + "...." + k[-4:]


@router.get("")
def get_config():
    """Returns current configuration with sensitive secrets masked."""
    return {
        "ai": {
            "provider": settings.ai.provider,
            "gemini_api_key_set": bool(settings.ai.gemini_api_key),
            "gemini_api_key_masked": mask_key(settings.ai.gemini_api_key),
            "gemini_model": settings.ai.gemini_model,
            "openai_api_key_set": bool(settings.ai.openai_api_key),
            "openai_api_key_masked": mask_key(settings.ai.openai_api_key),
            "openai_model": settings.ai.openai_model,
            "ollama_base_url": settings.ai.ollama_base_url,
            "ollama_model": settings.ai.ollama_model,
        },
        "db": {
            "mode": settings.db.mode,
            "host": settings.db.host,
            "port": settings.db.port,
            "database": settings.db.database,
            "user": settings.db.user,
            "sslmode": settings.db.sslmode,
            "schema_name": settings.db.schema_name,
            "has_password": bool(settings.db.password),
        },
        "read_only_mode": settings.read_only_mode,
    }


@router.post("")
def update_config(req: UpdateSettingsRequest):
    """Updates AI provider and app settings in memory."""
    if req.ai_provider is not None:
        settings.ai.provider = req.ai_provider
    if req.gemini_api_key is not None and req.gemini_api_key.strip():
        settings.ai.gemini_api_key = req.gemini_api_key.strip()
    if req.gemini_model is not None:
        settings.ai.gemini_model = req.gemini_model.strip()
    if req.openai_api_key is not None and req.openai_api_key.strip():
        settings.ai.openai_api_key = req.openai_api_key.strip()
    if req.openai_model is not None:
        settings.ai.openai_model = req.openai_model.strip()
    if req.ollama_base_url is not None:
        settings.ai.ollama_base_url = req.ollama_base_url.strip()
    if req.ollama_model is not None:
        settings.ai.ollama_model = req.ollama_model.strip()
    if req.read_only_mode is not None:
        settings.read_only_mode = req.read_only_mode

    return {
        "success": True,
        "message": "Configuration updated successfully.",
        "config": get_config()
    }
