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

def detect_and_cluster_clouds(Tb, threshold=235):
    """
    Failsafe AI-Powered Cloud Segmentation.
    Primary: PyTorch U-Net (Deep Learning)
    Fallback: K-Means Clustering (Machine Learning)
    """
    mask = Tb <= threshold
    labeled_image = label(mask, connectivity=2)
    regions = regionprops(labeled_image)
    
    ai_segmented_mask = np.zeros_like(Tb, dtype=np.uint8)
    
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
                    Tb_norm = Tb / 330.0
                    orig_h, orig_w = Tb.shape
                    
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
            cold_pixels = Tb[mask]
            if len(cold_pixels) >= 3: 
                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                pixel_data = cold_pixels.reshape(-1, 1)
                labels = kmeans.fit_predict(pixel_data)
                ai_segmented_mask[mask] = labels + 1
                
    return labeled_image, regions, ai_segmented_mask