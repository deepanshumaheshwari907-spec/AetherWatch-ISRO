import numpy as np
from skimage.measure import label, regionprops


def detect_and_cluster_clouds(thermal, threshold=235):
    """Detect cold-cloud candidates using a deterministic threshold."""
    mask = np.isfinite(thermal) & (thermal <= threshold)
    labeled_image = label(mask, connectivity=2)
    regions = regionprops(labeled_image)
    return labeled_image, regions, mask.astype(np.uint8)
