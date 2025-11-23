from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.services.simulation.engine import simulation_engine
import shutil
import os
import uuid

router = APIRouter()

@router.post("/run")
def run_simulation_endpoint(file: UploadFile = File(...), single_drone_mode: bool = Form(False)):
    # Save temp file
    file_ext = file.filename.split('.')[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{file_ext}"
    temp_path = os.path.join("app/static/simulations", temp_filename)
    
    # Ensure dir exists
    os.makedirs("app/static/simulations", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = simulation_engine.run_simulation(temp_path, single_drone_mode=single_drone_mode)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up input image if needed, or keep it for reference
        # For now we keep it or maybe delete it. Let's delete to save space.
        if os.path.exists(temp_path):
            os.remove(temp_path)
