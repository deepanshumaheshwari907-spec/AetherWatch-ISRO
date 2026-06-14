from fastapi.testclient import TestClient

import backend.main as main
from config import Config


SAMPLE_ANALYSIS = {
    "id": 7,
    "source_path": "/private/file.h5",
    "source_filename": "file.h5",
    "source_name": "MOSDAC INSAT L1C",
    "source_mode": "HISTORICAL",
    "product_name": "TEST",
    "acquisition_time": "2024-01-01T00:00:00+00:00",
    "processed_at": "2024-01-01T01:00:00+00:00",
    "detector": "COLD_CLOUD_THRESHOLD_V1",
    "threshold_kelvin": 235.0,
    "threat_count": 0,
    "threats": [],
}


def test_public_contract_and_private_path(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: True)
    monkeypatch.setattr(main, "ensure_initial_analysis", lambda: 7)
    monkeypatch.setattr(main, "get_latest_analysis", lambda include_threats=True: dict(SAMPLE_ANALYSIS))
    monkeypatch.setattr(main, "database_status", lambda: {"ok": True})
    with TestClient(main.app) as client:
        response = client.get("/api/v1/analyses/latest")
        assert response.status_code == 200
        assert "source_path" not in response.json()
        assert response.json()["source_mode"] == "HISTORICAL"


def test_admin_endpoint_requires_token(monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_TOKEN", "secret-token")
    monkeypatch.setattr(main, "init_db", lambda: True)
    monkeypatch.setattr(main, "ensure_initial_analysis", lambda: 7)
    with TestClient(main.app) as client:
        assert client.post("/api/v1/admin/reprocess-historical").status_code == 401
