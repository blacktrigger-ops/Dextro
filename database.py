# database.py (rebuilt version)
import mysql.connector
import sqlite3
import os
from contextlib import contextmanager

# Railway MySQL configuration (for deployment)
RAILWAY_MYSQL_CONFIG = {
    'host': 'mysql.railway.internal',
    'port': 3306,
    'database': 'railway',
    'user': 'root',
    'password': 'UpXiofqjknhWmszqIqTxBcMlhLpZGGId',
}

# Local MySQL configuration (for development)
LOCAL_MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'botdb'),
}

# Use Railway MySQL if available, otherwise fall back to local MySQL or SQLite
def get_mysql_config():
    # Try Railway MySQL first
    try:
        test_conn = mysql.connector.connect(**RAILWAY_MYSQL_CONFIG)
        test_conn.close()
        return RAILWAY_MYSQL_CONFIG
    except:
        # Try local MySQL
        try:
            test_conn = mysql.connector.connect(**LOCAL_MYSQL_CONFIG)
            test_conn.close()
            return LOCAL_MYSQL_CONFIG
        except:
            return None

MYSQL_CONFIG = get_mysql_config()

# Flag to track if we're using MySQL or SQLite
USE_MYSQL = MYSQL_CONFIG is not None

@contextmanager
def get_db():
    global USE_MYSQL
    if USE_MYSQL and MYSQL_CONFIG:
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            try:
                yield conn
            finally:
                conn.close()
        except Exception as e:
            print(f"MySQL connection failed: {e}")
            print("Falling back to SQLite...")
            USE_MYSQL = False
            # Fall through to SQLite
            pass
    
    if not USE_MYSQL:
        # Use SQLite fallback
        conn = sqlite3.connect('botdata.sqlite3')
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def setup_db():
    global USE_MYSQL
    try:
        with get_db() as conn:
            c = conn.cursor()
            if USE_MYSQL:
                # MySQL table creation
                c.execute('''
                    CREATE TABLE IF NOT EXISTS channel_config (
                        guild_id BIGINT PRIMARY KEY,
                        mod_channel BIGINT,
                        event_channel BIGINT,
                        team_channel BIGINT,
                        log_channel BIGINT
                    )
                ''')
                # Bot configuration table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS bot_config (
                        config_key VARCHAR(64) PRIMARY KEY,
                        config_value TEXT
                    )
                ''')
                # User usage
                c.execute('''
                    CREATE TABLE IF NOT EXISTS user_usage (
                        guild_id BIGINT,
                        user_id BIGINT,
                        command VARCHAR(64),
                        count INT DEFAULT 0,
                        PRIMARY KEY (guild_id, user_id, command)
                    )
                ''')
                # Server usage
                c.execute('''
                    CREATE TABLE IF NOT EXISTS server_usage (
                        guild_id BIGINT PRIMARY KEY,
                        events_created INT DEFAULT 0,
                        teams_created INT DEFAULT 0,
                        members_joined INT DEFAULT 0
                    )
                ''')
                # User participation in events/teams
                c.execute('''
                    CREATE TABLE IF NOT EXISTS user_event_participation (
                        guild_id BIGINT,
                        event_id BIGINT,
                        user_id BIGINT,
                        team_name VARCHAR(255),
                        PRIMARY KEY (guild_id, event_id, user_id)
                    )
                ''')
                # Team stats per event
                c.execute('''
                    CREATE TABLE IF NOT EXISTS team_event_stats (
                        guild_id BIGINT,
                        event_id BIGINT,
                        team_name VARCHAR(255),
                        score INT DEFAULT 0,
                        `rank` INT DEFAULT NULL,
                        PRIMARY KEY (guild_id, event_id, team_name)
                    )
                ''')
                # Events table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        guild_id BIGINT,
                        name VARCHAR(255),
                        max_sections INT
                    )
                ''')
                # Sections table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS sections (
                        section_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        event_id BIGINT,
                        name VARCHAR(255),
                        max_teams INT
                    )
                ''')
                # Teams table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS teams (
                        team_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        section_id BIGINT,
                        name VARCHAR(255),
                        leader_id BIGINT,
                        max_members INT,
                        emoji VARCHAR(32)
                    )
                ''')
                # Team members table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS team_members (
                        team_id BIGINT,
                        user_id BIGINT,
                        PRIMARY KEY (team_id, user_id)
                    )
                ''')
                # Channels table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        guild_id BIGINT,
                        channel_type VARCHAR(32),
                        channel_id BIGINT,
                        PRIMARY KEY (guild_id, channel_type)
                    )
                ''')
                # User stats table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id BIGINT,
                        guild_id BIGINT,
                        events_participated INT DEFAULT 0,
                        `rank` INT DEFAULT 0,
                        team_id BIGINT,
                        PRIMARY KEY (user_id, guild_id)
                    )
                ''')
                # Leaderboard table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        event_id BIGINT,
                        team_id BIGINT,
                        score INT DEFAULT 0,
                        PRIMARY KEY (event_id, team_id)
                    )
                ''')
                # Server stats table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS server_stats (
                        guild_id BIGINT,
                        stat_name VARCHAR(64),
                        value INT DEFAULT 0,
                        PRIMARY KEY (guild_id, stat_name)
                    )
                ''')
            else:
                # SQLite table creation
                c.execute('''
                    CREATE TABLE IF NOT EXISTS channel_config (
                        guild_id INTEGER PRIMARY KEY,
                        mod_channel INTEGER,
                        event_channel INTEGER,
                        team_channel INTEGER,
                        log_channel INTEGER
                    )
                ''')
                # Bot configuration table
                c.execute('''
                    CREATE TABLE IF NOT EXISTS bot_config (
                        config_key TEXT PRIMARY KEY,
                        config_value TEXT
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS user_usage (
                        guild_id INTEGER,
                        user_id INTEGER,
                        command TEXT,
                        count INTEGER DEFAULT 0,
                        PRIMARY KEY (guild_id, user_id, command)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS server_usage (
                        guild_id INTEGER PRIMARY KEY,
                        events_created INTEGER DEFAULT 0,
                        teams_created INTEGER DEFAULT 0,
                        members_joined INTEGER DEFAULT 0
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS user_event_participation (
                        guild_id INTEGER,
                        event_id INTEGER,
                        user_id INTEGER,
                        team_name TEXT,
                        PRIMARY KEY (guild_id, event_id, user_id)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS team_event_stats (
                        guild_id INTEGER,
                        event_id INTEGER,
                        team_name TEXT,
                        score INTEGER DEFAULT 0,
                        rank INTEGER DEFAULT NULL,
                        PRIMARY KEY (guild_id, event_id, team_name)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER,
                        name TEXT,
                        max_sections INTEGER
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS sections (
                        section_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id INTEGER,
                        name TEXT,
                        max_teams INTEGER
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS teams (
                        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        section_id INTEGER,
                        name TEXT,
                        leader_id INTEGER,
                        max_members INTEGER,
                        emoji TEXT
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS team_members (
                        team_id INTEGER,
                        user_id INTEGER,
                        PRIMARY KEY (team_id, user_id)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        guild_id INTEGER,
                        channel_type TEXT,
                        channel_id INTEGER,
                        PRIMARY KEY (guild_id, channel_type)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS user_stats (
                        user_id INTEGER,
                        guild_id INTEGER,
                        events_participated INTEGER DEFAULT 0,
                        rank INTEGER DEFAULT 0,
                        team_id INTEGER,
                        PRIMARY KEY (user_id, guild_id)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        event_id INTEGER,
                        team_id INTEGER,
                        score INTEGER DEFAULT 0,
                        PRIMARY KEY (event_id, team_id)
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS server_stats (
                        guild_id INTEGER,
                        stat_name TEXT,
                        value INTEGER DEFAULT 0,
                        PRIMARY KEY (guild_id, stat_name)
                    )
                ''')
            conn.commit()
    except Exception as e:
        print(f"Database setup failed: {e}")
        USE_MYSQL = False
        # Try again with SQLite
        setup_db()

def set_channel(guild_id, channel_type, channel_id):
    with get_db() as conn:
        c = conn.cursor()
        if channel_id is None:
            # Delete the channel configuration
            if USE_MYSQL:
                c.execute(
                    "DELETE FROM channels WHERE guild_id=%s AND channel_type=%s",
                    (guild_id, channel_type)
                )
            else:
                c.execute(
                    "DELETE FROM channels WHERE guild_id=? AND channel_type=?",
                    (guild_id, channel_type)
                )
        else:
            # Set the channel configuration
            if USE_MYSQL:
                c.execute(
                    "REPLACE INTO channels (guild_id, channel_type, channel_id) VALUES (%s, %s, %s)",
                    (guild_id, channel_type, channel_id)
                )
            else:
                c.execute(
                    "INSERT OR REPLACE INTO channels (guild_id, channel_type, channel_id) VALUES (?, ?, ?)",
                    (guild_id, channel_type, channel_id)
                )
        conn.commit()

def get_channel(guild_id, channel_type):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute(
                "SELECT channel_id FROM channels WHERE guild_id=%s AND channel_type=%s",
                (guild_id, channel_type)
            )
        else:
            c.execute(
                "SELECT channel_id FROM channels WHERE guild_id=? AND channel_type=?",
                (guild_id, channel_type)
            )
        row = c.fetchone()
        return row[0] if row else None

def log_user_command(guild_id, user_id, command):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute('''
                INSERT INTO user_usage (guild_id, user_id, command, count) VALUES (%s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE count = count + 1
            ''', (guild_id, user_id, command))
        else:
            c.execute('''
                INSERT INTO user_usage (guild_id, user_id, command, count) VALUES (?, ?, ?, 1)
                ON CONFLICT(guild_id, user_id, command) DO UPDATE SET count = count + 1
            ''', (guild_id, user_id, command))
        conn.commit()

def increment_server_stat(guild_id, stat):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute(f"INSERT INTO server_usage (guild_id, {stat}) VALUES (%s, 1) ON DUPLICATE KEY UPDATE {stat} = {stat} + 1", (guild_id,))
        else:
            c.execute(f"INSERT INTO server_usage (guild_id, {stat}) VALUES (?, 1) ON CONFLICT(guild_id) DO UPDATE SET {stat} = {stat} + 1", (guild_id,))
        conn.commit()

def get_user_stats(guild_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute('''SELECT command, count FROM user_usage WHERE guild_id = %s AND user_id = %s ORDER BY count DESC''', (guild_id, user_id))
        else:
            c.execute('''SELECT command, count FROM user_usage WHERE guild_id = ? AND user_id = ? ORDER BY count DESC''', (guild_id, user_id))
        return c.fetchall()

def get_server_stats(guild_id):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute('''SELECT events_created, teams_created, members_joined FROM server_usage WHERE guild_id = %s''', (guild_id,))
        else:
            c.execute('''SELECT events_created, teams_created, members_joined FROM server_usage WHERE guild_id = ?''', (guild_id,))
        return c.fetchone()

# Call this on bot startup
setup_db()

# --- User Event Participation Functions ---
def log_user_participation(guild_id, event_id, user_id, team_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO user_event_participation (guild_id, event_id, user_id, team_name)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE team_name = VALUES(team_name)
        ''', (guild_id, event_id, user_id, team_name))
        conn.commit()

def get_user_event_participation(guild_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT event_id, team_name FROM user_event_participation WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        return c.fetchall()

# --- Team Event Stats Functions ---
def log_team_stats(guild_id, event_id, team_name, score=0, rank=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO team_event_stats (guild_id, event_id, team_name, score, `rank`)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE score = VALUES(score), `rank` = VALUES(`rank`)
        ''', (guild_id, event_id, team_name, score, rank))
        conn.commit()

def get_team_stats(guild_id, event_id, team_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT score, `rank` FROM team_event_stats WHERE guild_id = %s AND event_id = %s AND team_name = %s
        ''', (guild_id, event_id, team_name))
        return c.fetchone()

def get_team_members(guild_id, event_id, team_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT user_id FROM user_event_participation WHERE guild_id = %s AND event_id = %s AND team_name = %s
        ''', (guild_id, event_id, team_name))
        return [row[0] for row in c.fetchall()]

def get_user_event_rank(guild_id, event_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT team_name FROM user_event_participation WHERE guild_id = %s AND event_id = %s AND user_id = %s
        ''', (guild_id, event_id, user_id))
        row = c.fetchone()
        if not row:
            return None, None
        team_name = row[0]
        c.execute('''
            SELECT `rank` FROM team_event_stats WHERE guild_id = %s AND event_id = %s AND team_name = %s
        ''', (guild_id, event_id, team_name))
        rank_row = c.fetchone()
        return team_name, (rank_row[0] if rank_row else None)

def add_event(guild_id, name, max_sections):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO events (guild_id, name, max_sections) VALUES (%s, %s, %s)''', (guild_id, name, max_sections))
        conn.commit()
        return c.lastrowid

def get_event(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT event_id, guild_id, name, max_sections FROM events WHERE event_id = %s''', (event_id,))
        return c.fetchone()

def list_events(guild_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT event_id, name, max_sections FROM events WHERE guild_id = %s''', (guild_id,))
        return c.fetchall()

def remove_event(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''DELETE FROM events WHERE event_id = %s''', (event_id,))
        conn.commit()

def add_section(event_id, name, max_teams):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO sections (event_id, name, max_teams) VALUES (%s, %s, %s)''', (event_id, name, max_teams))
        conn.commit()
        return c.lastrowid

def get_sections(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT section_id, name, max_teams FROM sections WHERE event_id = %s''', (event_id,))
        return c.fetchall()

def add_team(section_id, name, leader_id, max_members, emoji):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO teams (section_id, name, leader_id, max_members, emoji) VALUES (%s, %s, %s, %s, %s)''', (section_id, name, leader_id, max_members, emoji))
        conn.commit()
        return c.lastrowid

def get_teams(section_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT team_id, name, leader_id, max_members, emoji FROM teams WHERE section_id = %s''', (section_id,))
        return c.fetchall()

def add_team_member(team_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''INSERT IGNORE INTO team_members (team_id, user_id) VALUES (%s, %s)''', (team_id, user_id))
        conn.commit()

def get_team_members_by_id(team_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT user_id FROM team_members WHERE team_id = %s''', (team_id,))
        return [row[0] for row in c.fetchall()]

def remove_team_member(team_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''DELETE FROM team_members WHERE team_id = %s AND user_id = %s''', (team_id, user_id))
        conn.commit()

def remove_team(team_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''DELETE FROM teams WHERE team_id = %s''', (team_id,))
        conn.commit()

def remove_section(section_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''DELETE FROM sections WHERE section_id = %s''', (section_id,))
        conn.commit()

# User stats helpers
def set_user_stats(user_id, guild_id, events_participated=0, rank=0, team_id=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO user_stats (user_id, guild_id, events_participated, `rank`, team_id)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE events_participated=VALUES(events_participated), `rank`=VALUES(`rank`), team_id=VALUES(team_id)
        ''', (user_id, guild_id, events_participated, rank, team_id))
        conn.commit()

def fetch_user_stats(user_id, guild_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT events_participated, `rank`, team_id FROM user_stats WHERE user_id = %s AND guild_id = %s''', (user_id, guild_id))
        return c.fetchone()

# Leaderboard helpers
def set_leaderboard_score(event_id, team_id, score):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO leaderboard (event_id, team_id, score) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE score = VALUES(score)
        ''', (event_id, team_id, score))
        conn.commit()

def get_leaderboard(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT team_id, score FROM leaderboard WHERE event_id = %s ORDER BY score DESC''', (event_id,))
        return c.fetchall()

# Server stats helpers
def set_server_stat(guild_id, stat_name, value):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO server_stats (guild_id, stat_name, value) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        ''', (guild_id, stat_name, value))
        conn.commit()

def get_server_stat(guild_id, stat_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT value FROM server_stats WHERE guild_id = %s AND stat_name = %s''', (guild_id, stat_name))
        row = c.fetchone()
        return row[0] if row else 0

def get_team_info(team_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT name, leader_id, max_members, emoji FROM teams WHERE team_id = %s''', (team_id,))
        row = c.fetchone()
        if not row:
            return None
        return {
            'name': row[0],
            'leader': row[1],
            'max_members': row[2],
            'emoji': row[3],
        }

# Bot configuration functions
def get_bot_config(key, default=None):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute("SELECT config_value FROM bot_config WHERE config_key = %s", (key,))
        else:
            c.execute("SELECT config_value FROM bot_config WHERE config_key = ?", (key,))
        row = c.fetchone()
        return row[0] if row else default

def set_bot_config(key, value):
    with get_db() as conn:
        c = conn.cursor()
        if USE_MYSQL:
            c.execute(
                "REPLACE INTO bot_config (config_key, config_value) VALUES (%s, %s)",
                (key, value)
            )
        else:
            c.execute(
                "INSERT OR REPLACE INTO bot_config (config_key, config_value) VALUES (?, ?)",
                (key, value)
            )
        conn.commit() 