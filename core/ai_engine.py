import numpy as np
import os
from skimage.measure import label, regionprops

# Failsafe imports
try:
    import torch
    import torch.nn.functional as F
    from .unet_model import UNet
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

from sklearn.cluster import KMeans

class _ScaledRegion:
    def __init__(self, region, scale):
        self._region = region
        self.coords = np.round(np.asarray(region.coords, dtype=np.float64) * scale).astype(np.int32)
        self.centroid = np.asarray(region.centroid, dtype=np.float64) * scale
        self.area = int(np.asarray(region.area, dtype=np.float64) * (scale ** 2))

    def __getattr__(self, name):
        return getattr(self._region, name)


def detect_and_cluster_clouds(Tb, threshold=235):
    """
    Failsafe AI-Powered Cloud Segmentation.
    Primary: PyTorch U-Net (Deep Learning)
    Fallback: K-Means Clustering (Machine Learning)
    """
    scale = 1
    if max(Tb.shape) > 1024:
        scale = max(1, int(np.ceil(max(Tb.shape) / 1024)))

    working_tb = Tb[::scale, ::scale]
    mask = working_tb <= threshold
    labeled_image = label(mask, connectivity=2)
    regions = [_ScaledRegion(region, scale) for region in regionprops(labeled_image)]

    ai_segmented_mask = np.zeros_like(working_tb, dtype=np.uint8)
    
    if np.any(mask):
        use_fallback = False
        weights_path = os.path.join(os.path.dirname(__file__), 'unet_trained_weights.pth')
        
        # --- PRIMARY ENGINE: DEEP LEARNING ---
        if PYTORCH_AVAILABLE and os.path.exists(weights_path):
            try:
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                model = UNet(in_channels=1, out_channels=4).to(device)
                model.load_state_dict(torch.load(weights_path, map_location=device))
                model.eval()
                
                with torch.no_grad():
                    Tb_norm = working_tb / 330.0
                    orig_h, orig_w = working_tb.shape
                    
                    input_tensor = torch.tensor(Tb_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
                    input_resized = F.interpolate(input_tensor, size=(256, 256), mode='bilinear', align_corners=False).to(device)
                    
                    output = model(input_resized)
                    output_resized = F.interpolate(output, size=(orig_h, orig_w), mode='bilinear', align_corners=False)
                    
                    _, predicted_mask = torch.max(output_resized, 1)
                    ai_segmented_mask = predicted_mask.squeeze().cpu().numpy().astype(np.uint8)
                    ai_segmented_mask = np.where(mask, ai_segmented_mask, 0)
                    
            except Exception as e:
                print(f"⚠️ [AI ENGINE] Deep Learning Failed ({e}). Switching to Fallback...")
                use_fallback = True
        else:
            use_fallback = True
            
        # --- FALLBACK ENGINE: K-MEANS ML ---
        if use_fallback:
            print("🔄 [AI ENGINE] Executing K-Means Fallback Protocol.")
            cold_pixels = working_tb[mask]
            if len(cold_pixels) >= 3: 
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                pixel_data = cold_pixels.reshape(-1, 1)
                labels = kmeans.fit_predict(pixel_data)
                ai_segmented_mask[mask] = labels + 1
                
    return labeled_image, regions, ai_segmented_mask