import os

class Settings:
    PROJECT_NAME: str = "Disaster Management Mission Control"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Drone Configs
    SCOUT_DRONE_ID: str = "SCOUT-01"
    DELIVERY_DRONE_ID: str = "DELIVERY-01"
    
    # Map Config (Center of the 30 hectare area)
    # Example coords
    DEFAULT_LAT: float = 28.6139
    DEFAULT_LON: float = 77.2090
    
    # Model
    MODEL_PATH: str = "../best.pt"  # Assumes model is in root or accessible

settings = Settings()
