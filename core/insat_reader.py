import h5py
import numpy as np
import os

def load_tb_lat_lon(filepath):
    """
    Reads INSAT-3D L1C .h5 file and calculates Brightness Temperature (Tb),
    Latitude, and Longitude grids.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Satellite data file not found at: {filepath}")

    with h5py.File(filepath, "r") as f:
        # Extract raw image and look-up table (LUT)
        raw = f["IMG_TIR1"][0]
        lut = f["IMG_TIR1_TEMP"][:]
        Tb  = lut[raw]

        X = f["X"][:]   # scan angle grid
        Y = f["Y"][:]

    # INSAT geostationary constants
    sat_lon = 82.0          # INSAT-3D longitude (deg E)
    H       = 42164000.0    # satellite height (m)
    Re      = 6378137.0
    Rp      = 6356752.3

    xx, yy = np.meshgrid(X, Y)

    x = np.deg2rad(xx)
    y = np.deg2rad(yy)

    cosx = np.cos(x)
    cosy = np.cos(y)
    sinx = np.sin(x)
    siny = np.sin(y)

    # Projection Math
    a = (H * cosx * cosy)**2 - (cosy**2 + (Re/Rp)**2 * siny**2) * (H**2 - Re**2)
    a[a < 0] = np.nan
    a = np.sqrt(a)

    sn = (H*cosx*cosy - a) / (cosy**2 + (Re/Rp)**2 * siny**2)

    sx = sn * cosx * cosy
    sy = -sn * sinx * cosy
    sz =  sn * siny

    lon = np.rad2deg(np.arctan2(sy, sx)) + sat_lon
    lat = np.rad2deg(np.arctan((Re**2 / Rp**2) * (sz / np.sqrt(sx**2 + sy**2))))

    return Tb, lat, lon