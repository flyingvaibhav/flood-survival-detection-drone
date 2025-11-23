from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel
import time
import math

class DroneMode(str, Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    DELIVERING = "DELIVERING"
    RETURNING = "RETURNING"
    MANUAL = "MANUAL"

class DroneStatus(BaseModel):
    id: str
    mode: DroneMode
    battery: float
    lat: float
    lon: float
    altitude: float
    speed: float
    current_task: str = "Ready"

class Survivor(BaseModel):
    id: int
    lat: float
    lon: float
    confidence: float
    timestamp: float
    status: str = "Detected" # Detected, Verified, Kit Delivered

class MissionState:
    def __init__(self):
        self.scout = DroneStatus(
            id="SCOUT-01", mode=DroneMode.IDLE, battery=100.0, 
            lat=28.6139, lon=77.2090, altitude=0, speed=0
        )
        self.delivery = DroneStatus(
            id="DELIVERY-01", mode=DroneMode.IDLE, battery=100.0, 
            lat=28.6139, lon=77.2090, altitude=0, speed=0
        )
        self.survivors: List[Survivor] = []
        self.start_time = time.time()

    def update_drone(self, drone_type: str, **kwargs):
        drone = self.scout if drone_type == "scout" else self.delivery
        for k, v in kwargs.items():
            if hasattr(drone, k):
                setattr(drone, k, v)

    def add_survivor(self, lat, lon, conf):
        # Check for duplicates within ~10 meters (approx 0.0001 degrees)
        for s in self.survivors:
            dist = math.hypot(s.lat - lat, s.lon - lon)
            if dist < 0.0001:
                # Update confidence if higher
                if conf > s.confidence:
                    s.confidence = conf
                    s.timestamp = time.time()
                return s.id
        
        s_id = len(self.survivors) + 1
        self.survivors.append(Survivor(
            id=s_id, lat=lat, lon=lon, confidence=conf, timestamp=time.time()
        ))
        return s_id

mission_state = MissionState()
