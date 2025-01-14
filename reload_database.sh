#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Stop any existing bot process
pkill -f "python3 bot.py"

# Recreate the database
psql -c "DROP DATABASE IF EXISTS hersey_bot;"
createdb hersey_bot

# Start the bot
python3 bot.py &

echo "Bot restarted with fresh database"
