import cv2
import threading
import time
import requests
from flask import Flask, render_template, Response, jsonify, send_from_directory
from flask_socketio import SocketIO
import os
from detector import StandingDetector
import yaml
import sqlite3
import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bus_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS crowd_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            standing_count INTEGER,
            is_manual BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_crowd_event(standing, is_manual):
    try:
        conn = sqlite3.connect('bus_data.db')
        c = conn.cursor()
        c.execute('INSERT INTO crowd_events (standing_count, is_manual) VALUES (?, ?)',
                  (standing, is_manual))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

# Path to the frontend folder
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(frontend_dir, path)

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

if config['camera'].get('use_stream', False) and config['camera'].get('stream_url'):
    camera_source = config['camera']['stream_url']
else:
    camera_source = config['camera']['device_id']

cap = cv2.VideoCapture(camera_source)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['camera'].get('width', 640))
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera'].get('height', 480))

detector = StandingDetector('config.yaml')

current_standing = 0
current_sitting = 0
last_frame = None
last_alert_time = 0
lock = threading.Lock()
cap_lock = threading.Lock()

def send_telegram_alert(standing_count, is_manual=False):
    # Log the event to our database before sending the telegram!
    log_crowd_event(standing_count, is_manual)
    
    bot_token = config['alerts']['telegram_bot_token']
    chat_id = config['alerts']['telegram_chat_id']
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE" or not chat_id or chat_id == "YOUR_CHAT_ID_HERE":
        print("Telegram configured incorrectly or missing credentials.")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    if is_manual:
        # If there are > 5 standing, specifically mention overcrowding
        if standing_count > 5:
            text = f"🚨 *[MANUAL TRIGGER]* 🚨\nOvercrowding alert manually activated!\nThere are currently *{standing_count}* people standing."
        else:
            text = f"🚨 *[MANUAL TRIGGER]* 🚨\nAlert was manually activated from the dashboard.\nThere are currently *{standing_count}* people standing."
    else:
        text = f"🚨 *ALERT* 🚨\nOvercrowding detected! There are currently *{standing_count}* people standing."

    payload = {
        "chat_id": chat_id,
        "text": text
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram alert sent! Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def process_camera():
    global current_standing, current_sitting, last_frame, last_alert_time
    limit = config['alerts']['max_standing_limit']
    cooldown = config['alerts']['cooldown_seconds']
    telegram_enabled = config['alerts']['telegram_enabled']
    
    while True:
        try:
            with cap_lock:
                success, frame = cap.read()
            if not success:
                time.sleep(0.1)
                continue
                
            processed_frame, standing, sitting = detector.process_frame(frame)
            
            with lock:
                current_standing = standing
                current_sitting = sitting
                last_frame = processed_frame.copy()
                
            overcrowded = standing > limit
            
            # Check alerts
            current_time = time.time()
            if overcrowded and telegram_enabled:
                if current_time - last_alert_time > cooldown:
                    # Trigger alert in a thread so main loop isn't blocked
                    threading.Thread(target=send_telegram_alert, args=(standing,), daemon=True).start()
                    last_alert_time = current_time
                    
            socketio.emit('count_update', {
                'standing': standing,
                'sitting': sitting,
                'overcrowded': overcrowded
            })
        except Exception as e:
            print(f"Error processing frame: {e}")
        time.sleep(0.05)

@app.route('/api/count')
def get_count():
    return jsonify({
        'standing': current_standing,
        'sitting': current_sitting,
        'overcrowded': current_standing > config['alerts']['max_standing_limit']
    })

@app.route('/api/switch_camera', methods=['POST'])
def switch_camera():
    global cap, camera_source, config
    
    new_use_stream = not config['camera'].get('use_stream', False)
    config['camera']['use_stream'] = new_use_stream
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
        
    with cap_lock:
        cap.release()
        if new_use_stream and config['camera'].get('stream_url'):
            camera_source = config['camera']['stream_url']
        else:
            camera_source = config['camera']['device_id']
            
        cap = cv2.VideoCapture(camera_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['camera'].get('width', 640))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera'].get('height', 480))
        
    return jsonify({'use_stream': new_use_stream, 'source': camera_source})

@socketio.on('manual_trigger')
def handle_manual_trigger():
    with lock:
        standing = current_standing
    threading.Thread(target=send_telegram_alert, args=(standing, True), daemon=True).start()
    print("Manual trigger activated.")

@app.route('/api/stats')
def get_stats():
    try:
        conn = sqlite3.connect('bus_data.db')
        c = conn.cursor()
        
        # 1. Total crowding events today (using SQLite local time matching for simplicity)
        c.execute("SELECT COUNT(*) FROM crowd_events WHERE date(timestamp) = date('now')")
        today_events = c.fetchone()[0]
        
        # 2. Peak standing
        c.execute("SELECT MAX(standing_count) FROM crowd_events")
        peak_standing = c.fetchone()[0] or 0
        
        # 3. Last crowded time
        c.execute("SELECT timestamp FROM crowd_events ORDER BY id DESC LIMIT 1")
        last_eventrow = c.fetchone()
        
        # Format the timestamp nicely if it exists
        if last_eventrow:
            # SQLite CURRENT_TIMESTAMP is UTC format like '2023-11-20 14:05:00'
            last_dt = datetime.datetime.strptime(last_eventrow[0], '%Y-%m-%d %H:%M:%S')
            last_time = last_dt.strftime('%I:%M %p (%b %d)')
        else:
            last_time = "Never"
            
        conn.close()
        return jsonify({
            'today_events': today_events,
            'peak_standing': peak_standing,
            'last_event': last_time
        })
    except Exception as e:
        print(e)
        return jsonify({'today_events': 0, 'peak_standing': 0, 'last_event': 'Error'}), 500

def generate_frames():
    global last_frame
    while True:
        with lock:
            if last_frame is None:
                continue
            frame_to_encode = last_frame.copy()
            
        ret, buffer = cv2.imencode('.jpg', frame_to_encode)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    camera_thread = threading.Thread(target=process_camera, daemon=True)
    camera_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
