"""
AetherWatch — Background Automated Worker
Runs on a schedule to silently fetch and process latest satellite data.
Usage: python -m core.automated_worker
"""

import os
import time
from datetime import datetime
import schedule
from core.data_fetcher import fetch_latest_satellite_data

LOG_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "worker_logs.txt")
)


def _write_log(msg: str):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
    print(msg)


def job():
    """Scheduled task — fetches latest satellite matrix silently."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write_log(f"\n[{now}] CRON JOB TRIGGERED: Starting background ingestion...")
    try:
        path, status = fetch_latest_satellite_data()
        _write_log(f"[{now}] SUCCESS — Status: {status} | Path: {path}")
    except Exception as e:
        _write_log(f"[{now}] ERROR — Uplink failed: {str(e)}")


if __name__ == "__main__":
    _write_log("AetherWatch background worker started. Scheduled: every 30 minutes.")
    schedule.every(30).minutes.do(job)
    job()
    while True:
        schedule.run_pending()
        time.sleep(60)