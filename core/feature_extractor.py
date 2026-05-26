import numpy as np
from .risk_engine import (
    haversine_km,
    compute_risk_score,
    risk_level_from_score,
    classify_trend
)

def extract_tcc_features(region, Tb, lat, lon):
    """
    Extracts scientific, geographical, and risk features from an AI-detected cloud cluster.
    """
    coords = region.coords
    t_vals = Tb[coords[:, 0], coords[:, 1]]

    # Find the center of the cloud
    center_row, center_col = map(int, region.centroid)
    center_lat = lat[center_row, center_col]
    center_lon = lon[center_row, center_col]

    # Failsafe: If centroid falls in a map gap (NaN), pick the first valid cloud pixel
    if np.isnan(center_lat) or np.isnan(center_lon):
        for (r, c) in coords:
            if not np.isnan(lat[r, c]) and not np.isnan(lon[r, c]):
                center_lat = lat[r, c]
                center_lon = lon[r, c]
                break

    # Calculate radius/spread of the cloud
    distances = []
    for (r, c) in coords:
        if not np.isnan(lat[r, c]) and not np.isnan(lon[r, c]):
            d = haversine_km(center_lat, center_lon, lat[r, c], lon[r, c])
            distances.append(d)

    distances = np.array(distances)
    min_tb = float(np.min(t_vals))
    mean_radius_km = float(np.mean(distances)) if len(distances) else 0.0

    # Apply Threat Intelligence Logic
    risk_score = compute_risk_score(min_tb, mean_radius_km)
    risk_level = risk_level_from_score(risk_score)
    trend = classify_trend(min_tb, mean_radius_km)

    return {
        "pixel_count": float(region.area),
        "mean_tb": float(np.mean(t_vals)),
        "min_tb": min_tb,
        "center_lat": float(center_lat),
        "center_lon": float(center_lon),
        "mean_radius_km": mean_radius_km,
        "risk_score": float(risk_score),
        "risk_level": risk_level,
        "trend": trend,
    }