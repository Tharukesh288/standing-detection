import threading
import sys
import os
import uvicorn
from src.main import StandingDetectionSystem
from src.web_server import app, broadcast_update

def run_vision_system():
    """
    Runs the CV logic in a background thread.
    """
    print("Initializing Vision System...")
    # Initialize the system with a callback that sends data to our web server
    system = StandingDetectionSystem(
        source=0, 
        on_update_callback=broadcast_update
    )
    system.run()

if __name__ == "__main__":
    # 1. Start Vision Thread
    vision_thread = threading.Thread(target=run_vision_system, daemon=True)
    vision_thread.start()

    # 2. Start Web Server (Main Thread)
    # Host 0.0.0.0 is critical for allowing access from other devices (mobile)
    print("Starting Web Dashboard on port 8000...")
    print("Access via: http://localhost:8000 (or your LAN IP)")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit(0)
