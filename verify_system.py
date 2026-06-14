#!/usr/bin/env python3
"""End-to-end AetherWatch verification with Windows-safe ASCII output."""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def report(ok, message):
    print(f"[{'PASS' if ok else 'FAIL'}] {message}")
    return ok


def main():
    checks = []
    checks.append(
        report(
            sys.version_info >= (3, 11),
            f"Python 3.11+ (found {sys.version_info.major}.{sys.version_info.minor})",
        )
    )

    required = (
        "fastapi",
        "folium",
        "h5py",
        "numpy",
        "pandas",
        "plotly",
        "requests",
        "skimage",
        "streamlit",
    )
    for module in required:
        try:
            __import__(module)
            checks.append(report(True, f"Dependency import: {module}"))
        except ImportError:
            checks.append(report(False, f"Dependency import: {module}"))

    demo_file = ROOT / "data" / "demo_insat.h5"
    checks.append(report(demo_file.exists(), "Historical INSAT fixture exists"))

    temp_db = Path(tempfile.gettempdir()) / "aetherwatch_verify.db"
    for suffix in ("", "-wal", "-shm"):
        try:
            Path(str(temp_db) + suffix).unlink()
        except FileNotFoundError:
            pass

    try:
        from config import Config
        import core.database as database
        from core.analysis import analyze_file

        Config.DATABASE_PATH = str(temp_db)
        database.DB_PATH = str(temp_db)
        result = analyze_file(str(demo_file), source_mode="HISTORICAL")
        analysis_id, created = database.save_analysis(result)
        latest = database.get_latest_analysis()
        checks.append(report(created and analysis_id > 0, "Analysis persisted"))
        checks.append(
            report(
                latest
                and latest["detector"] == "COLD_CLOUD_THRESHOLD_V1"
                and latest["threat_count"] == len(latest["threats"]),
                "Canonical analysis contract",
            )
        )
    except Exception as exc:
        checks.append(report(False, f"End-to-end analysis: {exc}"))

    try:
        from backend.main import app

        routes = {route.path for route in app.routes}
        expected = {
            "/health",
            "/api/v1/analyses/latest",
            "/api/v1/analyses/latest/preview",
            "/api/v1/threats",
            "/api/v1/admin/reprocess-historical",
        }
        checks.append(report(expected.issubset(routes), "Production API routes"))
    except Exception as exc:
        checks.append(report(False, f"API import: {exc}"))

    print()
    passed = sum(checks)
    print(f"Verification: {passed}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
