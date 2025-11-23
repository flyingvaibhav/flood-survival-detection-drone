import time
import threading
import math
from app.services.drone.base import DroneInterface, DroneTelemetry, DroneMode

class SimulatedDrone(DroneInterface):
    def __init__(self, drone_id: str, start_lat: float, start_lon: float):
        self.telemetry = DroneTelemetry(
            id=drone_id,
            mode=DroneMode.IDLE,
            battery=100.0,
            lat=start_lat,
            lon=start_lon,
            altitude=0.0,
            speed=0.0
        )
        self.target_lat = start_lat
        self.target_lon = start_lon
        self.target_alt = 0.0
        self.running = True
        self.thread = threading.Thread(target=self._physics_loop, daemon=True)
        self.thread.start()

    def _physics_loop(self):
        last_time = time.time()
        while self.running:
            dt = time.time() - last_time
            last_time = time.time()
            
            # Simple physics simulation
            # Move towards target
            speed = 5.0 # m/s
            if self.telemetry.mode in [DroneMode.SCANNING, DroneMode.DELIVERING, DroneMode.RETURNING]:
                dist = math.hypot(self.target_lat - self.telemetry.lat, self.target_lon - self.telemetry.lon)
                if dist > 0.00001:
                    angle = math.atan2(self.target_lon - self.telemetry.lon, self.target_lat - self.telemetry.lat)
                    move_dist = speed * dt * 0.00001 # approx conversion to degrees
                    
                    self.telemetry.lat += move_dist * math.cos(angle)
                    self.telemetry.lon += move_dist * math.sin(angle)
                    self.telemetry.speed = speed
                    self.telemetry.heading = math.degrees(angle)
                else:
                    self.telemetry.speed = 0.0
            
            # Battery drain
            if self.telemetry.mode != DroneMode.IDLE:
                self.telemetry.battery = max(0, self.telemetry.battery - (0.1 * dt))
            
            time.sleep(0.1)

    def get_telemetry(self) -> DroneTelemetry:
        return self.telemetry

    def arm(self):
        pass

    def disarm(self):
        pass

    def takeoff(self, altitude: float):
        self.target_alt = altitude
        self.telemetry.altitude = altitude

    def land(self):
        self.target_alt = 0
        self.telemetry.altitude = 0

    def goto(self, lat: float, lon: float, altitude: float):
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = altitude

    def set_mode(self, mode: DroneMode):
        self.telemetry.mode = mode
