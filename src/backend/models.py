"""
Two-Stage BigCat Classification Models
- Stage 1: Binary Filter (BigCat vs NotBigCat)
- Stage 2: Species Classifier (Jaguar, Leopard, Tiger, Lion, Cheetah)
Uses timm EfficientNet-B2 which matches saved model weights
"""
import torch
import torch.nn as nn
from pathlib import Path

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False

from config import (
    DEVICE,
    STAGE1_MODEL_PATH,
    STAGE2_MODEL_PATH,
    STAGE2_CLASSES,
    NUM_STAGE2_CLASSES
)


def load_stage1_model():
    """Load Stage 1: BigCat Binary Filter using timm"""
    print("Loading Stage 1 (BigCat Binary Filter)...")
    
    if not TIMM_AVAILABLE:
        raise ImportError("timm is required. Install with: pip install timm")
    
    # Create model using timm (matches how it was trained)
    model = timm.create_model("efficientnet_b2", pretrained=False)
    # Replace classifier for binary output
    model.classifier = nn.Linear(model.classifier.in_features, 2)
    
    try:
        checkpoint = torch.load(STAGE1_MODEL_PATH, map_location=DEVICE, weights_only=False)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        print("[OK] Stage 1 weights loaded successfully")
    except Exception as e:
        print(f"[WARNING] Could not load Stage 1 weights: {e}")
        print("  Using randomly initialized model")
    
    model.to(DEVICE)
    model.eval()
    print(f"[OK] Stage 1 model loaded on {DEVICE}")
    return model


def load_stage2_model():
    """Load Stage 2: Species Classifier using timm"""
    print("Loading Stage 2 (Species Classifier)...")
    
    if not TIMM_AVAILABLE:
        raise ImportError("timm is required. Install with: pip install timm")
    
    # Create model using timm (matches how it was trained)
    model = timm.create_model("efficientnet_b2", pretrained=False)
    # Replace classifier for multi-class species output
    model.classifier = nn.Linear(model.classifier.in_features, NUM_STAGE2_CLASSES)
    
    try:
        checkpoint = torch.load(STAGE2_MODEL_PATH, map_location=DEVICE, weights_only=False)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        print("[OK] Stage 2 weights loaded successfully")
    except Exception as e:
        print(f"[WARNING] Could not load Stage 2 weights: {e}")
        print("  Using randomly initialized model")
    
    model.to(DEVICE)
    model.eval()
    print(f"[OK] Stage 2 model loaded on {DEVICE}")
    print(f"  Classes: {list(STAGE2_CLASSES.values())}")
    return model

