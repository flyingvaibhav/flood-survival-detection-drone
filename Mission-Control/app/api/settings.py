from fastapi import APIRouter, HTTPException
from app.core.settings.manager import settings_manager
from app.core.settings.models import SystemSettings
from app.services.detector import streamer

router = APIRouter()

@router.get("/", response_model=SystemSettings)
async def get_settings():
    return settings_manager.get_settings()

@router.post("/")
async def update_settings(settings: dict):
    try:
        # Check if camera source is changing
        old_source = settings_manager.get_settings().camera.camera_source
        
        updated = settings_manager.update_settings(settings)
        
        new_source = updated.camera.camera_source
        
        if old_source != new_source:
            streamer.set_source(new_source)
            
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
