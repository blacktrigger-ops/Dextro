# config.py

import os
import database

# Bot mode: 'definition', 'tournament', or 'both'
# Can be overridden by environment variable DEFAULT_MODE
BOT_MODE = os.getenv("DEFAULT_MODE", "both")

# Discord bot token: use environment variable if set, else fallback
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "your-token-here")

MODE_FILE = "mode.txt"

def get_mode():
    # Try database first (persistent across deployments)
    try:
        db_mode = database.get_bot_config("bot_mode")
        if db_mode in ("definition", "tournament", "both"):
            return db_mode
    except:
        pass
    
    # Fall back to file (for local development)
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE, 'r') as f:
            mode = f.read().strip()
            if mode in ("definition", "tournament", "both"):
                return mode
    return BOT_MODE

def set_mode(mode):
    if mode in ("definition", "tournament", "both"):
        # Save to database (persistent)
        try:
            database.set_bot_config("bot_mode", mode)
        except:
            pass
        
        # Also save to file (for local development)
        with open(MODE_FILE, 'w') as f:
            f.write(mode) 