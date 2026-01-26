"""
Model definitions for Jaguar Re-Identification.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor
from config import (
    DEVICE, 
    REID_MODEL_PATH, 
    YOLO_MODEL_PATH, 
    SAM_MODEL_PATH,
    SAM_MODEL_TYPE,
    EMBEDDING_DIM
)

class ConvNeXtEmbedding(nn.Module):
    """
    ConvNeXT-based embedding model for jaguar re-identification.
    Extracts 512-dimensional normalized embeddings.
    """
    def __init__(self, embedding_dim=EMBEDDING_DIM):
        super().__init__()

        self.backbone = models.convnext_base(
            weights=models.ConvNeXt_Base_Weights.IMAGENET1K_V1
        )
        self.backbone.classifier = nn.Identity()

        self.pool = nn.AdaptiveAvgPool2d(1)

        self.embedding = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024, embedding_dim),
            nn.BatchNorm1d(embedding_dim)
        )

    def forward(self, x):
        x = self.backbone(x)
        x = self.pool(x)
        x = self.embedding(x)
        x = F.normalize(x, p=2, dim=1)
        return x


def load_reid_model():
    """
    Load the pre-trained Re-ID model and move to device.
    """
    print("Loading Re-ID model...")
    model = ConvNeXtEmbedding()
    model.load_state_dict(
        torch.load(REID_MODEL_PATH, map_location=DEVICE, weights_only=True)
    )
    model.to(DEVICE)
    model.eval()
    print(f" Re-ID model loaded on {DEVICE}")
    return model


def load_yolo_model():
    """
    Load YOLO model for jaguar detection.
    """
    print("Loading YOLO detection model...")
    yolo_model = YOLO(YOLO_MODEL_PATH)
    print(f"✓ YOLO model loaded")
    return yolo_model


def load_sam_model():
    """
    Load Segment Anything Model (SAM) for precise segmentation.
    """
    print("Loading SAM segmentation model...")
    try:
        sam = sam_model_registry[SAM_MODEL_TYPE](checkpoint=SAM_MODEL_PATH)
        sam.to(device=DEVICE)
        sam.eval()
        predictor = SamPredictor(sam)
        print(f"✓ SAM model loaded on {DEVICE}")
        return predictor
    except Exception as e:
        print(f"⚠ SAM model not found, downloading...")
        print(f"  Please download from: https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth")
        print(f"  Place it in the backend directory")
        return None
