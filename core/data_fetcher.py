import os
import urllib.request

import h5py

# Public cloud backup URL jahan humne backup matrix rakha hai
SATELLITE_DATA_URL = "https://raw.githubusercontent.com/datasets/master/sample.h5"  # Sample placeholder for internet fetch


def _looks_like_valid_h5_file(filepath):
    """Return True when the downloaded file is a readable INSAT-style HDF5 matrix."""
    if not os.path.exists(filepath):
        return False

    try:
        with h5py.File(filepath, "r") as handle:
            required_keys = ("IMG_TIR1", "IMG_TIR1_TEMP", "X", "Y")
            return all(key in handle for key in required_keys)
    except Exception:
        return False


def fetch_latest_satellite_data(data_dir=None, fallback_path=None):
    """
    Automated Ingestion Pipeline with Fallback Logic.
    Fetches live geostationary matrix from cloud storage.
    """
    data_dir = data_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    live_path = os.path.join(data_dir, 'live_stream.h5')
    fallback_path = fallback_path or os.path.join(data_dir, 'demo_insat.h5')
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        print("🛰️ [INGESTION] Attempting to pull latest geostationary swath from matrix link...")
        # Internet se live download karne ki koshish (Timeout 10 seconds)
        urllib.request.urlretrieve(SATELLITE_DATA_URL, live_path)
        if not _looks_like_valid_h5_file(live_path):
            raise ValueError("Downloaded live matrix is invalid or incomplete.")

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