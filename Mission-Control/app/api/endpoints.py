from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.core.drone_state import mission_state, DroneMode
from app.services.detector import streamer
from app.services.planner import solve_tsp
import time

router = APIRouter()

@router.get("/video_feed")
def video_feed():
    return StreamingResponse(streamer.generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/status")
def get_status():
    return {
        "scout": mission_state.scout,
        "delivery": mission_state.delivery,
        "survivors": mission_state.survivors,
        "mission_time": time.time() - mission_state.start_time
    }

@router.post("/mission/start_scan")
def start_scan():
    mission_state.scout.mode = DroneMode.SCANNING
    mission_state.scout.current_task = "Scanning Sector A"
    streamer.start()
    return {"status": "Scan started"}

@router.post("/mission/stop_scan")
def stop_scan():
    mission_state.scout.mode = DroneMode.IDLE
    mission_state.scout.current_task = "Hovering"
    streamer.stop()
    return {"status": "Scan stopped"}

@router.post("/mission/deploy_delivery")
def deploy_delivery(background_tasks: BackgroundTasks):
    if not mission_state.survivors:
        return {"status": "No survivors to deliver to"}
    
    mission_state.delivery.mode = DroneMode.DELIVERING
    mission_state.delivery.current_task = "Calculating Route..."
    
    # Calculate route
    points = [(s.lat, s.lon) for s in mission_state.survivors]
    # Add home base as start
    home = (mission_state.delivery.lat, mission_state.delivery.lon)
    points.insert(0, home)
    
    path_indices = solve_tsp(points, start_index=0)
    
    # Simulate delivery in background
    background_tasks.add_task(simulate_delivery_mission, path_indices)
    
    return {"status": "Delivery Drone Deployed", "path": path_indices}

def simulate_delivery_mission(path_indices):
    # Mock simulation
    mission_state.delivery.current_task = "En route to Survivor 1"
    time.sleep(5)
    mission_state.delivery.current_task = "Dropping Kit..."
    time.sleep(2)
    mission_state.delivery.current_task = "Returning Home"
    time.sleep(5)
    mission_state.delivery.mode = DroneMode.IDLE
    mission_state.delivery.current_task = "Mission Complete"

@router.post("/survivor/add_mock")
def add_mock_survivor(lat: float, lon: float):
    # Helper for testing
    s_id = mission_state.add_survivor(lat, lon, 0.95)
    return {"id": s_id}
