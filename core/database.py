import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import Config
from logger import get_logger

logger = get_logger(__name__)
DB_PATH = Config.DATABASE_PATH
SCHEMA_VERSION = 2


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    Config.ensure_directories()
    with connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                source_filename TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_mode TEXT NOT NULL,
                product_name TEXT,
                acquisition_time TEXT,
                processed_at TEXT NOT NULL,
                checksum_sha256 TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                detector TEXT NOT NULL,
                threshold_kelvin REAL NOT NULL,
                min_temperature_kelvin REAL,
                max_temperature_kelvin REAL,
                mean_temperature_kelvin REAL,
                valid_pixel_fraction REAL,
                threat_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                pixel_count INTEGER NOT NULL,
                area_km2 REAL NOT NULL,
                mean_temperature_kelvin REAL NOT NULL,
                min_temperature_kelvin REAL NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                mean_radius_km REAL NOT NULL,
                risk_score REAL NOT NULL CHECK(risk_score BETWEEN 0 AND 100),
                risk_level TEXT NOT NULL,
                trend TEXT NOT NULL,
                FOREIGN KEY(analysis_id) REFERENCES analysis_runs(id)
                    ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_threats_analysis ON threats(analysis_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_processed ON analysis_runs(processed_at)"
        )
        current = conn.execute(
            "SELECT MAX(version) AS version FROM schema_version"
        ).fetchone()["version"]
        if current is None or current < SCHEMA_VERSION:
            conn.execute(
                "INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
            )
    logger.info("Database initialized at %s", DB_PATH)
    return True


def database_status():
    try:
        init_db()
        with connection() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"ok": True, "path": DB_PATH, "schema_version": SCHEMA_VERSION}
    except Exception as exc:
        logger.exception("Database health check failed")
        return {"ok": False, "path": DB_PATH, "error": str(exc)}


def analysis_exists(checksum_sha256):
    init_db()
    with connection() as conn:
        row = conn.execute(
            """
            SELECT id FROM analysis_runs
            WHERE checksum_sha256 = ? AND status = 'COMPLETED'
            """,
            (checksum_sha256,),
        ).fetchone()
    return row["id"] if row else None


def save_analysis(result):
    """Persist one completed analysis and its candidates atomically."""
    init_db()
    with connection() as conn:
        existing = conn.execute(
            "SELECT id, status FROM analysis_runs WHERE checksum_sha256 = ?",
            (result["checksum_sha256"],),
        ).fetchone()
        if existing and existing["status"] == "COMPLETED":
            return existing["id"], False
        if existing:
            conn.execute("DELETE FROM analysis_runs WHERE id = ?", (existing["id"],))

        cursor = conn.execute(
            """
            INSERT INTO analysis_runs (
                source_path, source_filename, source_name, source_mode,
                product_name, acquisition_time, processed_at, checksum_sha256,
                status, detector, threshold_kelvin, min_temperature_kelvin,
                max_temperature_kelvin, mean_temperature_kelvin,
                valid_pixel_fraction, threat_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["source_path"],
                result["source_filename"],
                result["source_name"],
                result["source_mode"],
                result.get("product_name"),
                result.get("acquisition_time"),
                result["processed_at"],
                result["checksum_sha256"],
                result["status"],
                result["detector"],
                result["threshold_kelvin"],
                result["min_temperature_kelvin"],
                result["max_temperature_kelvin"],
                result["mean_temperature_kelvin"],
                result["valid_pixel_fraction"],
                result["threat_count"],
            ),
        )
        analysis_id = cursor.lastrowid
        conn.executemany(
            """
            INSERT INTO threats (
                analysis_id, pixel_count, area_km2, mean_temperature_kelvin,
                min_temperature_kelvin, latitude, longitude, mean_radius_km,
                risk_score, risk_level, trend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    analysis_id,
                    threat["pixel_count"],
                    threat["area_km2"],
                    threat["mean_temperature_kelvin"],
                    threat["min_temperature_kelvin"],
                    threat["latitude"],
                    threat["longitude"],
                    threat["mean_radius_km"],
                    threat["risk_score"],
                    threat["risk_level"],
                    threat["trend"],
                )
                for threat in result["threats"]
            ],
        )
    logger.info(
        "Saved analysis %s with %s candidates", analysis_id, result["threat_count"]
    )
    return analysis_id, True


def record_failed_analysis(filepath, checksum, source_mode, error_message):
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_runs (
                source_path, source_filename, source_name, source_mode,
                processed_at, checksum_sha256, status, detector,
                threshold_kelvin, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, 'FAILED', ?, ?, ?)
            ON CONFLICT(checksum_sha256) DO UPDATE SET
                processed_at = excluded.processed_at,
                status = 'FAILED',
                error_message = excluded.error_message
            """,
            (
                os.path.abspath(filepath),
                os.path.basename(filepath),
                "MOSDAC INSAT L1C",
                source_mode,
                now,
                checksum,
                "COLD_CLOUD_THRESHOLD_V1",
                Config.THERMAL_THRESHOLD_KELVIN,
                str(error_message)[:2000],
            ),
        )


def _threats_for_analysis(conn, analysis_id):
    rows = conn.execute(
        """
        SELECT id, pixel_count, area_km2, mean_temperature_kelvin,
               min_temperature_kelvin, latitude, longitude, mean_radius_km,
               risk_score, risk_level, trend
        FROM threats
        WHERE analysis_id = ?
        ORDER BY risk_score DESC, id ASC
        """,
        (analysis_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_latest_analysis(include_threats=True):
    init_db()
    with connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM analysis_runs
            WHERE status = 'COMPLETED'
            ORDER BY COALESCE(acquisition_time, processed_at) DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        if include_threats:
            result["threats"] = _threats_for_analysis(conn, row["id"])
    return result


def list_threats(analysis_id=None, limit=500):
    init_db()
    limit = max(1, min(int(limit), 1000))
    with connection() as conn:
        if analysis_id is None:
            latest = conn.execute(
                """
                SELECT id FROM analysis_runs
                WHERE status = 'COMPLETED'
                ORDER BY COALESCE(acquisition_time, processed_at) DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
            if not latest:
                return []
            analysis_id = latest["id"]
        rows = conn.execute(
            """
            SELECT id, analysis_id, pixel_count, area_km2,
                   mean_temperature_kelvin, min_temperature_kelvin,
                   latitude, longitude, mean_radius_km, risk_score,
                   risk_level, trend
            FROM threats WHERE analysis_id = ?
            ORDER BY risk_score DESC, id ASC LIMIT ?
            """,
            (analysis_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_telemetry_history(limit=1000):
    import pandas as pd

    init_db()
    with connection() as conn:
        return pd.read_sql_query(
            """
            SELECT ar.processed_at AS timestamp, t.*
            FROM threats t
            JOIN analysis_runs ar ON ar.id = t.analysis_id
            ORDER BY ar.processed_at DESC, t.risk_score DESC
            LIMIT ?
            """,
            conn,
            params=(max(1, min(int(limit), 10000)),),
        )


def log_threat_to_db(threat_data):
    """Legacy writes are intentionally disabled in the public data flow."""
    logger.warning("Ignored legacy standalone threat write: %s", json.dumps(threat_data))
    return False
