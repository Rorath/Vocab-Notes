#!/bin/bash
# Double-click this file in Finder to launch Vocab-Notes.
# It sets up the environment on first run, then starts the app
# and opens it in your browser.

# Move into the folder this script lives in (works no matter where it's launched from).
cd "$(dirname "$0")" || exit 1

# Create the virtual environment the first time.
if [ ! -d "venv" ]; then
    echo "First-time setup: creating virtual environment..."
    python3 -m venv venv
fi

# Activate it.
source venv/bin/activate

# Make sure Flask is installed (quiet if already present).
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
fi

# Open the browser a moment after the server starts.
( sleep 2 && open "http://127.0.0.1:5001" ) &

echo ""
echo "Starting Vocab-Notes at http://127.0.0.1:5001"
echo "Press Ctrl+C in this window to stop the app."
echo ""

# Start the app.
python app.py
