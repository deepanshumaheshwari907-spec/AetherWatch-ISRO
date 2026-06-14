import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

from config import Config
from logger import get_logger
from .service import process_file

logger = get_logger(__name__)


def mosdac_is_configured():
    return bool(
        Config.ENABLE_LIVE_DATA_FETCH
        and Config.MOSDAC_USERNAME
        and Config.MOSDAC_PASSWORD
        and Config.MOSDAC_DATASET_ID
        and os.path.isfile(Config.MOSDAC_MDAPI_PATH)
    )


def build_mdapi_config(download_path):
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    return {
        "user_credentials": {
            "username": Config.MOSDAC_USERNAME,
            "password": Config.MOSDAC_PASSWORD,
        },
        "search_parameters": {
            "datasetId": Config.MOSDAC_DATASET_ID,
            "startTime": start_date.isoformat(),
            "endTime": end_date.isoformat(),
            "count": "10",
            "boundingBox": "",
            "gId": "",
        },
        "download_settings": {
            "download_path": download_path,
            "organize_by_date": False,
            "skip_user_prompt": True,
            "generate_error_log": True,
            "error_log_path": Config.STAGING_DIR,
        },
    }


def run_mdapi(command_runner=subprocess.run):
    if not mosdac_is_configured():
        raise RuntimeError(
            "MOSDAC requires enabled live fetch, credentials, dataset ID, "
            "and the official mdapi.py script"
        )
    Config.ensure_directories()
    with tempfile.TemporaryDirectory(
        prefix="mosdac-mdapi-", dir=Config.STAGING_DIR
    ) as workspace:
        script_path = os.path.join(workspace, "mdapi.py")
        config_path = os.path.join(workspace, "config.json")
        shutil.copy2(Config.MOSDAC_MDAPI_PATH, script_path)
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(build_mdapi_config(Config.DOWNLOAD_DIR), handle)
        try:
            os.chmod(config_path, 0o600)
        except OSError:
            pass
        command_runner(
            [sys.executable, script_path],
            cwd=workspace,
            check=True,
            timeout=1500,
        )


def process_downloaded_files():
    results = []
    files = sorted(
        Path(Config.DOWNLOAD_DIR).rglob("*.h5"),
        key=lambda item: item.stat().st_mtime,
    )
    for filepath in files:
        try:
            results.append(process_file(str(filepath), source_mode="LIVE"))
        except Exception as exc:
            logger.error("Rejected downloaded file %s: %s", filepath, exc)
    return results


def run_once(command_runner=subprocess.run):
    if not mosdac_is_configured():
        logger.warning("MOSDAC is not configured; retaining historical mode")
        return {"status": "DISABLED", "processed": []}
    run_mdapi(command_runner=command_runner)
    return {"status": "COMPLETED", "processed": process_downloaded_files()}


def main():
    Config.ensure_directories()
    logger.info("MOSDAC worker started")
    while True:
        try:
            run_once()
        except Exception:
            logger.exception("MOSDAC ingestion cycle failed")
        time.sleep(max(60, Config.INGEST_INTERVAL_SECONDS))


if __name__ == "__main__":
    main()
