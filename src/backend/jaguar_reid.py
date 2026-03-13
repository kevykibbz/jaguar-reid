"""
Stage 3: Jaguar Individual Re-Identification
Uses ConvNeXT + ArcFace model to extract unique facial embeddings
and match against known individuals in the database.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import io
from typing import cast

class JaguarReIDModel(nn.Module):
    """ConvNeXT-based jaguar re-identification model with ArcFace head"""
    
    def __init__(self, embedding_size=512, pretrained=False):
        super().__init__()
        
        # Load torchvision ConvNeXT backbone
        self.backbone = models.convnext_base(
            weights=models.ConvNeXt_Base_Weights.IMAGENET1K_V1 if pretrained else None
        )
        
        # Remove classifier (replace with identity for feature extraction)
        self.backbone.classifier = nn.Identity()  # type: ignore[assignment]
        
        # Pooling layer
        self.pool = nn.AdaptiveAvgPool2d(1)
        
        # Embedding head (1024 is ConvNeXT-Base output channels)
        self.embedding = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024, embedding_size),
            nn.BatchNorm1d(embedding_size)
        )
        
        self.embedding_size = embedding_size
    
    def forward(self, x):
        # Extract features from backbone [B, 1024, H, W]
        x = self.backbone(x)
        
        # Pool to [B, 1024, 1, 1]
        x = self.pool(x)
        
        # Project to embedding space [B, 512]
        x = self.embedding(x)
        
        # L2 normalize embeddings
        x = F.normalize(x, p=2, dim=1)
        
        return x


# Image preprocessing for ConvNeXT
reid_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def load_jaguar_reid_model(model_path, embedding_size=512, device='cpu'):
    """
    Load trained jaguar re-identification model.
    
    Args:
        model_path: Path to .pth checkpoint file
        embedding_size: Size of output embeddings
        device: Device to load model on ('cpu' or 'cuda')
    
    Returns:
        Loaded model in eval mode
    """
    print(f"Loading Jaguar Re-ID model from {model_path}...")
    
    model = JaguarReIDModel(embedding_size=embedding_size, pretrained=False)
    
    try:
        # Load state dict directly
        state_dict = torch.load(model_path, map_location=device, weights_only=False)
        
        # If it's a checkpoint dict with metadata, extract state_dict
        if isinstance(state_dict, dict) and 'model_state_dict' in state_dict:
            state_dict = state_dict['model_state_dict']
        elif isinstance(state_dict, dict) and 'state_dict' in state_dict:
            state_dict = state_dict['state_dict']
        
        model.load_state_dict(state_dict)
        print("✓ Loaded Re-ID model weights successfully")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not load Re-ID weights: {e}")
        print("  Using randomly initialized model")
    
    model.to(device)
    model.eval()
    print(f"✓ Jaguar Re-ID model ready on {device}")
    
    return model


def extract_jaguar_embedding(image_bytes, model, device='cpu'):
    """
    Extract jaguar facial embedding from image.
    
    Args:
        image_bytes: Raw image bytes (JPEG/PNG)
        model: Loaded JaguarReIDModel
        device: Device model is on (str or torch.device)
    
    Returns:
        numpy array of shape (embedding_size,) - the facial embedding vector
    """
    # Load and preprocess image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    # Apply transform to get tensor
    image_tensor = cast(torch.Tensor, reid_transform(image))
    # Add batch dimension and move to device
    image_tensor = image_tensor.unsqueeze(0).to(device)
    
    # Extract embedding
    with torch.no_grad():
        embedding = model(image_tensor)
    
    # Convert to numpy
    embedding_np = embedding.cpu().numpy()[0]
    
    return embedding_np


def extract_embedding_from_pil(pil_image, model, device='cpu'):
    """
    Extract jaguar embedding from PIL Image.
    
    Args:
        pil_image: PIL Image object (RGB)
        model: Loaded JaguarReIDModel
        device: Device model is on (str or torch.device)
    
    Returns:
        numpy array - the facial embedding vector
    """
    # Ensure PIL image is in RGB mode
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Apply transform to get tensor
    image_tensor = cast(torch.Tensor, reid_transform(pil_image))
    # Add batch dimension and move to device
    image_tensor = image_tensor.unsqueeze(0).to(device)
    
    with torch.no_grad():
        embedding = model(image_tensor)
    
    embedding_np = embedding.cpu().numpy()[0]
    
    return embedding_np


def compute_similarity(embedding1, embedding2):
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: numpy array or torch tensor
        embedding2: numpy array or torch tensor
    
    Returns:
        float: similarity score (0-1, higher = more similar)
    """
    import numpy as np
    
    # Convert to numpy if torch tensor
    if torch.is_tensor(embedding1):
        embedding1 = embedding1.cpu().numpy()
    if torch.is_tensor(embedding2):
        embedding2 = embedding2.cpu().numpy()
    
    # Ensure embeddings are 1D
    embedding1 = embedding1.flatten()
    embedding2 = embedding2.flatten()
    
    # Compute cosine similarity
    dot_product = np.dot(embedding1, embedding2)
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    similarity = dot_product / (norm1 * norm2)
    
    return float(similarity)
