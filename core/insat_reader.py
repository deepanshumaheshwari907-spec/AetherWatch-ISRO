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
        raw = np.asarray(f["IMG_TIR1"][0], dtype=np.int32)
        lut = np.asarray(f["IMG_TIR1_TEMP"][:], dtype=np.float32)
        Tb = lut[raw].astype(np.float32, copy=False)

        X = np.asarray(f["X"][:], dtype=np.float32)
        Y = np.asarray(f["Y"][:], dtype=np.float32)

    sat_lon = np.float32(82.0)
    H = np.float32(42164000.0)
    Re = np.float32(6378137.0)
    Rp = np.float32(6356752.3)

    lat = np.empty((Y.size, X.size), dtype=np.float32)
    lon = np.empty_like(lat)

    row_chunk = 256
    inv_rp2 = (Re / Rp) ** 2

    for start in range(0, Y.size, row_chunk):
        end = min(start + row_chunk, Y.size)

        x = np.deg2rad(X[None, :])
        y = np.deg2rad(Y[start:end, None])

        cosx = np.cos(x)
        cosy = np.cos(y)
        sinx = np.sin(x)
        siny = np.sin(y)

        a = (H * cosx * cosy) ** 2 - (cosy ** 2 + inv_rp2 * siny ** 2) * (H ** 2 - Re ** 2)
        a = np.sqrt(np.maximum(a, 0)).astype(np.float32, copy=False)

        sn = (H * cosx * cosy - a) / (cosy ** 2 + inv_rp2 * siny ** 2)

        sx = sn * cosx * cosy
        sy = -sn * sinx * cosy
        sz = sn * siny

        lon[start:end] = np.rad2deg(np.arctan2(sy, sx)).astype(np.float32) + sat_lon
        lat[start:end] = np.rad2deg(np.arctan((Re ** 2 / Rp ** 2) * (sz / np.sqrt(sx ** 2 + sy ** 2)))).astype(np.float32)

    return Tb, lat, lon