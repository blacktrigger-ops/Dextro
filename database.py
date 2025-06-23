import sqlite3
from contextlib import closing

DB_PATH = 'botdata.sqlite3'

def get_db():
    return sqlite3.connect(DB_PATH)

def setup_db():
    with get_db() as conn:
        c = conn.cursor()
        # Channel config per guild
        c.execute('''
            CREATE TABLE IF NOT EXISTS channel_config (
                guild_id INTEGER PRIMARY KEY,
                mod_channel INTEGER,
                event_channel INTEGER,
                team_channel INTEGER,
                log_channel INTEGER
            )
        ''')
        # User usage
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_usage (
                guild_id INTEGER,
                user_id INTEGER,
                command TEXT,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, command)
            )
        ''')
        # Server usage
        c.execute('''
            CREATE TABLE IF NOT EXISTS server_usage (
                guild_id INTEGER PRIMARY KEY,
                events_created INTEGER DEFAULT 0,
                teams_created INTEGER DEFAULT 0,
                members_joined INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

def set_channel(guild_id, channel_type, channel_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"INSERT INTO channel_config (guild_id, {channel_type}) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET {channel_type} = excluded.{channel_type}", (guild_id, channel_id))
        conn.commit()

def get_channel(guild_id, channel_type):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT {channel_type} FROM channel_config WHERE guild_id = ?", (guild_id,))
        row = c.fetchone()
        return row[0] if row else None

def log_user_command(guild_id, user_id, command):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO user_usage (guild_id, user_id, command, count) VALUES (?, ?, ?, 1)
            ON CONFLICT(guild_id, user_id, command) DO UPDATE SET count = count + 1
        ''', (guild_id, user_id, command))
        conn.commit()

def increment_server_stat(guild_id, stat):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"INSERT INTO server_usage (guild_id, {stat}) VALUES (?, 1) ON CONFLICT(guild_id) DO UPDATE SET {stat} = {stat} + 1", (guild_id,))
        conn.commit()

def get_user_stats(guild_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT command, count FROM user_usage WHERE guild_id = ? AND user_id = ? ORDER BY count DESC''', (guild_id, user_id))
        return c.fetchall()

def get_server_stats(guild_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT events_created, teams_created, members_joined FROM server_usage WHERE guild_id = ?''', (guild_id,))
        return c.fetchone()

# Call this on bot startup
setup_db() 