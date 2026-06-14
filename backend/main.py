import hmac
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from core.database import (
    database_status,
    get_latest_analysis,
    init_db,
    list_threats,
)
from core.insat_reader import load_insat_scene
from core.service import ensure_initial_analysis, process_file
from logger import get_logger
from backend.rate_limit import RateLimitMiddleware

logger = get_logger(__name__)
VERSION = "2.0.0"


def _parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _freshness(latest):
    if not latest:
        return {"state": "UNAVAILABLE", "age_hours": None, "is_fresh": False}
    source_time = _parse_time(latest.get("acquisition_time")) or _parse_time(
        latest["processed_at"]
    )
    if source_time.tzinfo is None:
        source_time = source_time.replace(tzinfo=timezone.utc)
    age_hours = max(
        0.0,
        (datetime.now(timezone.utc) - source_time).total_seconds() / 3600,
    )
    is_fresh = (
        latest["source_mode"] == "LIVE"
        and age_hours <= Config.DATA_FRESHNESS_HOURS
    )
    return {
        "state": "FRESH" if is_fresh else "HISTORICAL_OR_STALE",
        "age_hours": round(age_hours, 2),
        "is_fresh": is_fresh,
    }


def require_admin(x_admin_token: str = Header(default="")):
    if not Config.ADMIN_TOKEN:
        raise HTTPException(
            status_code=503, detail="Administrative operations are not configured"
        )
    if not hmac.compare_digest(x_admin_token, Config.ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid administrative token")
    return True


@asynccontextmanager
async def lifespan(app):
    Config.ensure_directories()
    init_db()
    try:
        ensure_initial_analysis()
    except Exception:
        logger.exception("Initial historical analysis failed")
    yield


app = FastAPI(
    title="AetherWatch API",
    description="INSAT cold-cloud candidate analysis API",
    version=VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)
app.add_middleware(RateLimitMiddleware)


@app.get("/", tags=["System"])
def root():
    return {
        "name": "AetherWatch API",
        "version": VERSION,
        "docs": "/api/docs",
        "methodology": "cold-cloud threshold candidate detection",
    }


@app.get("/health", tags=["System"])
def health_check():
    db = database_status()
    latest = get_latest_analysis(include_threats=False) if db["ok"] else None
    freshness = _freshness(latest)
    healthy = db["ok"] and latest is not None
    operational_state = "HEALTHY" if healthy and freshness["is_fresh"] else "DEGRADED"
    return {
        "status": operational_state,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "ok": db["ok"],
            "schema_version": db.get("schema_version"),
        },
        "latest_analysis_id": latest["id"] if latest else None,
        "source_mode": latest["source_mode"] if latest else None,
        "freshness": freshness,
        "live_ingestion_enabled": Config.ENABLE_LIVE_DATA_FETCH,
        "mosdac_configured": bool(
            Config.MOSDAC_USERNAME
            and Config.MOSDAC_PASSWORD
            and Config.MOSDAC_DATASET_ID
        ),
    }


@app.get("/api/v1/analyses/latest", tags=["Analyses"])
def latest_analysis():
    result = get_latest_analysis(include_threats=True)
    if not result:
        raise HTTPException(status_code=404, detail="No completed analysis is available")
    result["freshness"] = _freshness(result)
    result.pop("source_path", None)
    return result


@app.get("/api/v1/analyses/latest/preview", tags=["Analyses"])
def latest_preview(max_size: int = Query(default=180, ge=32, le=300)):
    latest = get_latest_analysis(include_threats=False)
    if not latest:
        raise HTTPException(status_code=404, detail="No completed analysis is available")
    scene = load_insat_scene(latest["source_path"])
    thermal = scene["thermal"]
    latitude = scene["latitude"]
    longitude = scene["longitude"]
    step = max(1, int(np.ceil(max(thermal.shape) / max_size)))
    return {
        "analysis_id": latest["id"],
        "thermal": thermal[::step, ::step].tolist(),
        "latitude": latitude[::step, ::step].tolist(),
        "longitude": longitude[::step, ::step].tolist(),
        "unit": "kelvin",
    }


@app.get("/api/v1/threats", tags=["Threats"])
def threats(
    analysis_id: int | None = None,
    limit: int = Query(default=500, ge=1, le=1000),
):
    return {
        "analysis_id": analysis_id,
        "items": list_threats(analysis_id=analysis_id, limit=limit),
    }


@app.post(
    "/api/v1/admin/reprocess-historical",
    tags=["Administration"],
    dependencies=[Depends(require_admin)],
)
def reprocess_historical():
    if not os.path.exists(Config.DEMO_DATA_FILE):
        raise HTTPException(status_code=404, detail="Historical INSAT file is missing")
    return process_file(Config.DEMO_DATA_FILE, source_mode="HISTORICAL")


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.exception("Unhandled API exception")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
