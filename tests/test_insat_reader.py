from pathlib import Path

import h5py
import pytest

from core.insat_reader import load_insat_scene, validate_insat_file


def test_real_fixture_metadata():
    fixture = Path(__file__).resolve().parents[1] / "data" / "demo_insat.h5"
    scene = load_insat_scene(str(fixture))
    assert scene["thermal"].shape == scene["latitude"].shape
    assert scene["thermal"].shape == scene["longitude"].shape
    assert scene["metadata"]["acquisition_time"].startswith("2024-06-18")


def test_missing_dataset_is_rejected(tmp_path):
    path = tmp_path / "invalid.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("IMG_TIR1", data=[[0]])
    with pytest.raises(ValueError, match="Missing HDF5 datasets"):
        validate_insat_file(str(path))
