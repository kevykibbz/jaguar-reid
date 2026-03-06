"""
Configuration settings for the BigCat Multi-Stage Inference Pipeline.

TWO-STAGE ARCHITECTURE:
├── Stage 1: BigCat Binary Filter (EfficientNet-B2)
│   ├── Input: Any animal image
│   ├── Task: Binary classification (BigCat vs NotBigCat)
│   └── Output: Binary label + confidence score
│
└── Stage 2: Species Classifier (EfficientNet-B2)
    ├── Input: Images classified as BigCat
    ├── Task: Multi-class species classification
    ├── Classes: Jaguar, Leopard, Tiger, Lion, Cheetah
    └── Output: Species label + confidence score
"""
import torch
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "jaguar-images")

# Automatic device detection
def get_device():
    """Automatically detect and return the best available device."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        device = torch.device("cpu")
        print("[CPU] No GPU detected, using CPU")
    return device

DEVICE = get_device()

# ==================== TWO-STAGE MODEL PATHS ====================
# Stage 1: BigCat Binary Filter
STAGE1_MODEL_PATH = "models/stage1_bigcat_efficientnet_b2.pth"

# Stage 2: Species Classifier (5 classes: Jaguar, Leopard, Tiger, Lion, Cheetah)
STAGE2_MODEL_PATH = "models/stage2_species_efficientnet_b2.pth"
STAGE2_CLASS_MAPPING_PATH = "models/mappings/stage2_class_mapping.json"

# Load Stage 2 class mapping
def load_stage2_classes():
    """Load species class names from mapping file."""
    mapping_path = Path(STAGE2_CLASS_MAPPING_PATH)
    if mapping_path.exists():
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)
        # Create reverse mapping (index -> class name)
        return {v: k for k, v in mapping.items()}
    else:
        print(f"⚠ Warning: Stage 2 mapping not found at {STAGE2_CLASS_MAPPING_PATH}")
        return {0: "cheetah", 1: "jaguar", 2: "leopard", 3: "lion", 4: "tiger"}

STAGE2_CLASSES = load_stage2_classes()
NUM_STAGE2_CLASSES = len(STAGE2_CLASSES)

# ==================== IMAGE PREPROCESSING ====================
IMAGE_SIZE = 224  # EfficientNet-B2 standard input size

# ==================== INFERENCE THRESHOLDS ====================
STAGE1_CONFIDENCE_THRESHOLD = 0.5   # Minimum confidence for "BigCat" classification
STAGE2_CONFIDENCE_THRESHOLD = 0.5   # Minimum confidence for species classification

# ==================== VIDEO PROCESSING ====================
VIDEO_BATCH_SIZE = 16  # Number of frames to process in parallel (batch processing)
# Increase for more GPU memory, decrease for lower memory systems

# ==================== API SETTINGS ====================
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost",
    "https://jaguar-reid-frontend.ashymeadow-ca757d9f.eastus.azurecontainerapps.io",
    "*",
]