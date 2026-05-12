# Bus Standing Detection System - Complete Project Guide

This document contains every technical detail about the project to help you prepare for presentations or Q&A sessions.

---

## 1. Project Overview
**What is it?**  
A real-time AI-powered system designed to monitor passenger flow inside a bus. It uses a camera feed to detect people, determine whether they are standing or sitting, and automatically alert authorities (via Telegram) if the bus is overcrowded.

**Why was it built?**  
To prevent dangerous overcrowding in public transport, automate capacity monitoring, and provide a dashboard for real-time traffic analysis.

---

## 2. Core Technologies & Libraries Used

### Backend (Python)
- **Flask (`flask`)**: The web framework used to serve the backend API and host the frontend dashboard.
- **Flask-SocketIO (`flask_socketio`)**: Enables real-time, two-way communication between the backend and the frontend browser. This is what allows the dashboard numbers to update instantly without refreshing the page.
- **OpenCV (`cv2`)**: Used for capturing video frames from the laptop camera, processing the images, and drawing the bounding boxes/skeletons on the screen.
- **Ultralytics YOLO (`ultralytics`)**: The core AI library. We use the `yolov8n.pt` (YOLOv8 Nano) model because it is incredibly fast and lightweight, allowing real-time object detection and pose estimation on a standard laptop CPU.
- **SQLite (`sqlite3`)**: A lightweight database used to log every time an overcrowding event happens.
- **Requests (`requests`)**: Used to send HTTP POST requests to the Telegram API to trigger the mobile alerts.
- **Subprocess**: Built-in Python library used to automatically start the `ngrok` tunnel in the background.

### Frontend (HTML, CSS, JavaScript)
- **Vanilla JS & HTML/CSS**: No heavy frontend frameworks were used, ensuring fast load times.
- **Chart.js**: A JavaScript charting library used to render the live "Standing vs. Sitting" graph on the dashboard.

### Networking
- **Ngrok**: A secure tunneling tool that takes the local Flask server (running on port 5000) and exposes it to the internet via a public HTTPS link.

---

## 3. How the AI Detection Works (The Logic)

If someone asks: *"How does the AI know if someone is standing or sitting?"*

1. **Frame Capture**: A custom "Fast-Reader" thread continuously pulls the absolute latest frame from the camera buffer. This prevents the video from lagging behind.
2. **YOLO Detection**: The YOLO model scans the frame specifically for `Class 0` (which is the "Person" class). 
3. **Pose Estimation**: The model returns "keypoints" (the human skeleton). 
4. **The Math (Algorithm)**:
   - The code looks specifically at the **Hips** (keypoints 11 & 12) and the **Knees** (keypoints 13 & 14).
   - If the vertical distance (Y-axis difference) between the hip and the knee is greater than 15% of the person's total height, they are classified as **Standing** (because their leg is straight).
   - If the distance is small, it means the hip and knee are horizontally aligned, classifying them as **Sitting**.
5. **Fallback System**: If the hips/knees are blocked by an object, the system falls back to calculating the Aspect Ratio of the bounding box. If the box is much taller than it is wide (Height / Width > 1.4), the person is considered standing.

---

## 4. The Workflow Pipeline

If someone asks: *"Trace the data from the camera to the user's phone."*

1. The **Laptop Camera** captures a frame.
2. **OpenCV** passes the frame to **YOLOv8**.
3. YOLO analyzes the posture and counts the totals.
4. The backend sends the total counts via **WebSocket (SocketIO)** directly to the browser dashboard to update the live chart.
5. If `Standing People > Allowed Limit`, the system checks the "cooldown timer" (to prevent spam).
6. The backend logs the event in the **SQLite Database** (`bus_data.db`).
7. The backend uses the `requests` library to send a message to the **Telegram Bot API**, which immediately pings the admin's phone.

---

## 5. Potential Interview Questions & Answers

**Q: Why use YOLOv8 Nano instead of YOLOv8 Small or Large?**
*Answer*: Real-time video processing requires high FPS (Frames Per Second). Larger models are more accurate but process very slowly on standard laptop CPUs, causing heavy lag. YOLOv8 Nano strikes the perfect balance between accurate human detection and high-speed processing.

**Q: What happens if the internet goes down?**
*Answer*: The core detection system, camera feed, and local dashboard (on localhost) will continue to work perfectly because all processing happens locally on the laptop. However, the Ngrok public URL and Telegram alerts will temporarily fail until the connection is restored.

**Q: How do you prevent the system from sending 100 Telegram alerts a second when the bus is full?**
*Answer*: We implemented a `cooldown_seconds` variable in `config.yaml` (defaulted to 60 seconds). Once an alert is sent, the system records the timestamp and will block any further alerts until the 60 seconds have passed.

**Q: How did you fix the camera delay/lag issue?**
*Answer*: Originally, OpenCV's default buffer would queue up frames faster than the AI could process them, causing the video to fall seconds behind reality. We fixed this by implementing a dedicated background threading class (`CameraReader`). This thread constantly empties the OpenCV buffer so that the AI loop only ever processes the absolute most recent frame, dropping the intermediate ones.
