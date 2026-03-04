"""
FastAPI Backend for Three-Stage Wildlife Classification System

Architecture:
- Stage 0: Animal Filter (Vision Transformer)
- Stage 1: BigCat Binary Filter (EfficientNet-B2)
- Stage 2: Species Classifier (EfficientNet-B2)

Endpoints:
- POST /classify: Classify an image through all three stages
- GET /health: Health check
- GET /: Root endpoint
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
from pathlib import Path

from config import CORS_ORIGINS
from models import load_stage1_model, load_stage2_model
from animal_filter import AnimalFilter
from preprocessing import classify_image, classify_video
from database.database_manager import get_database


# Request model for JSON input
class ClassifyRequest(BaseModel):
    image_url: str

# Initialize FastAPI app
app = FastAPI(
    title="Wildlife Classification API",
    description="Three-stage image classification system (Animal filter + BigCat filter + Species ID)",
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
print("\n" + "="*70)
print("INITIALIZING THREE-STAGE WILDLIFE CLASSIFICATION SYSTEM")
print("="*70)

animal_filter = AnimalFilter(device='cpu')
stage1_model = load_stage1_model()
stage2_model = load_stage2_model()

# Initialize database
try:
    db = get_database()
    print("✓ Database initialized")
except Exception as e:
    print(f"⚠️  Database initialization failed: {e}")
    db = None

print("\n" + "="*70)
print("🚀 SYSTEM READY!")
print("="*70)
print(f"📡 Backend running on: http://localhost:8000")
print(f"📚 API docs at: http://localhost:8000/docs")
print("="*70 + "\n")


@app.get("/")
def read_root():
    """Root endpoint - system info"""
    return {
        "message": "Wildlife Classification API",
        "system": "Three-Stage Pipeline (Stage 0: Animal Filter, Stage 1: BigCat Filter, Stage 2: Species)",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models": {
            "stage0": "loaded",
            "stage1": "loaded",
            "stage2": "loaded"
        },
        "system": "Three-Stage Wildlife Classification"
    }


@app.get("/jaguars")
def get_jaguars():
    """Get all jaguars from database"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        jaguars = db.list_jaguars()
        return {
            "success": True,
            "count": len(jaguars),
            "jaguars": jaguars
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/recent-activity")
def get_recent_activity(limit: int = 20):
    """Get recent activity feed (registrations and sightings)"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        activity = db.get_recent_activity(limit=limit)
        return {
            "success": True,
            "count": len(activity),
            "activity": activity
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/statistics")
def get_statistics():
    """Get database statistics"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        stats = db.get_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/classify")
async def classify(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None)
):
    """
    Classify an image or video through the three-stage pipeline.
    
    Stage 0: Animal Filter - Verify contains animal
    Stage 1: BigCat Filter - Detect if contains BigCat
    Stage 2: Species Identification - Identify which species
    
    Supported Input:
    - Images: JPG, PNG, BMP (any size)
    - Videos: MP4, MOV, AVI (max 30 seconds)
    
    Accepts both JSON and form-data:
    - JSON: {"image_url": "https://..."}
    - Form-data: file=<upload> or image_url=<url>
    
    Args:
        file: Image/Video file upload (optional if image_url provided)
        image_url: URL to image/video (optional if file provided)
    
    Returns:
        JSON with classification results from all stages
    """
    import io
    
    file_bytes = None
    file_name = ""
    
    # Check if request is JSON
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            json_data = await request.json()
            image_url = json_data.get("image_url")
        except:
            pass
    
    # Get file from upload or URL
    if file:
        file_bytes = await file.read()
        file_name = file.filename or "unknown"
        print(f"\nProcessing file: {file_name}")
    elif image_url:
        # Download from URL with proper headers to avoid 403 Forbidden
        try:
            print(f"\nDownloading from URL: {image_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com/',
            }
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(image_url, headers=headers)
                response.raise_for_status()
                file_bytes = response.content
                file_name = image_url.split('/')[-1].split('?')[0] or "image"
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download from URL: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a file or image_url"
        )
    
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="No file data received"
        )
    
    try:
        # Detect input type (image vs video)
        is_video = False
        
        # Check file extension
        if file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            is_video = True
        else:
            # Try to detect from first few bytes
            try:
                from PIL import Image as PILImage
                img = PILImage.open(io.BytesIO(file_bytes))
                img.verify() # Verify if it's a valid image
                is_video = False
            except Exception as e:
                # If PIL fails, check if it's a known image extension. If so, treat as image, else assume video.
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                    is_video = False
                    print(f"[Detector] WARNING: PIL verification failed for image, but file extension indicates image. Error: {e}")
                else:
                    is_video = True
        
        # Run appropriate classification
        if is_video:
            print("[Detector] Input type: VIDEO (max 30 seconds)")
            result = classify_video(file_bytes, animal_filter, stage1_model, stage2_model, max_duration=30)
        else:
            print("[Detector] Input type: IMAGE")
            result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Classification failed')
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Classification error: {str(e)}"
        )


@app.post("/predict")
async def predict(
    request: Request,
    files: Optional[list] = File(None),
    url1: Optional[str] = Form(None),
    url2: Optional[str] = Form(None)
):
    """
    Alternative endpoint for compatibility.
    For single image classification, use /classify instead.
    """
    return await classify(request=request, file=files[0] if files else None)


@app.post("/predict/url")
async def predict_from_url(request: Request):
    """
    Predict from image URL (JSON input)
    
    Request body:
    {
        "image_url": "https://...",
        "return_all_scores": true (optional)
    }
    """
    try:
        json_data = await request.json()
        image_url = json_data.get("image_url")
        
        if not image_url:
            raise HTTPException(status_code=422, detail="image_url is required")
        
        # Download from URL with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(image_url, headers=headers)
            response.raise_for_status()
            file_bytes = response.content
        
        # Classify
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Classification failed'))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/predict/binary")
async def predict_binary(request: Request):
    """
    Stage 1 Binary Classification only (BigCat vs NotBigCat)
    
    Request body:
    {
        "image_url": "https://..."
    }
    """
    try:
        json_data = await request.json()
        image_url = json_data.get("image_url")
        
        if not image_url:
            raise HTTPException(status_code=422, detail="image_url is required")
        
        # Download from URL with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(image_url, headers=headers)
            response.raise_for_status()
            file_bytes = response.content
        
        # Classify - full pipeline but we'll return only stage1
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Classification failed'))
        
        # Return only Stage 1 result
        return {
            "prediction": result.get("stage1", {}).get("prediction"),
            "confidence": result.get("stage1", {}).get("confidence"),
            "scores": result.get("stage1", {}).get("scores")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/predict/species")
async def predict_species(request: Request):
    """
    Stage 2 Species Classification only (assumes BigCat already detected)
    
    Request body:
    {
        "image_url": "https://..."
    }
    """
    try:
        json_data = await request.json()
        image_url = json_data.get("image_url")
        
        if not image_url:
            raise HTTPException(status_code=422, detail="image_url is required")
        
        # Download from URL with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(image_url, headers=headers)
            response.raise_for_status()
            file_bytes = response.content
        
        # Classify - full pipeline but we'll return only stage2
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Classification failed'))
        
        # Return only Stage 2 result
        return {
            "prediction": result.get("stage2", {}).get("prediction"),
            "confidence": result.get("stage2", {}).get("confidence"),
            "scores": result.get("stage2", {}).get("scores")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("⚠️  WARNING: Use 'python start_dev.py' for development")
    print("   This will exclude test files from triggering reloads")
    print("="*70 + "\n")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload when running directly
    )
