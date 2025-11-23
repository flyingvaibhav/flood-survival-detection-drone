import cv2
import numpy as np
import os
import uuid
import time
from ultralytics import YOLO
from app.services.simulation.pathfinding import astar_search
from app.core.config import settings

class SimulationEngine:
    def __init__(self, upload_dir="app/static/simulations"):
        self.upload_dir = upload_dir
        self.model = YOLO(settings.MODEL_PATH) # Reuse the main model
        os.makedirs(upload_dir, exist_ok=True)

    def run_simulation(self, image_path: str, single_drone_mode: bool = False) -> dict:
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(self.upload_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)

        # 1. Load Image
        original_img = cv2.imread(image_path)
        if original_img is None:
            raise ValueError("Could not load image")
        
        h, w = original_img.shape[:2]
        
        # 2. Detect Humans (Ground Truth)
        results = self.model(original_img)
        survivors = []
        for box in results[0].boxes:
            if int(box.cls[0]) == 0: # Person
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                survivors.append({
                    "pos": (cx, cy),
                    "box": (x1, y1, x2, y2),
                    "detected": False,
                    "delivery_dispatched": False,
                    "delivered": False
                })
        
        survivor_count = len(survivors)

        # 3. Setup Drones
        # Scout Drone
        scout_pos = [0, h // 2]
        scout_path = self._generate_lawn_mower_path(w, h, step=100)
        scout_speed = 10 # pixels per frame
        
        # Delivery Drones
        delivery_drones = [] 
        delivery_speed = 15
        
        # Single Drone Mode State
        single_drone_queue = [] # List of survivor indices
        single_drone_capacity = 20
        single_drone_kits = single_drone_capacity # Current kits on board
        active_delivery_sites = [] # List of (x, y) where kits have been delivered/dispatched
        delivery_radius_pixels = 50 # Approx 10m in pixels (tunable)
        
        if single_drone_mode:
            # Initialize one drone at home
            delivery_drones.append({
                "pos": [0, h // 2],
                "path": [],
                "path_idx": 0,
                "target": None,
                "status": "idle", # idle, moving, returning, completed
                "survivor_idx": -1
            })

        # 4. Simulation Loop
        frames = []
        scout_target_idx = 0
        
        # Create a grid for A* (0 = free, 1 = obstacle)
        grid_scale = 10
        grid_w, grid_h = w // grid_scale, h // grid_scale
        grid = np.zeros((grid_h, grid_w), dtype=int)

        max_steps = 5000 # Increased for single drone mode reloading
        step = 0
        
        while step < max_steps:
            frame = original_img.copy()
            
            # --- Scout Logic ---
            if scout_target_idx < len(scout_path):
                target = scout_path[scout_target_idx]
                dist = np.linalg.norm(np.array(target) - np.array(scout_pos))
                
                if dist < scout_speed:
                    scout_pos = list(target)
                    scout_target_idx += 1
                else:
                    direction = (np.array(target) - np.array(scout_pos)) / dist
                    scout_pos[0] += direction[0] * scout_speed
                    scout_pos[1] += direction[1] * scout_speed
            
            # Check detections
            detection_radius = 100
            for idx, s in enumerate(survivors):
                s_dist = np.linalg.norm(np.array(s["pos"]) - np.array(scout_pos))
                if s_dist < detection_radius and not s["detected"]:
                    s["detected"] = True
                    
                    # Check delivery radius constraint
                    too_close = False
                    for site in active_delivery_sites:
                        if np.linalg.norm(np.array(s["pos"]) - np.array(site)) < delivery_radius_pixels:
                            too_close = True
                            break
                    
                    if not too_close:
                        active_delivery_sites.append(s["pos"])
                        
                        if single_drone_mode:
                            # Add to queue
                            single_drone_queue.append(idx)
                        else:
                            # Dispatch Delivery Drone (Multiple Mode)
                            start_node = (0, h // 2) # Home
                            end_node = s["pos"]
                            
                            # Convert to grid coords for A*
                            start_grid = (start_node[0] // grid_scale, start_node[1] // grid_scale)
                            end_grid = (end_node[0] // grid_scale, end_node[1] // grid_scale)
                            
                            path_grid = astar_search(grid, start_grid, end_grid)
                            
                            if path_grid:
                                # Convert back to pixel coords
                                pixel_path = [(p[0] * grid_scale, p[1] * grid_scale) for p in path_grid]
                                delivery_drones.append({
                                    "pos": list(start_node),
                                    "path": pixel_path,
                                    "path_idx": 0,
                                    "target": end_node,
                                    "status": "enroute",
                                    "survivor_idx": idx
                                })

            # --- Delivery Logic ---
            if single_drone_mode:
                drone = delivery_drones[0]
                
                # Decision Making
                if drone["status"] == "idle":
                    scout_finished = scout_target_idx >= len(scout_path)
                    
                    # Check for Reload condition
                    if single_drone_kits <= 0:
                        # Must reload
                        start_node = tuple(map(int, drone["pos"]))
                        end_node = (0, h // 2)
                        start_grid = (start_node[0] // grid_scale, start_node[1] // grid_scale)
                        end_grid = (end_node[0] // grid_scale, end_node[1] // grid_scale)
                        path_grid = astar_search(grid, start_grid, end_grid)
                        if path_grid:
                            drone["path"] = [(p[0] * grid_scale, p[1] * grid_scale) for p in path_grid]
                            drone["path_idx"] = 0
                            drone["status"] = "returning"
                            # Note: We don't set completed here, we are returning to reload
                    
                    elif single_drone_queue:
                        # Have kits, have targets -> Go deliver
                        best_idx = -1
                        min_dist = float('inf')
                        
                        for s_idx in single_drone_queue:
                            d = np.linalg.norm(np.array(survivors[s_idx]["pos"]) - np.array(drone["pos"]))
                            if d < min_dist:
                                min_dist = d
                                best_idx = s_idx
                        
                        if best_idx != -1:
                            single_drone_queue.remove(best_idx)
                            target_survivor = survivors[best_idx]
                            
                            start_node = tuple(map(int, drone["pos"]))
                            end_node = target_survivor["pos"]
                            
                            start_grid = (start_node[0] // grid_scale, start_node[1] // grid_scale)
                            end_grid = (end_node[0] // grid_scale, end_node[1] // grid_scale)
                            
                            path_grid = astar_search(grid, start_grid, end_grid)
                            
                            if path_grid:
                                drone["path"] = [(p[0] * grid_scale, p[1] * grid_scale) for p in path_grid]
                                drone["path_idx"] = 0
                                drone["status"] = "moving"
                                drone["survivor_idx"] = best_idx
                                single_drone_kits -= 1 # Use one kit
                    
                    elif scout_finished and not single_drone_queue:
                        # No more targets, scout done -> Go home and finish
                        start_node = tuple(map(int, drone["pos"]))
                        end_node = (0, h // 2)
                        start_grid = (start_node[0] // grid_scale, start_node[1] // grid_scale)
                        end_grid = (end_node[0] // grid_scale, end_node[1] // grid_scale)
                        path_grid = astar_search(grid, start_grid, end_grid)
                        if path_grid:
                            drone["path"] = [(p[0] * grid_scale, p[1] * grid_scale) for p in path_grid]
                            drone["path_idx"] = 0
                            drone["status"] = "returning"

                # Movement Logic
                if drone["status"] in ["moving", "returning"]:
                    if drone["path_idx"] < len(drone["path"]):
                        target = drone["path"][drone["path_idx"]]
                        d_dist = np.linalg.norm(np.array(target) - np.array(drone["pos"]))
                        
                        if d_dist < delivery_speed:
                            drone["pos"] = list(target)
                            drone["path_idx"] += 1
                        else:
                            direction = (np.array(target) - np.array(drone["pos"])) / d_dist
                            drone["pos"][0] += direction[0] * delivery_speed
                            drone["pos"][1] += direction[1] * delivery_speed
                    else:
                        # Reached destination
                        if drone["status"] == "moving":
                            # Delivered
                            survivors[drone["survivor_idx"]]["delivered"] = True
                            drone["status"] = "idle"
                        elif drone["status"] == "returning":
                            # Reached Home
                            if single_drone_kits <= 0:
                                # Reloading
                                single_drone_kits = single_drone_capacity
                                drone["status"] = "idle" # Ready to go out again
                            else:
                                # Mission Complete
                                drone["status"] = "completed"

            else:
                # Multiple Drone Logic
                for drone in delivery_drones:
                    if drone["path_idx"] < len(drone["path"]):
                        target = drone["path"][drone["path_idx"]]
                        d_dist = np.linalg.norm(np.array(target) - np.array(drone["pos"]))
                        
                        if d_dist < delivery_speed:
                            drone["pos"] = list(target)
                            drone["path_idx"] += 1
                        else:
                            direction = (np.array(target) - np.array(drone["pos"])) / d_dist
                            drone["pos"][0] += direction[0] * delivery_speed
                            drone["pos"][1] += direction[1] * delivery_speed
                    else:
                        # Reached target
                        if drone["status"] == "enroute":
                            survivors[drone["survivor_idx"]]["delivered"] = True
                            drone["status"] = "returning"
                            # Reverse path to go home
                            drone["path"] = drone["path"][::-1]
                            drone["path_idx"] = 0
                        elif drone["status"] == "returning":
                            drone["status"] = "completed"

            # --- Visualization ---
            # Draw Survivors
            for s in survivors:
                color = (0, 0, 255) # Red (Undetected)
                if s["delivered"]:
                    color = (0, 255, 0) # Green (Delivered)
                elif s["detected"]:
                    color = (0, 255, 255) # Yellow (Detected)
                
                cv2.circle(frame, s["pos"], 10, color, -1)
                if s["detected"]:
                    cv2.rectangle(frame, (s["box"][0], s["box"][1]), (s["box"][2], s["box"][3]), color, 2)

            # Draw Scout
            cv2.circle(frame, (int(scout_pos[0]), int(scout_pos[1])), 8, (255, 255, 255), -1)
            cv2.putText(frame, "SCOUT", (int(scout_pos[0])+10, int(scout_pos[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw Scout Path (Lawn Mower) - Optional, maybe too cluttered
            # for i in range(len(scout_path)-1):
            #     cv2.line(frame, scout_path[i], scout_path[i+1], (50, 50, 50), 1)

            # Draw Delivery Drones
            for drone in delivery_drones:
                if drone["status"] != "completed":
                    cv2.circle(frame, (int(drone["pos"][0]), int(drone["pos"][1])), 8, (255, 100, 0), -1)
                    cv2.putText(frame, "DELIVERY", (int(drone["pos"][0])+10, int(drone["pos"][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 1)

            # Overlay Info
            cv2.putText(frame, f"Survivors: {survivor_count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            found_count = sum(1 for s in survivors if s["detected"])
            delivered_count = sum(1 for s in survivors if s["delivered"])
            cv2.putText(frame, f"Detected: {found_count}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.putText(frame, f"Delivered: {delivered_count}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if single_drone_mode:
                 cv2.putText(frame, f"Kits: {single_drone_kits}/{single_drone_capacity}", (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

            frames.append(frame)
            step += 1
            
            # End condition: All delivered and drones returned
            all_delivered = all(s["delivered"] for s in survivors)
            all_returned = all(d["status"] == "completed" for d in delivery_drones)
            
            # In single drone mode, we might be "idle" but waiting for scout to find more, or "returning" to reload
            # So we only break if scout is done AND queue is empty AND drone is completed
            
            if single_drone_mode:
                if scout_target_idx >= len(scout_path) and not single_drone_queue and delivery_drones[0]["status"] == "completed":
                    break
            else:
                if all_delivered and all_returned and scout_target_idx >= len(scout_path):
                    break
            
            # Safety break
            if step >= max_steps:
                break

        if not frames:
            print("Error: No frames generated during simulation.")
            raise ValueError("Simulation failed to generate any frames.")

        # 5. Generate Video
        # Try using avc1 (H.264) which is browser friendly
        video_filename = "simulation.mp4"
        video_path = os.path.join(job_dir, video_filename)
        
        # Try avc1 first
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(video_path, fourcc, 30, (w, h))
        
        if not out.isOpened():
            print("Warning: avc1 codec not available, falling back to mp4v")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(video_path, fourcc, 30, (w, h))

        if not out.isOpened():
             raise RuntimeError("Could not open VideoWriter with avc1 or mp4v")

        for f in frames:
            out.write(f)
        out.release()

        print(f"Video generated at {video_path} with {len(frames)} frames.")

        return {
            "job_id": job_id,
            "survivors_count": survivor_count,
            "video_url": f"/static/simulations/{job_id}/{video_filename}"
        }

    def _generate_lawn_mower_path(self, w, h, step=100):
        path = []
        # Start at 0, mid_y
        path.append((0, h//2))
        
        # Go to top left to start pattern
        path.append((0, 0))
        
        x = 0
        moving_down = True
        
        while x < w:
            if moving_down:
                path.append((x, h))
                if x + step < w:
                    path.append((x + step, h))
            else:
                path.append((x, 0))
                if x + step < w:
                    path.append((x + step, 0))
            
            x += step
            moving_down = not moving_down
            
        # Return to home (0, mid_y)
        path.append((0, h//2))
        return path

simulation_engine = SimulationEngine()
