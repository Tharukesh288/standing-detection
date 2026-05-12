#!/bin/bash
echo "Starting Passenger Flow Backend..."

# Navigate to the directory where this script is located
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found! Please run scripts/setup.sh first to install everything."
    exit 1
fi

source venv/bin/activate

echo "Opening User Dashboard..."
if command -v xdg-open &> /dev/null; then
    # Runs the browser in the background
    xdg-open "$(pwd)/frontend/index.html" &
else
    # Fallback to python webbrowser if xdg-open isn't available
    python3 -c "import webbrowser, os; webbrowser.open('file://' + os.path.realpath('frontend/index.html'))" &
fi

cd backend
python3 app.py