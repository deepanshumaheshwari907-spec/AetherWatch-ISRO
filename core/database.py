"""
AetherWatch — Telemetry Database
Handles all SQLite read/write operations for threat vector logging.
"""

import sqlite3
import os
import uuid
from datetime import datetime

import pandas as pd

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "aetherwatch_telemetry.db")
)


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Main threat log table — one row per detected cluster per scan
    cur.execute("""
        CREATE TABLE IF NOT EXISTS threat_logs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    TEXT    NOT NULL,
            timestamp     TEXT    NOT NULL,
            data_source   TEXT    DEFAULT 'UNKNOWN',
            center_lat    REAL,
            center_lon    REAL,
            min_tb        REAL,
            mean_tb       REAL,
            mean_radius_km REAL,
            risk_score    REAL,
            risk_level    TEXT,
            trend         TEXT,
            pixel_count   INTEGER
        )
    """)

    # Scan-level summary — one row per full analysis run
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scan_sessions (
            session_id      TEXT PRIMARY KEY,
            timestamp       TEXT NOT NULL,
            data_source     TEXT,
            total_clusters  INTEGER,
            peak_risk_score REAL,
            peak_risk_level TEXT,
            threshold_k     INTEGER
        )
    """)

    conn.commit()
    conn.close()


def new_session_id() -> str:
    """Generate a unique session ID for each analysis run."""
    return uuid.uuid4().hex[:12].upper()


def log_scan_session(session_id: str, data_source: str, total_clusters: int,
                     peak_risk_score: float, peak_risk_level: str, threshold_k: int):
    """Log a summary record for an entire scan session."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO scan_sessions
        (session_id, timestamp, data_source, total_clusters,
         peak_risk_score, peak_risk_level, threshold_k)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data_source,
        total_clusters,
        round(float(peak_risk_score), 2),
        peak_risk_level,
        threshold_k,
    ))
    conn.commit()
    conn.close()


def log_threat_to_db(threat_data: dict, session_id: str = "MANUAL",
                     data_source: str = "UNKNOWN"):
    """Insert a single threat cluster record."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO threat_logs
        (session_id, timestamp, data_source, center_lat, center_lon,
         min_tb, mean_tb, mean_radius_km, risk_score, risk_level, trend, pixel_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data_source,
        threat_data.get("center_lat"),
        threat_data.get("center_lon"),
        threat_data.get("min_tb"),
        threat_data.get("mean_tb"),
        threat_data.get("mean_radius_km"),
        threat_data.get("risk_score"),
        threat_data.get("risk_level"),
        threat_data.get("trend"),
        int(threat_data.get("pixel_count", 0)),
    ))
    conn.commit()
    conn.close()


def fetch_telemetry_history(limit: int = 200) -> pd.DataFrame:
    """Return the most recent threat log entries as a DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(
        f"SELECT * FROM threat_logs ORDER BY id DESC LIMIT {limit}", conn
    )
    conn.close()
    return df


def fetch_scan_sessions(limit: int = 50) -> pd.DataFrame:
    """Return recent scan session summaries."""
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(
        f"SELECT * FROM scan_sessions ORDER BY timestamp DESC LIMIT {limit}", conn
    )
    conn.close()
    return df


def fetch_risk_trend() -> pd.DataFrame:
    """
    Return peak risk score per session for the trend chart.
    Grouped by session so the chart shows scan-level history.
    """
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query("""
        SELECT timestamp, peak_risk_score AS risk_score, peak_risk_level AS risk_level
        FROM   scan_sessions
        ORDER  BY timestamp ASC
    """, conn)
    conn.close()
    return df