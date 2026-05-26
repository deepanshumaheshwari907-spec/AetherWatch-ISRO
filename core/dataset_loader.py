import os
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T
import h5py
import numpy as np

class INSATCloudDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        """
        data_dir: Folder jahan saari .h5 satellite files rakhi hain
        """
        self.data_dir = data_dir
        self.file_list = [f for f in os.listdir(data_dir) if f.endswith('.h5')]
        
        # 🌟 THE FIX: Resizing massive satellite images to fit in laptop RAM
        self.resize = T.Resize((256, 256), antialias=True)

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        file_path = os.path.join(self.data_dir, self.file_list[idx])
        
        try:
            with h5py.File(file_path, 'r') as f:
                # Raw thermal data extract karna
                raw = f["IMG_TIR1"][0]
                lut = f["IMG_TIR1_TEMP"][:]
                Tb = lut[raw]
                
                # Deep Learning Normalization
                Tb_normalized = Tb / 330.0 
                
                # Tensor conversion: Shape (1, H, W)
                image_tensor = torch.tensor(Tb_normalized, dtype=torch.float32).unsqueeze(0)
                
                # 🌟 Apply Resizing to save RAM (5GB -> few MBs)
                image_tensor = self.resize(image_tensor)
                
                # Dummy mask for prototype training (Also resized)
                dummy_mask = torch.zeros((1, Tb.shape[0], Tb.shape[1]), dtype=torch.float32)
                dummy_mask = self.resize(dummy_mask).squeeze(0).long()
                
                return image_tensor, dummy_mask
                
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            # Failsafe: Return empty 256x256 tensors if file corrupts
            return torch.zeros((1, 256, 256)), torch.zeros((256, 256), dtype=torch.long)