"""
Three-Stage BigCat Classification Models
- Stage 1: Binary Filter (BigCat vs NotBigCat)
- Stage 2: Species Classifier (Jaguar, Leopard, Tiger, Lion, Cheetah)
- Stage 3: Jaguar Individual Re-Identification (ConvNeXT + ArcFace)
Uses timm EfficientNet-B2 for Stage 1 & 2, ConvNeXT for Stage 3
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
    NUM_STAGE2_CLASSES,
    STAGE3_REID_MODEL_PATH,
    STAGE3_EMBEDDING_SIZE
)


def load_stage1_model():
    """Load Stage 1: BigCat Binary Filter using timm"""
    print("Loading Stage 1 (BigCat Binary Filter)...")
    
    if not TIMM_AVAILABLE:
        raise ImportError("timm is required. Install with: pip install timm")
    
    # Create model using timm (matches how it was trained)
    model = timm.create_model("efficientnet_b2", pretrained=False)
    # Replace classifier for binary output
    num_features = 1408  # EfficientNet-B2 feature dimension
    model.classifier = nn.Linear(num_features, 2)

    # Newer timm versions may initialize models on meta device to save memory.
    # Materialize to CPU before loading weights so load_state_dict works.
    if any(p.is_meta for p in model.parameters()):
        model = model.to_empty(device='cpu')

    try:
        checkpoint = torch.load(STAGE1_MODEL_PATH, map_location='cpu', weights_only=False)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'], assign=True)
        else:
            model.load_state_dict(checkpoint, assign=True)
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
    num_features = 1408  # EfficientNet-B2 feature dimension
    model.classifier = nn.Linear(num_features, NUM_STAGE2_CLASSES)

    # Materialize meta tensors if timm used meta device init
    if any(p.is_meta for p in model.parameters()):
        model = model.to_empty(device='cpu')

    try:
        checkpoint = torch.load(STAGE2_MODEL_PATH, map_location='cpu', weights_only=False)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'], assign=True)
        else:
            model.load_state_dict(checkpoint, assign=True)
        print("[OK] Stage 2 weights loaded successfully")
    except Exception as e:
        print(f"[WARNING] Could not load Stage 2 weights: {e}")
        print("  Using randomly initialized model")

    model.to(DEVICE)
    model.eval()
    print(f"[OK] Stage 2 model loaded on {DEVICE}")
    print(f"  Classes: {list(STAGE2_CLASSES.values())}")
    return model


def load_stage3_model():
    """Load Stage 3: Jaguar Re-ID Model (ConvNeXT + ArcFace)"""
    print("Loading Stage 3 (Jaguar Re-Identification)...")
    
    from jaguar_reid import load_jaguar_reid_model
    
    model = load_jaguar_reid_model(
        STAGE3_REID_MODEL_PATH,
        embedding_size=STAGE3_EMBEDDING_SIZE,
        device=str(DEVICE)
    )
    
    print(f"[OK] Stage 3 model loaded on {DEVICE}")
    print(f"  Embedding size: {STAGE3_EMBEDDING_SIZE}")
    return model

