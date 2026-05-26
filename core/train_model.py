import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import os

# Apne banaye hue modules import kar rahe hain
from unet_model import UNet
from dataset_loader import INSATCloudDataset

def train_unet():
    print("🚀 Initializing U-Net Training Sequence...")
    
    # 1. Setup Data
    # (Assuming saari .h5 files 'data/' folder me hain)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    dataset = INSATCloudDataset(data_dir=data_dir)
    
    # DataLoader batches me data bhejta hai (ek baar me 2 images)
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    
    # 2. Initialize Model, Loss, and Optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️ Computation Device: {device}")
    
    model = UNet(in_channels=1, out_channels=4).to(device)
    
    # Loss Function: Model ki galti measure karta hai
    criterion = nn.CrossEntropyLoss()
    
    # Optimizer (Adam): Model ki galti ko theek karta hai
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 3. The Training Loop
    epochs = 5 # Kitni baar model poora data dekhega
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        
        for batch_idx, (images, masks) in enumerate(dataloader):
            images, masks = images.to(device), masks.to(device)
            
            # Forward pass: Model guess karta hai
            predictions = model(images)
            
            # Loss calculate karna
            loss = criterion(predictions, masks)
            
            # Backward pass: Galtiyon se seekhna
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        print(f"📊 Epoch [{epoch+1}/{epochs}] - Loss: {epoch_loss/len(dataloader):.4f}")
        
    # 4. Save the trained brain!
    save_path = os.path.join(os.path.dirname(__file__), 'unet_trained_weights.pth')
    torch.save(model.state_dict(), save_path)
    print(f"✅ Training Complete! Model weights saved to: {save_path}")

if __name__ == "__main__":
    train_unet()