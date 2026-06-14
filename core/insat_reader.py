import os
from datetime import datetime, timezone

import h5py
import numpy as np

REQUIRED_DATASETS = ("IMG_TIR1", "IMG_TIR1_TEMP", "X", "Y")


def _decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _parse_acquisition_time(attrs):
    for key in ("Acquisition_Start_Time", "Acquisition_End_Time"):
        if key not in attrs:
            continue
        raw = _decode(attrs[key]).strip()
        for fmt in ("%d-%b-%YT%H:%M:%S", "%d-%B-%YT%H:%M:%S"):
            try:
                return datetime.strptime(raw, fmt).replace(
                    tzinfo=timezone.utc
                ).isoformat()
            except ValueError:
                pass
    return None


def validate_insat_file(filepath):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Satellite data file not found: {filepath}")
    if not h5py.is_hdf5(filepath):
        raise ValueError(f"Not a valid HDF5 file: {filepath}")
    with h5py.File(filepath, "r") as handle:
        missing = [name for name in REQUIRED_DATASETS if name not in handle]
        if missing:
            raise ValueError(f"Missing HDF5 datasets: {', '.join(missing)}")
        if handle["IMG_TIR1"].ndim not in (2, 3):
            raise ValueError(
                f"Unexpected IMG_TIR1 shape: {handle['IMG_TIR1'].shape}"
            )
    return True


def load_insat_scene(filepath):
    validate_insat_file(filepath)
    with h5py.File(filepath, "r") as handle:
        raw_data = handle["IMG_TIR1"]
        raw = raw_data[0] if raw_data.ndim == 3 else raw_data[:]
        lut = handle["IMG_TIR1_TEMP"][:]
        if raw.size == 0 or int(np.nanmax(raw)) >= len(lut):
            raise ValueError("Thermal image indexes exceed its lookup table")
        thermal = lut[raw].astype(np.float32)
        x_values = handle["X"][:]
        y_values = handle["Y"][:]
        metadata = {
            "source": "MOSDAC INSAT L1C",
            "filename": os.path.basename(filepath),
            "product_name": _decode(
                handle.attrs.get("HDF_Product_File_Name", os.path.basename(filepath))
            ),
            "acquisition_time": _parse_acquisition_time(handle.attrs),
        }

    if x_values.ndim == 1 and y_values.ndim == 1:
        xx, yy = np.meshgrid(x_values, y_values)
    elif x_values.shape == thermal.shape and y_values.shape == thermal.shape:
        xx, yy = x_values, y_values
    else:
        raise ValueError(
            "Coordinate grids are incompatible with the thermal image: "
            f"X={x_values.shape}, Y={y_values.shape}, thermal={thermal.shape}"
        )

    satellite_longitude = 82.0
    satellite_height = 42164000.0
    equatorial_radius = 6378137.0
    polar_radius = 6356752.3
    x_angle = np.deg2rad(xx)
    y_angle = np.deg2rad(yy)
    cos_x, cos_y = np.cos(x_angle), np.cos(y_angle)
    sin_x, sin_y = np.sin(x_angle), np.sin(y_angle)
    radius_ratio = (equatorial_radius / polar_radius) ** 2
    discriminant = (
        (satellite_height * cos_x * cos_y) ** 2
        - (cos_y**2 + radius_ratio * sin_y**2)
        * (satellite_height**2 - equatorial_radius**2)
    )
    discriminant[discriminant < 0] = np.nan
    root = np.sqrt(discriminant)
    sn = (satellite_height * cos_x * cos_y - root) / (
        cos_y**2 + radius_ratio * sin_y**2
    )
    sx = sn * cos_x * cos_y
    sy = -sn * sin_x * cos_y
    sz = sn * sin_y
    longitude = np.rad2deg(np.arctan2(sy, sx)) + satellite_longitude
    latitude = np.rad2deg(
        np.arctan(
            (equatorial_radius**2 / polar_radius**2)
            * (sz / np.sqrt(sx**2 + sy**2))
        )
    )

    valid = np.isfinite(thermal) & np.isfinite(latitude) & np.isfinite(longitude)
    if not np.any(valid):
        raise ValueError("Scene contains no valid geolocated thermal pixels")
    metadata["valid_pixel_fraction"] = float(valid.mean())
    return {
        "thermal": thermal,
        "latitude": latitude,
        "longitude": longitude,
        "metadata": metadata,
    }


def load_tb_lat_lon(filepath):
    scene = load_insat_scene(filepath)
    return scene["thermal"], scene["latitude"], scene["longitude"]
