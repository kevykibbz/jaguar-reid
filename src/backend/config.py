"""
Configuration settings for the Jaguar Re-ID backend.
"""
import torch

# Automatic device detection
def get_device():
    """
    Automatically detect and return the best available device.
    Priority: CUDA GPU > CPU
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f" GPU detected: {torch.cuda.get_device_name(0)}")
        print(f" GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device("cpu")
        print(" Using CPU (No GPU detected)")
    
    return device

# Global device
DEVICE = get_device()

# Model paths
REID_MODEL_PATH = "models/convnext_arcface_jaguar_final.pth"
YOLO_MODEL_PATH = "yolov8n.pt"
SAM_MODEL_PATH = "sam_vit_b_01ec64.pth"
SAM_MODEL_TYPE = "vit_b"

# YOLO detection settings
YOLO_CONFIDENCE_THRESHOLD = 0.3
CROP_PADDING_PERCENT = 0.1

# SAM segmentation settings
SAM_POINTS_PER_SIDE = 32
SAM_PRED_IOU_THRESH = 0.88
SAM_STABILITY_SCORE_THRESH = 0.95

# ReID model settings
EMBEDDING_DIM = 512
IMAGE_SIZE = 224

# API settings
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost",
    "https://jaguar-reid-frontend.ashymeadow-ca757d9f.eastus.azurecontainerapps.io",
    "*",  # Allow all origins for production
]