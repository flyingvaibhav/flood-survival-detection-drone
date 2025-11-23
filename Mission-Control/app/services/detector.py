import cv2
import numpy as np
from ultralytics import YOLO
from app.core.config import settings
from app.core.drone_state import mission_state
import threading
import time

class VideoStreamer:
    def __init__(self, source=0):
        self.model = YOLO(settings.MODEL_PATH)
        self.source = source
        self.cap = None
        self.lock = threading.Lock()
        self.running = False
        self.current_frame = None
        self.latest_raw_frame = None
        self.thread = None
        self.read_thread = None
        
    def start(self):
        if self.running:
            return
        self.running = True
        self.cap = cv2.VideoCapture(self.source)
        
        # Thread to read frames as fast as possible
        self.read_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.read_thread.start()
        
        # Thread to process frames (inference)
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.read_thread:
            self.read_thread.join()
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def _reader_loop(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.1)
                continue
                
            success, frame = self.cap.read()
            if not success:
                # If video ends or camera disconnects, try to reset
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                time.sleep(0.1)
                continue
            
            with self.lock:
                self.latest_raw_frame = frame
            
            # Small sleep to prevent CPU hogging by reader
            time.sleep(0.005)

    def _process_loop(self):
        while self.running:
            frame = None
            with self.lock:
                if self.latest_raw_frame is not None:
                    frame = self.latest_raw_frame.copy()
            
            if frame is None:
                time.sleep(0.01)
                continue

            # Run inference
            results = self.model(frame, verbose=False)
            annotated_frame = results[0].plot()

            # Process detections for mission state
            for box in results[0].boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                if cls == 0 and conf > 0.5: # Person class
                    # Simulate GPS based on drone position (mock)
                    lat = mission_state.scout.lat + (np.random.random() - 0.5) * 0.0001
                    lon = mission_state.scout.lon + (np.random.random() - 0.5) * 0.0001
                    
                    # Add to state
                    mission_state.add_survivor(lat, lon, conf)
            
            with self.lock:
                ret, buffer = cv2.imencode('.jpg', annotated_frame)
                if ret:
                    self.current_frame = buffer.tobytes()
            
            # No sleep here - run as fast as inference allows

    def generate_frames(self):
        while True:
            if not self.running:
                # Yield a placeholder frame to prevent browser hanging
                blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank_frame, "SYSTEM IDLE - WAITING FOR SCAN", (80, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
                ret, buffer = cv2.imencode('.jpg', blank_frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(1.0) # Low FPS for idle
                continue
                
            with self.lock:
                if self.current_frame is None:
                    time.sleep(0.01)
                    continue
                frame_bytes = self.current_frame
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Limit streaming FPS to ~20 to save bandwidth
            time.sleep(0.05)

# Global streamer instance
# In production, source might be an RTSP stream URL from the drone
streamer = VideoStreamer(source=0) # Default to webcam for demo
