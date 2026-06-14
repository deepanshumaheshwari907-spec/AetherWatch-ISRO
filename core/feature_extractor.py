import numpy as np

from .risk_engine import (
    classify_trend,
    compute_risk_score,
    haversine_km,
    risk_level_from_score,
)


def extract_tcc_features(region, thermal, latitude, longitude, pixel_area_km2=4.0):
    """Return the canonical cold-cloud candidate representation."""
    coords = region.coords
    temperatures = thermal[coords[:, 0], coords[:, 1]]
    finite_temperatures = temperatures[np.isfinite(temperatures)]
    if finite_temperatures.size == 0:
        raise ValueError("Candidate has no valid thermal pixels")

    center_row, center_col = map(int, region.centroid)
    center_lat = latitude[center_row, center_col]
    center_lon = longitude[center_row, center_col]
    if not np.isfinite(center_lat) or not np.isfinite(center_lon):
        valid_coords = [
            (row, col)
            for row, col in coords
            if np.isfinite(latitude[row, col]) and np.isfinite(longitude[row, col])
        ]
        if not valid_coords:
            raise ValueError("Candidate has no valid geographic coordinates")
        center_row, center_col = valid_coords[len(valid_coords) // 2]
        center_lat = latitude[center_row, center_col]
        center_lon = longitude[center_row, center_col]

    distances = [
        haversine_km(
            center_lat,
            center_lon,
            latitude[row, col],
            longitude[row, col],
        )
        for row, col in coords
        if np.isfinite(latitude[row, col]) and np.isfinite(longitude[row, col])
    ]
    min_temperature = float(np.min(finite_temperatures))
    mean_radius_km = float(np.mean(distances)) if distances else 0.0
    risk_score = compute_risk_score(min_temperature, mean_radius_km)

    return {
        "pixel_count": int(region.area),
        "area_km2": float(region.area * pixel_area_km2),
        "mean_temperature_kelvin": float(np.mean(finite_temperatures)),
        "min_temperature_kelvin": min_temperature,
        "latitude": float(center_lat),
        "longitude": float(center_lon),
        "mean_radius_km": mean_radius_km,
        "risk_score": float(risk_score),
        "risk_level": risk_level_from_score(risk_score),
        "trend": classify_trend(min_temperature, mean_radius_km),
    }
