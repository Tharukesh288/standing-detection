#!/bin/bash
echo "Setting up Standing Detection System..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
echo "Setup complete! Run 'python backend/app.py' to start."
