import os

from config import Config
from logger import get_logger
from .analysis import analyze_file, sha256_file
from .database import (
    analysis_exists,
    get_latest_analysis,
    record_failed_analysis,
    save_analysis,
)

logger = get_logger(__name__)


def process_file(filepath, source_mode="HISTORICAL", force=False):
    checksum = sha256_file(filepath)
    existing_id = analysis_exists(checksum)
    if existing_id and not force:
        return {"analysis_id": existing_id, "created": False, "duplicate": True}
    if existing_id and force:
        return {
            "analysis_id": existing_id,
            "created": False,
            "duplicate": True,
            "message": "Immutable analysis already exists for this checksum",
        }
    try:
        result = analyze_file(filepath, source_mode=source_mode)
        analysis_id, created = save_analysis(result)
        return {
            "analysis_id": analysis_id,
            "created": created,
            "duplicate": not created,
            "threat_count": result["threat_count"],
        }
    except Exception as exc:
        record_failed_analysis(filepath, checksum, source_mode, exc)
        logger.exception("Analysis failed for %s", filepath)
        raise


def ensure_initial_analysis():
    latest = get_latest_analysis(include_threats=False)
    if latest:
        return latest["id"]
    if not os.path.exists(Config.DEMO_DATA_FILE):
        logger.warning("No initial INSAT file exists at %s", Config.DEMO_DATA_FILE)
        return None
    result = process_file(Config.DEMO_DATA_FILE, source_mode="HISTORICAL")
    return result["analysis_id"]
