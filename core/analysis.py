import hashlib
import os
from datetime import datetime, timezone

import numpy as np

from config import Config
from .ai_engine import detect_and_cluster_clouds
from .feature_extractor import extract_tcc_features
from .insat_reader import load_insat_scene
from .risk_engine import is_valid_tcc


def sha256_file(filepath, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with open(filepath, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze_file(filepath, source_mode="HISTORICAL"):
    scene = load_insat_scene(filepath)
    thermal = scene["thermal"]
    latitude = scene["latitude"]
    longitude = scene["longitude"]
    _, regions, _ = detect_and_cluster_clouds(
        thermal, Config.THERMAL_THRESHOLD_KELVIN
    )

    threats = []
    for region in regions:
        if not is_valid_tcc(
            region, Config.PIXEL_AREA_KM2, Config.MIN_REGION_AREA_KM2
        ):
            continue
        threats.append(
            extract_tcc_features(
                region,
                thermal,
                latitude,
                longitude,
                Config.PIXEL_AREA_KM2,
            )
        )
    threats.sort(key=lambda item: item["risk_score"], reverse=True)

    finite = thermal[np.isfinite(thermal)]
    metadata = scene["metadata"]
    return {
        "source_path": os.path.abspath(filepath),
        "source_filename": os.path.basename(filepath),
        "source_name": metadata["source"],
        "source_mode": source_mode.upper(),
        "product_name": metadata["product_name"],
        "acquisition_time": metadata["acquisition_time"],
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "checksum_sha256": sha256_file(filepath),
        "status": "COMPLETED",
        "detector": "COLD_CLOUD_THRESHOLD_V1",
        "threshold_kelvin": Config.THERMAL_THRESHOLD_KELVIN,
        "min_temperature_kelvin": float(np.min(finite)),
        "max_temperature_kelvin": float(np.max(finite)),
        "mean_temperature_kelvin": float(np.mean(finite)),
        "valid_pixel_fraction": metadata["valid_pixel_fraction"],
        "threat_count": len(threats),
        "threats": threats,
    }
