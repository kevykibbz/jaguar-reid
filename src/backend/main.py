"""
FastAPI backend for Jaguar Re-Identification system.
Provides endpoints for comparing jaguar images using deep learning.
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import torch.nn.functional as F
from typing import List, Optional
import httpx
import io
from config import CORS_ORIGINS
from models import load_reid_model, load_yolo_model, load_sam_model
from preprocessing import extract_embedding

# Initialize FastAPI app
app = FastAPI(
    title="Jaguar Re-ID API",
    description="AI-powered jaguar re-identification system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models on startup
print("=" * 60)
print("Initializing Jaguar Re-ID System")
print("=" * 60)

yolo_model = load_yolo_model()
sam_predictor = load_sam_model()
reid_model = load_reid_model()

print("=" * 60)
print("System ready!")
print("=" * 60)


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "message": "Jaguar Re-identification API",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Detailed health check with model status."""
    return {
        "status": "healthy",
        "models": {
            "yolo": "loaded",
            "sam": "loaded" if sam_predictor is not None else "unavailable",
            "reid": "loaded"
        },
        "segmentation": "SAM" if sam_predictor is not None else "bounding box"
    }


@app.post("/predict")
async def predict(
    files: Optional[List[UploadFile]] = File(None),
    url1: Optional[str] = Form(None),
    url2: Optional[str] = Form(None)
):
    """
    Compare two jaguar images and return similarity score.
    Supports both file uploads and URLs.
    
    Args:
        files: List of exactly 2 image files (optional if URLs provided)
        url1: URL to first image (optional if files provided)
        url2: URL to second image (optional if files provided)
    
    Returns:
        Dictionary with similarity score (0-1)
    """
    contents1 = None
    contents2 = None
    filename1 = "image1"
    filename2 = "image2"
    
    # Get images from files or URLs
    if files and len(files) == 2:
        contents1 = await files[0].read()
        contents2 = await files[1].read()
        filename1 = files[0].filename
        filename2 = files[1].filename
    elif url1 and url2:
        # Download images from URLs
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                print(f"📥 Downloading from URL 1: {url1}")
                response1 = await client.get(url1)
                response1.raise_for_status()
                contents1 = response1.content
                filename1 = url1.split('/')[-1] or "url_image1"
                
                print(f"📥 Downloading from URL 2: {url2}")
                response2 = await client.get(url2)
                response2.raise_for_status()
                contents2 = response2.content
                filename2 = url2.split('/')[-1] or "url_image2"
            except Exception as e:
                return {"error": f"Failed to download images: {str(e)}"}
    else:
        return {"error": "Please provide either 2 files or 2 URLs"}
    
    print(f"\n📸 Processing images: {filename1} vs {filename2}")
    
    # Extract embeddings
    print("Image 1:")
    emb1 = extract_embedding(contents1, yolo_model, reid_model, sam_predictor)
    
    print("Image 2:")
    emb2 = extract_embedding(contents2, yolo_model, reid_model, sam_predictor)
    
    # Calculate similarity
    similarity = F.cosine_similarity(
        emb1.unsqueeze(0),
        emb2.unsqueeze(0)
    ).item()
    
    print(f"✓ Similarity score: {similarity:.4f}\n")

    return {
        "similarity": similarity,
        "same_jaguar": similarity >= 0.75,
        "confidence": abs(similarity - 0.75) / 0.25  # Distance from threshold
    }

