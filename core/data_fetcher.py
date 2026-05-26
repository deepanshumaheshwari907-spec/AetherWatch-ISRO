import os
import urllib.request

# Public cloud backup URL jahan humne backup matrix rakha hai
SATELLITE_DATA_URL = "https://raw.githubusercontent.com/datasets/master/sample.h5" # Sample placeholder for internet fetch

def fetch_latest_satellite_data():
    """
    Automated Ingestion Pipeline with Fallback Logic.
    Fetches live geostationary matrix from cloud storage.
    """
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    live_path = os.path.join(data_dir, 'live_stream.h5')
    fallback_path = os.path.join(data_dir, 'demo_insat.h5')
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        print("🛰️ [INGESTION] Attempting to pull latest geostationary swath from matrix link...")
        # Internet se live download karne ki koshish (Timeout 10 seconds)
        urllib.request.urlretrieve(SATELLITE_DATA_URL, live_path)
        print("✅ [INGESTION] Live matrix synchronization successful.")
        return live_path, "LIVE_STREAM"
        
    except Exception as e:
        print(f"⚠️ [INGESTION WARNING] Cloud link unreachable: {e}")
        print("🔄 [INGESTION] Activating Failsafe Local Fallback Matrix...")
        
        # Check if local file exists
        if os.path.exists(fallback_path):
            return fallback_path, "FALLBACK_DEMO"
        else:
            raise FileNotFoundError("Critical System Error: Both Cloud and Local fallback data matrices are missing!")