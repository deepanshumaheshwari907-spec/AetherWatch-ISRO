import math

# --- 1. GEO MATH ---
def haversine_km(lat1, lon1, lat2, lon2):
    """Calculates distance between two lat/lon points on Earth in km"""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def is_valid_tcc(region, pixel_km2=4, min_area_km2=34800):
    """Filters out tiny noise clouds. TCC must be large enough."""
    area_km2 = region.area * pixel_km2
    radius_km = math.sqrt(area_km2 / math.pi)
    
    # Must have at least 1 degree radius approx and sufficient area
    if (radius_km / 111) < 1 or area_km2 < min_area_km2:
        return False
    return True

# --- 2. RISK & SEVERITY MATH ---
def clamp(x, low=0, high=100):
    return max(low, min(high, x))

def compute_risk_score(min_tb, mean_radius_km=50.0):
    """Calculate a 0-100 heuristic score from temperature and candidate size."""

    if mean_radius_km is None:
        mean_radius_km = 50.0

    tb_score = clamp((235 - min_tb) / (235 - 190) * 100)
    size_score = (mean_radius_km / 1200) * 100
    risk_score = (0.6 * tb_score) + (0.4 * size_score)
    return round(risk_score, 1)

def risk_level_from_score(risk_score):
    if risk_score >= 85: return "CRITICAL"
    elif risk_score >= 60: return "HIGH"
    elif risk_score >= 30: return "MEDIUM"
    else: return "LOW"

def classify_trend(min_tb, mean_radius_km):
    if min_tb < 210 and mean_radius_km > 600: return "INTENSIFYING"
    elif min_tb < 225: return "STABLE"
    else: return "WEAKENING"
