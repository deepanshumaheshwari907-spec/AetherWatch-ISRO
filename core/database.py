import sqlite3
import os
from datetime import datetime

# Database file ko data folder me save karenge
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'aetherwatch_telemetry.db'))

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table schema for tracking threat vectors
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            center_lat REAL,
            center_lon REAL,
            min_tb REAL,
            mean_radius_km REAL,
            risk_score REAL,
            risk_level TEXT,
            trend TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_threat_to_db(threat_data):
    """Inserts a single threat vector into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO threat_logs 
        (timestamp, center_lat, center_lon, min_tb, mean_radius_km, risk_score, risk_level, trend)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        now, 
        threat_data['center_lat'], 
        threat_data['center_lon'],
        threat_data['min_tb'], 
        threat_data['mean_radius_km'],
        threat_data['risk_score'], 
        threat_data['risk_level'], 
        threat_data['trend']
    ))
    conn.commit()
    conn.close()

def fetch_telemetry_history():
    """Fetches all past records for plotting graphs."""
    conn = sqlite3.connect(DB_PATH)
    import pandas as pd
    df = pd.read_sql_query("SELECT * FROM threat_logs", conn)
    conn.close()
    return df