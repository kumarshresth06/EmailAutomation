#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Ensure venv exists and is correctly activated
if [ ! -d "venv" ]; then
    /opt/homebrew/bin/python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the app
python3 main.py
