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

from config import CORS_ORIGINS, DEVICE
from models import load_stage1_model, load_stage2_model, load_stage3_model
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

# Initialize models as None (lazy loading)
print("\n" + "="*70)
print("JAGUAR RE-ID SYSTEM - SERVER STARTING")
print("="*70)
print("Models will be loaded on first request to reduce startup time")
print("="*70 + "\n")

animal_filter = None
stage1_model = None
stage2_model = None
stage3_model = None
db = None
models_loaded = False

def ensure_models_loaded():
    """Lazy load models on first request"""
    global animal_filter, stage1_model, stage2_model, stage3_model, db, models_loaded
    
    if models_loaded:
        return
    
    print("\n" + "="*70)
    print("LOADING MODELS (First Request - This may take a few minutes on CPU)")
    print("="*70)
    
    # Initialize Stage 0 (Animal Filter)
    print("Loading Stage 0 (Animal vs Non-Animal Filter)...")
    animal_filter = AnimalFilter(device='cpu')
    animal_filter.initialize()
    print("[OK] Stage 0 model loaded on cpu")
    
    print("Loading Stage 1 (BigCat Filter)...")
    stage1_model = load_stage1_model()
    print("[OK] Stage 1 model loaded")
    
    print("Loading Stage 2 (Species Classifier)...")
    stage2_model = load_stage2_model()
    print("[OK] Stage 2 model loaded")
    
    print("Loading Stage 3 (Jaguar Re-ID)...")
    stage3_model = load_stage3_model()
    print("[OK] Stage 3 model loaded")
    
    # Initialize database
    try:
        db = get_database()
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[WARNING] Database initialization failed: {e}")
        db = None
    
    models_loaded = True
    print("\n" + "="*70)
    print("ALL MODELS LOADED - SYSTEM READY!")
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
        "status": "healthy" if models_loaded else "starting",
        "models": {
            "stage0": "loaded" if animal_filter else "not_loaded",
            "stage1": "loaded" if stage1_model else "not_loaded",
            "stage2": "loaded" if stage2_model else "not_loaded",
            "stage3": "loaded" if stage3_model else "not_loaded"
        },
        "system": "Three-Stage Wildlife Classification + Jaguar Re-ID"
    }


@app.get("/jaguars")
def get_jaguars():
    """Get all jaguars from database"""
    ensure_models_loaded()
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
    ensure_models_loaded()
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
    ensure_models_loaded()
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
    # Lazy load models on first request
    ensure_models_loaded()
    
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
            result = classify_video(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db, max_duration=30)
        else:
            print("[Detector] Input type: IMAGE")
            result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db)
        
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
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db)
        
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
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db)
        
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
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db)
        
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


@app.post("/suggest-names")
async def suggest_jaguar_names(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None)
):
    """
    Generate AI-powered name suggestions for a jaguar.
    
    Returns creative name suggestions based on spotted patterns, 
    geographical regions, and cultural significance.
    """
    import random
    from datetime import datetime
    
    # Base name categories with suggestions
    nature_names = [
        ("Luna", "Moon", "Named after the moon, symbolizing nocturnal hunting"),
        ("Sol", "Sun", "Representing the golden spotted coat"),
        ("Rio", "River", "For jaguars found near waterways"),
        ("Sierra", "Mountain", "From mountain ranges"),
        ("Storm", "Weather", "For powerful and fierce jaguars"),
        ("Shadow", "Nature", "Symbolizing stealth and camouflage"),
        ("Blaze", "Fire", "For jaguars with distinctive bright patterns"),
        ("Thunder", "Weather", "Representing power and strength"),
    ]
    
    indigenous_names = [
        ("Itzamná", "Mayan", "Ancient Mayan deity associated with jaguars"),
        ("Balam", "Mayan", "Means 'jaguar' in Mayan"),
        ("Ix Chel", "Mayan", "Goddess associated with jaguars"),
        ("Tepeyollotl", "Aztec", "Earth deity symbolized by jaguar"),
        ("Yaguareté", "Guaraní", "Traditional indigenous name for jaguar"),
        ("Kukulkan", "Mayan", "Feathered serpent deity"),
    ]
    
    personality_names = [
        ("Phoenix", "Rebirth", "For resilient jaguars"),
        ("Ranger", "Explorer", "For jaguars with large territories"),
        ("Sage", "Wisdom", "For older, experienced jaguars"),
        ("Mystique", "Mystery", "For elusive individuals"),
        ("Valor", "Courage", "For bold jaguars"),
        ("Onyx", "Gemstone", "For dark-spotted jaguars"),
        ("Amber", "Gemstone", "For golden-coated jaguars"),
    ]
    
    # Combine and randomly select
    all_names = nature_names + indigenous_names + personality_names
    random.shuffle(all_names)
    
    # Select 6 diverse suggestions
    suggestions = []
    used_categories = set()
    
    for name, category, description in all_names:
        if len(suggestions) < 6:
            # Try to diversify categories
            if category not in used_categories or len(suggestions) >= 3:
                suggestions.append({
                    "name": name,
                    "category": category,
                    "description": description
                })
                used_categories.add(category)
    
    # If we have file/image, extract metadata
    image_metadata = {}
    if file:
        try:
            from PIL import Image
            import io
            file_bytes = await file.read()
            image = Image.open(io.BytesIO(file_bytes))
            image_metadata = {
                "width": image.width,
                "height": image.height,
                "format": image.format
            }
        except:
            pass
    
    return {
        "suggestions": suggestions,
        "image_metadata": image_metadata
    }


@app.post("/register")
async def register_jaguar(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    jaguar_name: Optional[str] = Form(None)
):
    """
    Register a new jaguar in the database.
    
    Validates that the image contains a jaguar, extracts facial embedding,
    and stores in database with the provided name.
    
    Args:
        file: Image file upload (optional if image_url provided)
        image_url: URL to image (optional if file provided)
        jaguar_name: Name for the jaguar (required)
    
    Returns:
        JSON with success status, message, and jaguar_id
    """
    # Lazy load models on first request
    ensure_models_loaded()
    
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    if not jaguar_name or not jaguar_name.strip():
        raise HTTPException(status_code=400, detail="jaguar_name is required")
    
    jaguar_name = jaguar_name.strip()
    
    # Get file from upload or URL
    file_bytes = None
    
    if file:
        file_bytes = await file.read()
    elif image_url:
        # Download from URL
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            }
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(image_url, headers=headers)
                response.raise_for_status()
                file_bytes = response.content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Please provide either a file or image_url")
    
    if not file_bytes:
        raise HTTPException(status_code=400, detail="No file data received")
    
    try:
        # Detect if input is video or image
        is_video = False
        image_bytes = None
        
        # Try to determine file type
        if file and file.filename:
            ext = file.filename.lower().split('.')[-1]
            if ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
                is_video = True
        
        # If it's a video, extract middle frame
        if is_video:
            print(f"[Registration] Detected video input, extracting frame...")
            import tempfile
            import os
            
            # Save video to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            try:
                from preprocessing import extract_video_frames
                # Extract just one frame from the middle
                frames = extract_video_frames(tmp_path, frame_interval=999999, max_duration=30)  # Large interval = 1 frame
                
                if not frames:
                    raise HTTPException(status_code=400, detail="Failed to extract frame from video")
                
                # Convert first frame (PIL Image) to bytes
                import io
                img_byte_arr = io.BytesIO()
                frames[0].save(img_byte_arr, format='JPEG')
                image_bytes = img_byte_arr.getvalue()
                
                print(f"[Registration] Extracted frame from video ({len(image_bytes)} bytes)")
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        else:
            # It's an image, use directly
            image_bytes = file_bytes
        
        # Step 1: Validate it's a jaguar (without auto-registration)
        result = classify_image(image_bytes, animal_filter, stage1_model, stage2_model, stage3_model=None, db=None)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Classification failed'))
        
        # Check if it's really a jaguar
        species = result.get('final_species', '')
        if species != 'jaguar':
            raise HTTPException(
                status_code=400,
                detail=f"File does not contain a jaguar. Detected: {species}"
            )
        
        # Step 2: Extract jaguar embedding
        from jaguar_reid import extract_jaguar_embedding
        import uuid
        from datetime import datetime
        
        embedding = extract_jaguar_embedding(image_bytes, stage3_model, device=str(DEVICE))
        
        # Step 3: Check if jaguar already exists with this name
        existing_jaguars = db.list_jaguars()
        for jag in existing_jaguars:
            if jag.get('name', '').lower() == jaguar_name.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"A jaguar with the name '{jaguar_name}' already exists"
                )
        
        # Step 4: Generate unique ID and register
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        jaguar_id = f"jaguar_{timestamp}"
        
        success = db.register_jaguar(
            jaguar_id=jaguar_id,
            name=jaguar_name,
            embedding=embedding.tolist(),
            image_url=None,
            local_path=None
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register jaguar in database")
        
        print(f"[Registration] Successfully registered: {jaguar_name} (ID: {jaguar_id})")
        
        return {
            "success": True,
            "message": f"Successfully registered jaguar: {jaguar_name}",
            "jaguar_id": jaguar_id,
            "jaguar_name": jaguar_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


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
