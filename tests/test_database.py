import core.database as database
from config import Config


def test_analysis_persistence_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(Config, "DATABASE_PATH", str(db_path))
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    result = {
        "source_path": "/tmp/test.h5",
        "source_filename": "test.h5",
        "source_name": "MOSDAC INSAT L1C",
        "source_mode": "HISTORICAL",
        "product_name": "TEST",
        "acquisition_time": "2024-01-01T00:00:00+00:00",
        "processed_at": "2024-01-01T01:00:00+00:00",
        "checksum_sha256": "a" * 64,
        "status": "COMPLETED",
        "detector": "COLD_CLOUD_THRESHOLD_V1",
        "threshold_kelvin": 235.0,
        "min_temperature_kelvin": 200.0,
        "max_temperature_kelvin": 300.0,
        "mean_temperature_kelvin": 270.0,
        "valid_pixel_fraction": 0.9,
        "threat_count": 1,
        "threats": [
            {
                "pixel_count": 100,
                "area_km2": 400.0,
                "mean_temperature_kelvin": 220.0,
                "min_temperature_kelvin": 200.0,
                "latitude": 15.0,
                "longitude": 80.0,
                "mean_radius_km": 50.0,
                "risk_score": 45.0,
                "risk_level": "MEDIUM",
                "trend": "STABLE",
            }
        ],
    }
    first_id, first_created = database.save_analysis(result)
    second_id, second_created = database.save_analysis(result)
    assert first_created is True
    assert second_created is False
    assert first_id == second_id
    assert database.get_latest_analysis()["threats"][0]["risk_score"] == 45.0


def test_failed_checksum_can_be_reprocessed(tmp_path, monkeypatch):
    db_path = tmp_path / "retry.db"
    monkeypatch.setattr(Config, "DATABASE_PATH", str(db_path))
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    checksum = "b" * 64
    database.record_failed_analysis(
        "/tmp/retry.h5", checksum, "LIVE", "temporary failure"
    )
    assert database.analysis_exists(checksum) is None

    result = {
        "source_path": "/tmp/retry.h5",
        "source_filename": "retry.h5",
        "source_name": "MOSDAC INSAT L1C",
        "source_mode": "LIVE",
        "product_name": "TEST",
        "acquisition_time": "2024-01-01T00:00:00+00:00",
        "processed_at": "2024-01-01T01:00:00+00:00",
        "checksum_sha256": checksum,
        "status": "COMPLETED",
        "detector": "COLD_CLOUD_THRESHOLD_V1",
        "threshold_kelvin": 235.0,
        "min_temperature_kelvin": 200.0,
        "max_temperature_kelvin": 300.0,
        "mean_temperature_kelvin": 270.0,
        "valid_pixel_fraction": 0.9,
        "threat_count": 0,
        "threats": [],
    }
    _, created = database.save_analysis(result)
    assert created is True
    assert database.get_latest_analysis()["status"] == "COMPLETED"
