#!/bin/bash

# Standing Detection System - Startup Script

echo "=========================================="
echo "  Bus Standing Detection System"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend" || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Download YOLO model if not exists
echo "Checking YOLO model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>/dev/null

echo ""
echo "=========================================="
echo "  Starting Detection System..."
echo "=========================================="
echo ""
echo "Dashboard URL: http://localhost:5000"
echo "Dashboard URL: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the application
python3 app.py
