import os

from dotenv import load_dotenv

load_dotenv()


def _project_path(base_dir, value):
    if os.path.isabs(value):
        return os.path.normpath(value)
    return os.path.normpath(os.path.join(base_dir, value))


def _data_path(base_dir, data_dir, value):
    if os.path.isabs(value):
        return os.path.normpath(value)
    if os.path.dirname(value):
        return os.path.normpath(os.path.join(base_dir, value))
    return os.path.normpath(os.path.join(data_dir, value))


class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    CORS_ORIGINS = [
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
        if value.strip()
    ]

    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    STREAMLIT_LOGGER_LEVEL = os.getenv("STREAMLIT_LOGGER_LEVEL", "info")

    DATA_DIR = _project_path(BASE_DIR, os.getenv("DATA_DIR", "data"))
    DATABASE_PATH = _data_path(
        BASE_DIR,
        DATA_DIR,
        os.getenv("DATABASE_PATH", "aetherwatch_telemetry.db"),
    )
    DATABASE_AUTO_INIT = os.getenv("DATABASE_AUTO_INIT", "true").lower() == "true"
    DEMO_DATA_FILE = _data_path(
        BASE_DIR,
        DATA_DIR,
        os.getenv("DEMO_DATA_FILE", "demo_insat.h5"),
    )
    DOWNLOAD_DIR = _project_path(
        BASE_DIR, os.getenv("DOWNLOAD_DIR", "data/downloads")
    )
    STAGING_DIR = _project_path(BASE_DIR, os.getenv("STAGING_DIR", "data/staging"))

    MOSDAC_USERNAME = os.getenv("MOSDAC_USERNAME", "")
    MOSDAC_PASSWORD = os.getenv("MOSDAC_PASSWORD", "")
    MOSDAC_DATASET_ID = os.getenv("MOSDAC_DATASET_ID", "")
    MOSDAC_MDAPI_PATH = _project_path(
        BASE_DIR, os.getenv("MOSDAC_MDAPI_PATH", "vendor/mdapi.py")
    )
    INGEST_INTERVAL_SECONDS = int(os.getenv("INGEST_INTERVAL_SECONDS", "1800"))
    DATA_FRESHNESS_HOURS = int(os.getenv("DATA_FRESHNESS_HOURS", "6"))

    THERMAL_THRESHOLD_KELVIN = float(
        os.getenv("THERMAL_THRESHOLD_KELVIN", "235")
    )
    MIN_REGION_AREA_KM2 = float(os.getenv("MIN_REGION_AREA_KM2", "34800"))
    PIXEL_AREA_KM2 = float(os.getenv("PIXEL_AREA_KM2", "4"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = _project_path(
        BASE_DIR, os.getenv("LOG_FILE", "logs/aetherwatch.log")
    )
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"

    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
    ENABLE_LIVE_DATA_FETCH = (
        os.getenv("ENABLE_LIVE_DATA_FETCH", "false").lower() == "true"
    )
    ENABLE_DATABASE_LOGGING = (
        os.getenv("ENABLE_DATABASE_LOGGING", "true").lower() == "true"
    )

    @classmethod
    def ensure_directories(cls):
        for path in (
            cls.DATA_DIR,
            os.path.dirname(cls.DATABASE_PATH),
            os.path.dirname(cls.LOG_FILE),
            cls.DOWNLOAD_DIR,
            cls.STAGING_DIR,
        ):
            os.makedirs(path, exist_ok=True)
        return True
