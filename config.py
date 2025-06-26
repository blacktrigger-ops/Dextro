# config.py

import os

# Bot mode: 'definition', 'tournament', or 'both'
BOT_MODE = "both"

# Discord bot token: use environment variable if set, else fallback
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "your-token-here")

MODE_FILE = "mode.txt"

def get_mode():
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, 'r') as f:
            mode = f.read().strip()
            if mode in ("definition", "tournament", "both"):
                return mode
    return BOT_MODE

def set_mode(mode):
    if mode in ("definition", "tournament", "both"):
        with open(MODE_FILE, 'w') as f:
            f.write(mode) 