import os
import time
from datetime import datetime

import schedule

from core.data_fetcher import fetch_latest_satellite_data

# Yeh log file track karegi ki worker kab kab chala tha
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'worker_logs.txt'))

def job():
    """The automated task that runs silently in the background."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⚙️ [{now}] CRON JOB TRIGGERED: Starting Background Ingestion...")
    
    try:
        # Humara purana function call kar rahe hain
        path, status = fetch_latest_satellite_data()
        
        log_msg = f"[{now}] SUCCESS - Matrix pulled. Status: {status}\n"
        print(f"✅ Worker Task Complete: Data stored at {path}")
        
    except Exception as e:
        log_msg = f"[{now}] ERROR - Uplink failed: {str(e)}\n"
        print(f"❌ Worker Task Failed: {e}")
        
    # Writing to log file for audit purposes (Enterprise feature)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg)

# 🕒 Scheduling the job (Real-world me ISRO data har 15-30 min me update hota hai)
# Presentation testing ke liye hum isko har 1 minute (60 seconds) pe set kar rahe hain.
schedule.every(1).minutes.do(job)

if __name__ == "__main__":
    print("🚀 AetherWatch Background Telemetry Worker Initialized...")
    print("Listening for scheduled intervals (Press Ctrl+C to stop).")
    
    # Run the job immediately once on startup
    job()
    
    # Keep the worker alive in an infinite loop
    while True:
        schedule.run_pending()
        time.sleep(1)