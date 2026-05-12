# Standing Detection System

A real-time passenger standing detection system using YOLOv8, OpenCV, and a Flask web dashboard. The system utilizes your laptop webcam to continuously monitor a space, count standing vs. sitting people, and sends automatic Telegram alerts when overcrowding occurs.

## Features
- **Real-time YOLOv8 Pose Detection**: Fast inference using the lightweight `yolov8n.pt` model.
- **Web Dashboard**: View the live camera feed, real-time statistics, and a historical chart of crowding over time.
- **Auto-Ngrok Tunneling**: Automatically exposes your dashboard to the internet securely via Ngrok, printing the live URL right in the terminal.
- **Telegram Alerts**: Automatic notifications when the number of standing people exceeds the configured limit.
- **Database Logging**: Saves all overcrowding events to a local SQLite database for historical tracking.

## Project Structure
```text
.
├── backend/
│   ├── app.py             # Main Flask server & WebSocket handler
│   ├── detector.py        # YOLOv8 object/pose detection logic
│   ├── config.yaml        # Configuration (camera, thresholds, Telegram bot info)
│   ├── requirements.txt   # Python dependencies
│   └── bus_data.db        # SQLite database (auto-generated)
├── frontend/
│   ├── index.html         # Web dashboard UI
│   ├── style.css          # Styling (Nord theme)
│   └── script.js          # Client-side logic & Chart.js integration
├── run.sh                 # One-click startup script
└── README.md
```

## Setup & Installation

**Prerequisites:**
- Python 3.8+
- [Ngrok](https://ngrok.com/) (If you want to access the dashboard online)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Tharukesh288/standing-detection.git
   cd standing-detection
   ```

2. **Configure your settings:**
   Edit `backend/config.yaml` to set your Telegram Bot Token, Chat ID, and the maximum allowed standing limit before triggering an alert.

3. **Add your Ngrok Token (Optional):**
   If you want the dashboard to be accessible over the internet:
   ```bash
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```

## How to Run

You can easily start the entire system (backend, frontend, and Ngrok tunnel) using the provided script:

```bash
chmod +x run.sh
./run.sh
```

Or run it manually:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Upon starting, the terminal will print your **Live Online URL**. You can open this link on your phone or any browser to see the dashboard and live camera feed!