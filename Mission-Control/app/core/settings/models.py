from pydantic import BaseModel
from typing import Optional

class FlightCheckSettings(BaseModel):
    pre_flight_check: bool = True
    battery_threshold: int = 20
    gps_satellite_min: int = 6
    imu_calibration_check: bool = True
    propeller_check: bool = True

class DroneSettings(BaseModel):
    rth_altitude: int = 30
    max_speed: int = 10
    geofence_enabled: bool = True
    obstacle_avoidance: bool = True
    flight_mode: str = "STABILIZE" # STABILIZE, LOITER, AUTO

class CameraSettings(BaseModel):
    resolution: str = "1080p"
    fps: int = 30
    thermal_enabled: bool = False
    auto_record: bool = True
    ai_confidence: float = 0.5

class MavlinkSettings(BaseModel):
    connection_string: str = "udp:127.0.0.1:14550"
    baud_rate: int = 57600
    system_id: int = 1
    component_id: int = 1
    heartbeat_timeout: int = 5

class ProfileSettings(BaseModel):
    pilot_name: str = "Commander"
    organization: str = "Disaster Relief Corp"
    theme: str = "dark"
    notifications: bool = True

class SystemSettings(BaseModel):
    flight_check: FlightCheckSettings = FlightCheckSettings()
    drone: DroneSettings = DroneSettings()
    camera: CameraSettings = CameraSettings()
    mavlink: MavlinkSettings = MavlinkSettings()
    profile: ProfileSettings = ProfileSettings()
