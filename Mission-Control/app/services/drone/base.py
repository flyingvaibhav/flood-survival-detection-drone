from abc import ABC, abstractmethod
from pydantic import BaseModel
from enum import Enum

class DroneMode(str, Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    DELIVERING = "DELIVERING"
    RETURNING = "RETURNING"
    MANUAL = "MANUAL"
    ERROR = "ERROR"

class DroneTelemetry(BaseModel):
    id: str
    mode: DroneMode
    battery: float
    lat: float
    lon: float
    altitude: float
    speed: float
    heading: float = 0.0
    current_task: str = "Ready"

class DroneInterface(ABC):
    @abstractmethod
    def get_telemetry(self) -> DroneTelemetry:
        pass

    @abstractmethod
    def arm(self):
        pass

    @abstractmethod
    def disarm(self):
        pass

    @abstractmethod
    def takeoff(self, altitude: float):
        pass

    @abstractmethod
    def land(self):
        pass

    @abstractmethod
    def goto(self, lat: float, lon: float, altitude: float):
        pass

    @abstractmethod
    def set_mode(self, mode: DroneMode):
        pass
