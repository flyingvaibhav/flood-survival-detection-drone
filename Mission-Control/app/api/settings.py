from fastapi import APIRouter, HTTPException
from app.core.settings.manager import settings_manager
from app.core.settings.models import SystemSettings

router = APIRouter()

@router.get("/", response_model=SystemSettings)
async def get_settings():
    return settings_manager.get_settings()

@router.post("/")
async def update_settings(settings: dict):
    try:
        updated = settings_manager.update_settings(settings)
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
