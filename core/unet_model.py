import torch
import torch.nn as nn

class UNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=4):
        """
        in_channels = 1 (Sirf Thermal Infrared band le rahe hain)
        out_channels = 4 (Classes: 0=Clear, 1=Low Cloud, 2=Moderate, 3=Severe Core)
        """
        super(UNet, self).__init__()

        # Encoder (Contracting Path)
        self.enc1 = self.conv_block(in_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Bottleneck (The bottom of the 'U')
        self.bottleneck = self.conv_block(256, 512)

        # Decoder (Expansive Path)
        self.upconv3 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.dec3 = self.conv_block(512, 256)
        
        self.upconv2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec2 = self.conv_block(256, 128)
        
        self.upconv1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec1 = self.conv_block(128, 64)

        # Final Output Layer
        self.final_conv = nn.Conv2d(64, out_channels, kernel_size=1)

    def conv_block(self, in_c, out_c):
        """Ek standard block jisme Convolution aur ReLU activation lagta hai"""
        return nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        # Downsampling
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        
        # Bottleneck
        b = self.bottleneck(self.pool(e3))
        
        # Upsampling & Skip Connections
        d3 = self.upconv3(b)
        d3 = torch.cat((e3, d3), dim=1) # Skip connection
        d3 = self.dec3(d3)
        
        d2 = self.upconv2(d3)
        d2 = torch.cat((e2, d2), dim=1) # Skip connection
        d2 = self.dec2(d2)
        
        d1 = self.upconv1(d2)
        d1 = torch.cat((e1, d1), dim=1) # Skip connection
        d1 = self.dec1(d1)
        
        out = self.final_conv(d1)
        return out