from sqlmodel import Session, select
from app.core.database import engine
from app.models.models import Survivor, MissionLog, SurvivorStatus
from app.services.drone.simulated import SimulatedDrone
from app.services.drone.base import DroneMode
from app.core.config import settings
import math
import time
import threading

class MissionCoordinator:
    def __init__(self):
        self.scout = SimulatedDrone(settings.SCOUT_DRONE_ID, settings.DEFAULT_LAT, settings.DEFAULT_LON)
        self.delivery = SimulatedDrone(settings.DELIVERY_DRONE_ID, settings.DEFAULT_LAT, settings.DEFAULT_LON)
        self.start_time = time.time()
        self.mission_active = False

    def log_event(self, message: str, level: str = "INFO", drone_id: str = None):
        with Session(engine) as session:
            log = MissionLog(message=message, level=level, drone_id=drone_id)
            session.add(log)
            session.commit()

    def add_survivor(self, lat: float, lon: float, conf: float, image_path: str = None):
        with Session(engine) as session:
            # Check duplicates
            statement = select(Survivor)
            results = session.exec(statement).all()
            for s in results:
                dist = math.hypot(s.lat - lat, s.lon - lon)
                if dist < 0.0001:
                    # Update image if better confidence
                    if conf > s.confidence and image_path:
                        s.confidence = conf
                        s.image_path = image_path
                        session.add(s)
                        session.commit()
                    return s.id
            
            survivor = Survivor(lat=lat, lon=lon, confidence=conf, image_path=image_path)
            session.add(survivor)
            session.commit()
            session.refresh(survivor)
            self.log_event(f"Survivor detected at {lat:.5f}, {lon:.5f}", "INFO", self.scout.telemetry.id)
            return survivor.id

    def start_scan(self):
        self.scout.set_mode(DroneMode.SCANNING)
        self.scout.takeoff(10)
        self.scout.telemetry.current_task = "Scanning Sector A"
        self.log_event("Mission Started: Scanning", "INFO", self.scout.telemetry.id)

    def stop_scan(self):
        self.scout.set_mode(DroneMode.IDLE)
        self.scout.land()
        self.scout.telemetry.current_task = "Hovering"
        self.log_event("Mission Stopped", "INFO", self.scout.telemetry.id)

    def deploy_delivery(self, path_indices):
        self.delivery.set_mode(DroneMode.DELIVERING)
        self.delivery.takeoff(10)
        self.delivery.telemetry.current_task = "Starting Delivery Run"
        self.log_event("Delivery Drone Deployed", "INFO", self.delivery.telemetry.id)
        
        # Start background thread for delivery simulation
        threading.Thread(target=self._run_delivery_mission, args=(path_indices,), daemon=True).start()

    def _run_delivery_mission(self, path_indices):
        with Session(engine) as session:
            survivors = session.exec(select(Survivor)).all()
            # Map indices to survivors (assuming 0 is home)
            # This logic needs to match the planner's index mapping
            
            for idx in path_indices:
                if idx == 0: continue # Home
                
                # Find survivor (simplified, assuming list order matches)
                if idx - 1 < len(survivors):
                    target = survivors[idx-1]
                    self.delivery.telemetry.current_task = f"En route to Survivor #{target.id}"
                    self.delivery.goto(target.lat, target.lon, 10)
                    time.sleep(5) # Simulate flight time
                    
                    self.delivery.telemetry.current_task = f"Dropping Kit for #{target.id}"
                    time.sleep(2)
                    
                    target.status = SurvivorStatus.DELIVERED
                    session.add(target)
                    session.commit()
                    self.log_event(f"Kit Delivered to Survivor #{target.id}", "SUCCESS", self.delivery.telemetry.id)

            self.delivery.telemetry.current_task = "Returning Home"
            self.delivery.goto(settings.DEFAULT_LAT, settings.DEFAULT_LON, 10)
            time.sleep(5)
            self.delivery.land()
            self.delivery.set_mode(DroneMode.IDLE)
            self.delivery.telemetry.current_task = "Mission Complete"
            self.log_event("Delivery Mission Complete", "SUCCESS", self.delivery.telemetry.id)

coordinator = MissionCoordinator()
