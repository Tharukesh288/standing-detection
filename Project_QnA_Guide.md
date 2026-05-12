# Bus Standing Detection System - Comprehensive Architecture & Implementation Guide

This document is the absolute source of truth for the project. It contains every single technical detail, file structure breakdown, algorithm logic, and implementation choice made during the development of this system.

---

## 1. System Architecture & High-Level Overview
**Objective**: To automatically monitor a bus environment, differentiate between standing and sitting passengers, visualize this data in real-time on a web dashboard, log events to a database, and send instant Telegram alerts when overcrowding thresholds are breached.

**Architecture Paradigm**: Client-Server Model with Asynchronous Processing.
- **Frontend**: Vanilla HTML/CSS/JS (Lightweight, no compile step).
- **Backend API**: Flask (Serves the dashboard and REST API).
- **Real-time Pipeline**: Flask-SocketIO (WebSockets) for pushing continuous data without client polling.
- **AI Processing**: OpenCV (Hardware interfacing) + Ultralytics YOLOv8 (Inference).
- **External Services**: Ngrok (Tunneling for WAN access), Telegram API (Notifications).

---

## 2. File Structure & Component Breakdown

### `/backend/app.py` (The Core Controller)
This is the heart of the system. It is heavily multi-threaded to prevent blocking operations.
*   **Database Initialization (`init_db`)**: On startup, it connects to SQLite (`bus_data.db`) and creates the `crowd_events` table if it doesn't exist. The table schema contains: `id` (Primary Key), `timestamp` (DATETIME), `standing_count` (INTEGER), and `is_manual` (BOOLEAN).
*   **Flask & SocketIO Setup**: Initializes a Flask app that serves the static files from the `../frontend` folder. `SocketIO` is wrapped around the Flask app with `cors_allowed_origins="*"` to allow cross-origin WebSocket connections.
*   **The `CameraReader` Class (Lag Mitigation)**: 
    *   *The Problem*: Standard `cv2.VideoCapture.read()` processes frames sequentially. Because YOLO takes ~50ms+ to process a frame, camera frames build up in the buffer, causing the video feed to lag seconds behind reality.
    *   *The Solution*: `CameraReader` spins up a dedicated `daemon=True` thread. This thread runs an infinite `while` loop that *only* reads from the camera and stores the result in `self.latest_frame`, overwriting the old frame. It uses a `threading.Lock()` to prevent memory corruption when the main thread reads the frame. This guarantees 0 seconds of delay.
*   **The `process_camera` Loop**: This thread pulls `cam_reader.read()`, passes it to `detector.process_frame()`, and updates the global `current_standing` and `current_sitting` variables. It then emits a `count_update` event over WebSocket to all connected browser clients.
*   **Telegram Alerting (`send_telegram_alert`)**: If `standing > limit`, it triggers an alert. To prevent spamming the API, it implements a cooldown (checked via `time.time() - last_alert_time`). The alert function is spawned in a *new thread* (`threading.Thread(target=send_telegram_alert)`) so the HTTP request doesn't freeze the camera feed.
*   **Auto-Ngrok Script**: On startup, `app.py` spawns a thread that uses Python's `subprocess` library to silently run `ngrok http 5000`, waits 3 seconds, polls the local Ngrok API (`http://127.0.0.1:4040/api/tunnels`), extracts the public HTTPS URL, and prints it to the terminal.

### `/backend/detector.py` (The AI Engine)
*   **Initialization**: Loads `config.yaml` to set thresholds and instantiates the YOLO model using `self.model = YOLO('yolov8n.pt')`.
*   **Inference**: Calls `self.model(frame, stream=True, classes=[0], conf=self.conf_thresh)`. `classes=[0]` forces the model to ignore cars, animals, etc., and *only* detect humans (Class 0 in the COCO dataset).
*   **The Posture Algorithm**:
    1.  The model outputs bounding boxes (`xyxy`) and Keypoints (the 17 points of the human skeleton).
    2.  The code specifically extracts: Left Hip (11), Right Hip (12), Left Knee (13), and Right Knee (14).
    3.  It checks the confidence score of these joints (`> 0.5`).
    4.  **Math**: It calculates the vertical distance between the hip and the knee (`knee_y - hip_y`).
    5.  **Logic**: If a person is sitting, their femur is horizontal, meaning their knee and hip have almost the same Y-coordinate. If they are standing, their leg is straight, meaning the knee is physically far below the hip.
    6.  **Threshold**: If `vertical_dist > (0.15 * bounding_box_height)`, the person is classified as "Standing".
    7.  **Fallback Mechanism**: If the camera can only see the upper body (keypoints missing), the system falls back to a mathematical Aspect Ratio check. If `(Height / Width) > 1.4`, the person is standing.
*   **Annotation**: Uses `cv2.rectangle`, `cv2.putText`, and `cv2.circle` to draw colored boxes (Nord Green for Standing, Nord Red for Sitting) and plot the skeleton joints directly onto the numpy array frame.

### `/backend/config.yaml` (The Settings File)
Separating configuration from code prevents hardcoding. It contains:
*   `alerts.max_standing_limit`: The integer threshold that triggers an overcrowded state (default: 5).
*   `alerts.cooldown_seconds`: Prevents API spam by enforcing a wait time between messages.
*   `camera.device_id`: The hardware index for the webcam (usually `0`).
*   `camera.use_stream`: Boolean flag allowing the system to easily swap to an external IP camera (like an ESP32-CAM) in the future.
*   `detection.model_path`: Set to `yolov8n.pt`. Nano is chosen specifically because its parameter size allows 15-30 FPS on standard CPUs.

### `/frontend/script.js` (The Client Controller)
*   **Dynamic URL Parsing**: Uses `window.location.origin` to automatically figure out if the user is accessing via localhost or Ngrok, ensuring WebSocket connections never fail due to CORS.
*   **WebSocket Receiver**: Listens for the `count_update` event. When received, it instantly updates the DOM elements.
*   **Chart.js Integration**: Maintains a rolling historical array of `MAX_DATA_POINTS = 30`. Every time a WebSocket packet arrives, it pushes the new standing/sitting integers into the Chart datasets, shifting out the oldest data point to create a continuous scrolling effect. Animations are disabled (`duration: 0`) in the chart config to prevent rendering lag.
*   **Database Polling**: Runs a `setInterval` every 5 seconds to hit the `/api/stats` REST endpoint, updating the "Total Events Today" and "Peak Standing" UI components.

---

## 3. Exhaustive Dependency Details
- **Python Version**: 3.8+
- `ultralytics`: The official YOLO library package. Automatically downloads the PyTorch backend.
- `opencv-python`: Provides the `cv2` bindings for camera capture and image matrix manipulation.
- `flask` & `Flask-SocketIO`: Handles WSGI routing and WebSocket protocol upgrades.
- `PyYAML`: Parses the `config.yaml` file into Python dictionaries.
- `requests`: Standard library for making external HTTP calls (Telegram API & Ngrok API).

---

## 4. Why This Architecture was Chosen (Design Decisions)
1. **Why SQLite?** We do not need a massive distributed database like PostgreSQL. SQLite writes directly to a `.db` file on the hard drive, requires zero configuration, and easily handles the write speed of a single application.
2. **Why Flask-SocketIO over REST Polling?** If the frontend requested data every second via AJAX, it would create massive HTTP overhead. WebSockets keep a single persistent TCP connection open, allowing the server to push numbers with near-zero latency.
3. **Why YOLOv8 Nano?** Accuracy vs. Speed tradeoff. `yolov8s` or `yolov8m` provides slightly better bounding boxes, but drops the frame rate significantly on non-GPU machines. Nano provides the mathematically optimal balance for live CCTV processing.
4. **Why serve Frontend through Flask?** Originally, the HTML was opened as a raw file. Serving it through Flask means the entire application (HTML, APIs, Video Feed, WebSockets) runs on a single port (5000). This is what allows Ngrok to expose the *entire* application securely over a single URL without cross-origin resource sharing (CORS) errors.
