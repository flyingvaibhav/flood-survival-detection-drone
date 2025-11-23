# Mission Control Dashboard

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have a YOLO model (e.g., `yolo11n.pt`) in the root directory or update `app/core/config.py` with the correct path.

## Running the Dashboard

Run the application:
```bash
python run.py
```

Open your browser to `http://localhost:8000`.

## Features

- **Real-time Video Feed**: Streams from the default camera (simulating the Scout Drone).
- **Survivor Detection**: Uses YOLO to detect people and "geotags" them (simulated coordinates).
- **Mission Planning**: Calculates the shortest path (TSP) for the Delivery Drone to visit all detected survivors.
- **Interactive Map**: Visualizes drone positions and survivor locations.
