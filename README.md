# Standing Person Detection & Tracking System

A real-time AI system designed to detect, track, and count standing people from a camera feed.

## Architecture
1. **Detection**: YOLOv8-Pose (Nano) for lightweight, real-time person detection and keypoint extraction.
2. **Tracking**: DeepSORT for robust temporal tracking and unique ID assignment, preventing double-counting.
3. **Posture Inference**: Instead of naive bounding box checks, this system uses spatial keypoint geometry (Head-Hip-Ankle alignment) to logically verify a standing posture.
4. **Data Output**: Real-time OpenCV visualization and structured JSON logging for backend consumption.

## Setup
```bash
pip install -r requirements.txt
```

## Running the System
To run using the default webcam:
```bash
python run_system.py
```

To run on a video file:
```bash
python run_system.py --source path/to/video.mp4
```

To specify a custom output path for the data JSON:
```bash
python run_system.py --output data/my_session.json
```

## Modular Structure
- `src/detector.py`: YOLOv8 wrapper.
- `src/tracker.py`: DeepSORT integration.
- `src/logic.py`: Heuristic logic for posture analysis.
- `src/utils/logger.py`: JSON-based structured logging for scalability.
- `data/results.json`: Output data for historical analysis.
