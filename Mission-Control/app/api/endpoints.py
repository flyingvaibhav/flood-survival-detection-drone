from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.models import Survivor, MissionLog
from app.services.mission.coordinator import coordinator
from app.services.detector import streamer
from app.services.planner import solve_tsp
from app.core.config import settings
import time

router = APIRouter()

@router.get("/video_feed")
def video_feed():
    return StreamingResponse(streamer.generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/status")
def get_status(session: Session = Depends(get_session)):
    survivors = session.exec(select(Survivor)).all()
    return {
        "scout": coordinator.scout.get_telemetry(),
        "delivery": coordinator.delivery.get_telemetry(),
        "survivors": survivors,
        "mission_time": time.time() - coordinator.start_time
    }

@router.post("/mission/start_scan")
def start_scan():
    coordinator.start_scan()
    streamer.start()
    return {"status": "Scan started"}

@router.post("/mission/stop_scan")
def stop_scan():
    coordinator.stop_scan()
    streamer.stop()
    return {"status": "Scan stopped"}

@router.post("/mission/deploy_delivery")
def deploy_delivery(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    survivors = session.exec(select(Survivor)).all()
    if not survivors:
        return {"status": "No survivors to deliver to"}
    
    # Calculate route
    points = [(s.lat, s.lon) for s in survivors]
    # Add home base as start
    home = (coordinator.delivery.telemetry.lat, coordinator.delivery.telemetry.lon)
    points.insert(0, home)
    
    path_indices = solve_tsp(points, start_index=0)
    
    # Deploy
    coordinator.deploy_delivery(path_indices)
    
    return {"status": "Delivery Drone Deployed", "path": path_indices}

@router.get("/logs")
def get_logs(session: Session = Depends(get_session)):
    logs = session.exec(select(MissionLog).order_by(MissionLog.timestamp.desc()).limit(50)).all()
    return logs
