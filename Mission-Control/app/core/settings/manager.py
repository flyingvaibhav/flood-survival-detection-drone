import json
import os
from app.core.settings.models import SystemSettings

SETTINGS_FILE = "user_settings.json"

class SettingsManager:
    def __init__(self):
        self.settings = SystemSettings()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.settings = SystemSettings(**data)
            except Exception as e:
                print(f"Error loading settings: {e}")
                # Fallback to defaults
                self.settings = SystemSettings()
        else:
            self.save_settings()

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                f.write(self.settings.model_dump_json(indent=4))
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_settings(self) -> SystemSettings:
        return self.settings

    def update_settings(self, new_settings: dict):
        # Deep update logic could go here, but for now we'll just re-parse
        # This assumes the dict is a full or partial representation that Pydantic can handle
        # For partial updates, we might need more logic, but let's assume full section updates for simplicity
        # or we can use model_copy with update.
        
        # A simple way is to update the current model with the new dict
        current_dump = self.settings.model_dump()
        
        # Recursive update helper
        def update_dict(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = update_dict(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        updated_dump = update_dict(current_dump, new_settings)
        self.settings = SystemSettings(**updated_dump)
        self.save_settings()
        return self.settings

settings_manager = SettingsManager()
