import asyncio
import json
import logging
import threading
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Dashboard")

app = FastAPI()

# Store connected clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Broadcast to all connected clients
        # Convert dict to JSON string
        json_msg = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(json_msg)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")

manager = ConnectionManager()

@app.get("/")
async def get():
    # We will serve the HTML file directly for simplicity
    with open("src/web/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for optional pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Integration Logic ---
# Global reference to the asyncio loop to schedule broadcasts from the CV thread
global_loop = None

def start_server(host="0.0.0.0", port=8000):
    import uvicorn
    global global_loop
    # Get the loop that uvicorn will run on (bit tricky in threads, simplified below)
    uvicorn.run(app, host=host, port=port, log_level="error")

def broadcast_update(data):
    """
    Called by the CV system. Schedules a broadcast on the event loop.
    Since CV runs in a separate thread, we need to be thread-safe.
    """
    try:
        # We need to run the async broadcast function in the main event loop
        # This is a robust pattern for bridging Sync -> Async
        asyncio.run(manager.broadcast(data))
    except Exception as e:
        # If the loop is already running or complicates things, we simplify:
        # For a simple local dashboard, creating a new loop or using run_coroutine_threadsafe is best.
        # But allow-multiple-loops can be messy.
        # Alternative: The CV logic runs the server? No, server blocks.
        # Quick fix for threaded async broadcast:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(manager.broadcast(data))
        loop.close()
