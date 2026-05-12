# Standing Detection System for Bus

This system detects standing vs sitting people using a camera and YOLO object detection, displaying the real-time count on a web dashboard.

## Setup Instructions

1. Run the setup script:
   ```bash
   bash scripts/setup.sh
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

4. Open the frontend:
   Simply open `frontend/index.html` in your browser.
c