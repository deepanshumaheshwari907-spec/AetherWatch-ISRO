"""
AetherWatch — Satellite Data Ingestion Pipeline
Priority order:
  1. Live download from configured URL (if set and reachable)
  2. Most recent file in data/downloads/
  3. Demo fallback matrix (demo_insat.h5)
"""

import os
import glob
import urllib.request
import h5py

# Set a real URL here if you have a live feed; leave as empty string for demo mode.
SATELLITE_DATA_URL = os.environ.get("INSAT_LIVE_URL", "")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def _is_valid_insat_h5(filepath: str) -> bool:
    """Return True only if the file is a readable INSAT-style HDF5 matrix."""
    if not os.path.exists(filepath):
        return False
    try:
        with h5py.File(filepath, "r") as fh:
            required = ("IMG_TIR1", "IMG_TIR1_TEMP", "X", "Y")
            return all(k in fh for k in required)
    except Exception:
        return False


def _latest_downloaded_file() -> str | None:
    """Return the most recently modified valid H5 file from the downloads folder."""
    downloads_dir = os.path.join(DATA_DIR, "downloads")
    candidates    = glob.glob(os.path.join(downloads_dir, "*.h5")) + \
                    glob.glob(os.path.join(downloads_dir, "*.hdf5"))
    valid = [f for f in candidates if _is_valid_insat_h5(f)]
    if not valid:
        return None
    return max(valid, key=os.path.getmtime)


def fetch_latest_satellite_data(data_dir: str = None,
                                 fallback_path: str = None) -> tuple[str, str]:
    """
    Automated Ingestion Pipeline with 3-level fallback.

    Returns
    -------
    (filepath, status_string)
        status is one of: LIVE_STREAM | CACHED_DOWNLOAD | FALLBACK_DEMO
    """
    _data_dir     = data_dir     or DATA_DIR
    _fallback     = fallback_path or os.path.join(_data_dir, "demo_insat.h5")
    live_path     = os.path.join(_data_dir, "live_stream.h5")

    os.makedirs(_data_dir, exist_ok=True)

    # ── LEVEL 1: Live download ──────────────────────────────────────────────
    if SATELLITE_DATA_URL:
        try:
            print("🛰️  [INGESTION] Pulling live geostationary swath…")
            urllib.request.urlretrieve(SATELLITE_DATA_URL, live_path)
            if not _is_valid_insat_h5(live_path):
                raise ValueError("Downloaded file is not a valid INSAT matrix.")
            print("✅ [INGESTION] Live matrix synchronised.")
            return live_path, "LIVE_STREAM"
        except Exception as exc:
            print(f"⚠️  [INGESTION] Live fetch failed: {exc}")

    # ── LEVEL 2: Most recent cached download ───────────────────────────────
    cached = _latest_downloaded_file()
    if cached:
        print(f"🔄 [INGESTION] Using cached download: {os.path.basename(cached)}")
        return cached, f"CACHED::{os.path.basename(cached)}"

    # ── LEVEL 3: Demo fallback ─────────────────────────────────────────────
    if _is_valid_insat_h5(_fallback):
        print("🔄 [INGESTION] Activating demo fallback matrix.")
        return _fallback, "FALLBACK_DEMO"

    raise FileNotFoundError(
        "No valid satellite data found. "
        "Upload an INSAT HDF5 file via the sidebar or set the INSAT_LIVE_URL environment variable."
    )