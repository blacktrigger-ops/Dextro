# database.py (rebuilt version)
import sqlite3
from contextlib import closing
import os

DB_PATH = os.getenv('DB_PATH', 'botdata.sqlite3')

def get_db():
    dir_name = os.path.dirname(DB_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
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
        # User participation in events/teams
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_event_participation (
                guild_id INTEGER,
                event_id INTEGER,
                user_id INTEGER,
                team_name TEXT,
                PRIMARY KEY (guild_id, event_id, user_id)
            )
        ''')
        # Team stats per event
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
        # Events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                name TEXT,
                max_sections INTEGER
            )
        ''')
        # Sections table
        c.execute('''
            CREATE TABLE IF NOT EXISTS sections (
                section_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                name TEXT,
                max_teams INTEGER
            )
        ''')
        # Teams table
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
        # Team members table
        c.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                team_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (team_id, user_id)
            )
        ''')
        # Channels table
        c.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                guild_id INTEGER,
                channel_type TEXT,
                channel_id INTEGER,
                PRIMARY KEY (guild_id, channel_type)
            )
        ''')
        # User stats table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER,
                guild_id INTEGER,
                events_participated INTEGER DEFAULT 0,
                rank INTEGER DEFAULT 0,
                team_id INTEGER,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        # Leaderboard table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                event_id INTEGER,
                team_id INTEGER,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (event_id, team_id)
            )
        ''')
        # Server stats table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS server_stats (
                guild_id INTEGER,
                stat_name TEXT,
                value INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, stat_name)
            )
        ''')
        conn.commit()

def set_channel(guild_id, channel_type, channel_id):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO channels (guild_id, channel_type, channel_id) VALUES (?, ?, ?)",
            (guild_id, channel_type, channel_id)
        )

def get_channel(guild_id, channel_type):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT channel_id FROM channels WHERE guild_id=? AND channel_type=?",
            (guild_id, channel_type)
        )
        row = cur.fetchone()
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

# --- User Event Participation Functions ---
def log_user_participation(guild_id, event_id, user_id, team_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO user_event_participation (guild_id, event_id, user_id, team_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id, event_id, user_id) DO UPDATE SET team_name = excluded.team_name
        ''', (guild_id, event_id, user_id, team_name))
        conn.commit()

def get_user_event_participation(guild_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT event_id, team_name FROM user_event_participation WHERE guild_id = ? AND user_id = ?
        ''', (guild_id, user_id))
        return c.fetchall()

# --- Team Event Stats Functions ---
def log_team_stats(guild_id, event_id, team_name, score=0, rank=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO team_event_stats (guild_id, event_id, team_name, score, rank)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, event_id, team_name) DO UPDATE SET score = excluded.score, rank = excluded.rank
        ''', (guild_id, event_id, team_name, score, rank))
        conn.commit()

def get_team_stats(guild_id, event_id, team_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT score, rank FROM team_event_stats WHERE guild_id = ? AND event_id = ? AND team_name = ?
        ''', (guild_id, event_id, team_name))
        return c.fetchone()

def get_team_members(guild_id, event_id, team_name):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT user_id FROM user_event_participation WHERE guild_id = ? AND event_id = ? AND team_name = ?
        ''', (guild_id, event_id, team_name))
        return [row[0] for row in c.fetchall()]

def get_user_event_rank(guild_id, event_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT team_name FROM user_event_participation WHERE guild_id = ? AND event_id = ? AND user_id = ?
        ''', (guild_id, event_id, user_id))
        row = c.fetchone()
        if not row:
            return None, None
        team_name = row[0]
        c.execute('''
            SELECT rank FROM team_event_stats WHERE guild_id = ? AND event_id = ? AND team_name = ?
        ''', (guild_id, event_id, team_name))
        rank_row = c.fetchone()
        return team_name, (rank_row[0] if rank_row else None)

def add_event(guild_id, name, max_sections):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO events (guild_id, name, max_sections) VALUES (?, ?, ?)', (guild_id, name, max_sections))
        conn.commit()
        return c.lastrowid

def get_event(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT event_id, name, max_sections FROM events WHERE event_id = ?', (event_id,))
        return c.fetchone()

def list_events(guild_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT event_id, name, max_sections FROM events WHERE guild_id = ?', (guild_id,))
        return c.fetchall()

def remove_event(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
        conn.commit()

def add_section(event_id, name, max_teams):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO sections (event_id, name, max_teams) VALUES (?, ?, ?)', (event_id, name, max_teams))
        conn.commit()
        return c.lastrowid

def get_sections(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT section_id, name, max_teams FROM sections WHERE event_id = ?', (event_id,))
        return c.fetchall()

def add_team(section_id, name, leader_id, max_members, emoji):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('INSERT INTO teams (section_id, name, leader_id, max_members, emoji) VALUES (?, ?, ?, ?, ?)', (section_id, name, leader_id, max_members, emoji))
        conn.commit()
        return c.lastrowid

def get_teams(section_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT team_id, name, leader_id, max_members, emoji FROM teams WHERE section_id = ?', (section_id,))
        return c.fetchall()

def add_team_member(team_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO team_members (team_id, user_id) VALUES (?, ?)', (team_id, user_id))
        conn.commit()

def get_team_members_by_id(team_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT user_id FROM team_members WHERE team_id = ?', (team_id,))
        return [row[0] for row in c.fetchall()]

def remove_team_member(team_id, user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM team_members WHERE team_id = ? AND user_id = ?', (team_id, user_id))
        conn.commit()

def remove_team(team_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM teams WHERE team_id = ?', (team_id,))
        c.execute('DELETE FROM team_members WHERE team_id = ?', (team_id,))
        conn.commit()

def remove_section(section_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM sections WHERE section_id = ?', (section_id,))
        c.execute('DELETE FROM teams WHERE section_id = ?', (section_id,))
        conn.commit()

# User stats helpers
def set_user_stats(user_id, guild_id, events_participated=0, rank=0, team_id=None):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_stats (user_id, guild_id, events_participated, rank, team_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, guild_id, events_participated, rank, team_id)
        )

def fetch_user_stats(user_id, guild_id):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT events_participated, rank, team_id FROM user_stats WHERE user_id=? AND guild_id=?",
            (user_id, guild_id)
        )
        return cur.fetchone()

# Leaderboard helpers
def set_leaderboard_score(event_id, team_id, score):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO leaderboard (event_id, team_id, score) VALUES (?, ?, ?)",
            (event_id, team_id, score)
        )

def get_leaderboard(event_id):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT team_id, score FROM leaderboard WHERE event_id=? ORDER BY score DESC",
            (event_id,)
        )
        return cur.fetchall()

# Server stats helpers
def set_server_stat(guild_id, stat_name, value):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO server_stats (guild_id, stat_name, value) VALUES (?, ?, ?)",
            (guild_id, stat_name, value)
        )

def get_server_stat(guild_id, stat_name):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT value FROM server_stats WHERE guild_id=? AND stat_name=?",
            (guild_id, stat_name)
        )
        row = cur.fetchone()
        return row[0] if row else 0

def get_team_info(team_id):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT name, section_id, leader_id, max_members FROM teams WHERE team_id=?",
            (team_id,)
        )
        row = cur.fetchone()
        if row:
            return {
                'name': row[0],
                'section_id': row[1],
                'leader_id': row[2],
                'max_members': row[3]
            }
        return None 