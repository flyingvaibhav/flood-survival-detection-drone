from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum

class SurvivorStatus(str, Enum):
    DETECTED = "Detected"
    VERIFIED = "Verified"
    DELIVERED = "Kit Delivered"

class Survivor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lat: float
    lon: float
    confidence: float
    status: SurvivorStatus = Field(default=SurvivorStatus.DETECTED)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    image_path: Optional[str] = None

class MissionLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "INFO" # INFO, WARNING, ERROR
    message: str
    drone_id: Optional[str] = None
