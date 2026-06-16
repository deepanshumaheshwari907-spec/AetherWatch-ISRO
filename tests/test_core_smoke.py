import os
from unittest.mock import patch

import h5py
import numpy as np
import pytest

from core.insat_reader import load_tb_lat_lon

from core.ai_engine import _ScaledRegion
from core.data_fetcher import fetch_latest_satellite_data
from core.feature_extractor import build_threat_explanation, describe_geographic_context
from core.risk_engine import compute_risk_score, haversine_km, risk_level_from_score


def test_compute_risk_score_returns_expected_range():
    score = compute_risk_score(200.0, 500.0)

    assert 0 <= score <= 100
    assert score > 40


def test_haversine_distance_matches_expected_order():
    distance = haversine_km(0.0, 0.0, 0.0, 1.0)

    assert 100 < distance < 120


def test_risk_level_mapping_is_consistent():
    assert risk_level_from_score(90) == "Extreme"
    assert risk_level_from_score(70) == "High"
    assert risk_level_from_score(40) == "Medium"
    assert risk_level_from_score(10) == "Low"


def test_fetch_latest_satellite_data_falls_back_to_demo_file():
    with patch("core.data_fetcher.urllib.request.urlretrieve", side_effect=RuntimeError("offline")):
        path, status = fetch_latest_satellite_data()

    assert status == "FALLBACK_DEMO"
    assert os.path.exists(path)


def test_load_tb_lat_lon_returns_float32_grids_for_memory_efficiency(tmp_path):
    fake_path = tmp_path / "sample.h5"
    fake_path.write_bytes(b"stub")

    class FakeHandle:
        def __init__(self):
            self._raw = np.array([[0, 1], [2, 3]], dtype=np.uint16)
            self._lut = np.array([190.0, 191.0, 192.0, 193.0], dtype=np.float64)
            self._x = np.array([0.0, 1.0], dtype=np.float64)
            self._y = np.array([0.0, 1.0], dtype=np.float64)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def __getitem__(self, key):
            if key == "IMG_TIR1":
                return self._raw[np.newaxis, :, :]
            if key == "IMG_TIR1_TEMP":
                return self._lut
            if key == "X":
                return self._x
            if key == "Y":
                return self._y
            raise KeyError(key)

    with patch("core.insat_reader.h5py.File", return_value=FakeHandle()):
        Tb, lat, lon = load_tb_lat_lon(str(fake_path))

    assert Tb.dtype == np.float32
    assert lat.dtype == np.float32
    assert lon.dtype == np.float32


def test_load_tb_lat_lon_returns_expected_shapes(tmp_path):
    file_path = tmp_path / "mini_insat.h5"
    with h5py.File(file_path, "w") as handle:
        handle["IMG_TIR1"] = np.array([[[0, 1], [2, 3]]], dtype=np.uint16)
        handle["IMG_TIR1_TEMP"] = np.array([100.0, 200.0, 300.0, 400.0], dtype=np.float32)
        handle["X"] = np.array([0.0, 1.0], dtype=np.float32)
        handle["Y"] = np.array([0.0, 1.0], dtype=np.float32)

    Tb, lat, lon = load_tb_lat_lon(str(file_path))

    assert Tb.shape == (2, 2)
    assert lat.shape == (2, 2)
    assert lon.shape == (2, 2)
    assert np.isfinite(Tb).all()


def test_describe_geographic_context_labels_indian_sector():
    context = describe_geographic_context(18.5, 80.2)

    assert "India" in context or "Indian" in context


def test_build_threat_explanation_mentions_reasoning():
    explanation = build_threat_explanation({"risk_level": "High", "risk_score": 72.0, "trend": "Intensifying", "mean_tb": 205.0, "mean_radius_km": 700.0})

    assert "High" in explanation
    assert "Intensifying" in explanation or "risk" in explanation.lower()


def test_scaled_region_centroid_stays_two_dimensional():
    region = type("FakeRegion", (), {"coords": np.array([[1, 2], [3, 4]]), "centroid": (5.0, 6.0), "area": 2.0})()

    scaled = _ScaledRegion(region, scale=4)

    assert scaled.centroid.shape == (2,)
    assert scaled.centroid.tolist() == [20.0, 24.0]
    assert scaled.coords.shape == (2, 2)


def test_fetch_latest_satellite_data_falls_back_when_live_file_is_invalid(tmp_path):
    data_dir = tmp_path / "ingest"
    data_dir.mkdir()
    demo_file = data_dir / "demo_insat.h5"
    demo_file.write_bytes(b"demo-matrix")

    with patch("core.data_fetcher.urllib.request.urlretrieve", return_value=(str(data_dir / "live_stream.h5"), None)):
        path, status = fetch_latest_satellite_data(data_dir=str(data_dir), fallback_path=str(demo_file))

    assert status == "FALLBACK_DEMO"
    assert path == str(demo_file)
