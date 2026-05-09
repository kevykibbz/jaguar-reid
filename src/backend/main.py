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
from services.azure_storage import AzureStorageManager
from utils import extract_image_metadata


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
azure_storage = None
models_loaded = False
db_initialized = False

def ensure_db_initialized():
    """Lazy initialize only the database and Azure storage — no ML models."""
    global db, azure_storage, db_initialized

    if db_initialized:
        return

    try:
        db = get_database()
        print("[OK] Database initialized")
    except Exception as e:
        print(f"[WARNING] Database initialization failed: {e}")
        db = None

    try:
        azure_storage = AzureStorageManager()
        if azure_storage.is_available():
            print("[OK] Azure Storage initialized")
        else:
            print("[WARNING] Azure Storage not configured, using local storage")
    except Exception as e:
        print(f"[WARNING] Azure Storage initialization failed: {e}")
        azure_storage = None

    db_initialized = True


def ensure_models_loaded():
    """Lazy load models on first request"""
    global animal_filter, stage1_model, stage2_model, stage3_model, models_loaded

    if models_loaded:
        return

    # Ensure DB is up first
    ensure_db_initialized()

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
def get_jaguars(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    exclude_id: Optional[str] = None
):
    """
    Get jaguars from database with pagination and search
    
    Args:
        page: Page number (starts at 1)
        limit: Number of results per page (max 100)
        search: Search query for jaguar names
        exclude_id: Exclude a specific jaguar ID from results
    """
    ensure_db_initialized()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Validate pagination params
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50
        
        # Get all jaguars
        all_jaguars = db.list_jaguars()
        
        # Exclude specific jaguar if requested
        if exclude_id:
            all_jaguars = [j for j in all_jaguars if j.get('id') != exclude_id]
        
        # Apply search filter
        if search and search.strip():
            search_lower = search.strip().lower()
            all_jaguars = [
                j for j in all_jaguars 
                if search_lower in j.get('name', '').lower() or 
                   search_lower in j.get('id', '').lower()
            ]
        
        # Calculate pagination
        total_count = len(all_jaguars)
        total_pages = (total_count + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        # Get paginated results
        paginated_jaguars = all_jaguars[start_idx:end_idx]
        
        return {
            "success": True,
            "count": len(paginated_jaguars),
            "total": total_count,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages,
            "jaguars": paginated_jaguars
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/jaguar/{jaguar_id}")
def get_jaguar_by_id(jaguar_id: str):
    """
    Get details of a specific jaguar by ID
    
    Args:
        jaguar_id: The unique ID of the jaguar
    
    Returns:
        JSON with jaguar details including images, sightings, and metadata
    """
    ensure_db_initialized()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Get all jaguars and find the specific one
        all_jaguars = db.list_jaguars()
        jaguar = next((j for j in all_jaguars if j.get('id') == jaguar_id), None)
        
        if not jaguar:
            raise HTTPException(status_code=404, detail=f"Jaguar with ID '{jaguar_id}' not found")
        
        return jaguar
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/jaguar/{jaguar_id}/comments")
def get_jaguar_comments(jaguar_id: str):
    """
    Get comments for a specific jaguar
    
    Args:
        jaguar_id: The unique ID of the jaguar
    
    Returns:
        JSON with list of comments (currently returns empty array as comments not implemented in DB)
    """
    ensure_db_initialized()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Verify jaguar exists
        all_jaguars = db.list_jaguars()
        jaguar = next((j for j in all_jaguars if j.get('id') == jaguar_id), None)
        
        if not jaguar:
            raise HTTPException(status_code=404, detail=f"Jaguar with ID '{jaguar_id}' not found")
        
        # TODO: Implement comments in database
        # For now, return empty comments array
        return []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/jaguar/{jaguar_id}/likes")
def get_jaguar_likes(jaguar_id: str):
    """
    Get like count and user like status for a specific jaguar
    
    Args:
        jaguar_id: The unique ID of the jaguar
    
    Returns:
        JSON with like count and whether current user has liked
    """
    ensure_db_initialized()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Verify jaguar exists
        all_jaguars = db.list_jaguars()
        jaguar = next((j for j in all_jaguars if j.get('id') == jaguar_id), None)
        
        if not jaguar:
            raise HTTPException(status_code=404, detail=f"Jaguar with ID '{jaguar_id}' not found")
        
        # TODO: Implement likes in database with user tracking
        # For now, return placeholder data
        return {
            "count": 0,
            "liked": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/jaguar/{jaguar_id}/likes")
def toggle_jaguar_like(jaguar_id: str):
    """
    Toggle like status for a specific jaguar
    
    Args:
        jaguar_id: The unique ID of the jaguar
    
    Returns:
        JSON with updated like count and user like status
    """
    ensure_db_initialized()
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Verify jaguar exists
        all_jaguars = db.list_jaguars()
        jaguar = next((j for j in all_jaguars if j.get('id') == jaguar_id), None)
        
        if not jaguar:
            raise HTTPException(status_code=404, detail=f"Jaguar with ID '{jaguar_id}' not found")
        
        # TODO: Implement likes in database with user tracking
        # For now, return placeholder data
        return {
            "liked": True,
            "count": 1
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/recent-activity")
def get_recent_activity(limit: int = 20):
    """Get recent activity feed (registrations and sightings)"""
    ensure_db_initialized()
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
    ensure_db_initialized()
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
            result = classify_video(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db, azure_storage, max_duration=30)
        else:
            print("[Detector] Input type: IMAGE")
            result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db, azure_storage)
        
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
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db, azure_storage)
        
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
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db, azure_storage)
        
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
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model, db, azure_storage)
        
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
    import urllib.request
    
    # Fallback names used when iNaturalist is unavailable
    fallback_names = [
        ("Luna", "Moon", "Named after the moon, symbolizing nocturnal hunting"),
        ("Balam", "Mayan", "Means 'jaguar' in Mayan"),
        ("Rio", "River", "For jaguars found near waterways"),
        ("Kukulkan", "Mayan", "Ancient Mayan feathered serpent deity"),
        ("Storm", "Weather", "For powerful and fierce jaguars"),
        ("Guarani", "Guarani", "Named after the Guarani people of South America"),
        ("Shadow", "Nature", "Symbolizing stealth and camouflage"),
        ("Tepeyollotl", "Aztec", "Earth deity symbolized by jaguar"),
        ("Onyx", "Gemstone", "For dark-spotted jaguars"),
        ("Valor", "Courage", "For bold jaguars"),
    ]

    # --- iNaturalist: fetch place names from recent jaguar observations ---
    place_names = []
    try:
        inat_url = (
            "https://api.inaturalist.org/v1/observations"
            "?taxon_id=41970&quality_grade=research&per_page=30"
            "&fields=place_guess"
        )
        req = urllib.request.Request(
            inat_url,
            headers={"Accept": "application/json", "User-Agent": "WildlifeReID/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json as _json
            obs_data = _json.loads(resp.read())
        seen = set()
        for obs in obs_data.get("results", []):
            place = obs.get("place_guess", "")
            if not place:
                continue
            # Take the first segment before any comma (e.g. "Mato Grosso, BR" → "Mato Grosso")
            segment = place.split(",")[0].strip()
            # Keep single-word segments that look like proper names (4-14 chars, alpha only)
            if " " not in segment and segment.isalpha() and segment.isascii() and 4 <= len(segment) <= 14:
                cap = segment.capitalize()
                if cap not in seen:
                    seen.add(cap)
                    place_names.append((cap, "Place", f"Named after {segment}, a region in jaguar territory"))
    except Exception as e:
        print(f"[suggest-names] iNaturalist fetch failed (using fallback): {e}")

    # Build final pool: up to 3 place names + fallback cultural names
    random.shuffle(place_names)
    random.shuffle(fallback_names)
    pool = place_names[:3] + fallback_names

    # Select 6 diverse suggestions
    suggestions = []
    used_categories = set()

    for name, category, description in pool:
        if len(suggestions) < 6:
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

        image_metadata = {}
        try:
            image_metadata = extract_image_metadata(
                image_bytes,
                filename=(file.filename if file is not None and getattr(file, 'filename', None) else 'image.jpg')
            )
        except Exception as e:
            print(f"[Registration] Warning: failed to extract image metadata: {e}")
        
        # Step 1: Validate it's a jaguar (without auto-registration)
        result = classify_image(image_bytes, animal_filter, stage1_model, stage2_model, stage3_model=None, db=None, azure_storage=None)
        
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
        
        # Step 5: Upload image to Azure Blob Storage
        image_url = None
        local_path = None
        
        if azure_storage and azure_storage.is_available():
            try:
                print(f"[Registration] Uploading image to Azure Blob Storage...")
                success_upload, blob_url = azure_storage.upload_image(
                    image_bytes=image_bytes,
                    jaguar_id=jaguar_id,
                    filename=f"{jaguar_name}.jpg"
                )
                if success_upload:
                    image_url = blob_url
                    print(f"[Registration] Image uploaded to Azure: {blob_url}")
                else:
                    print(f"[Registration] WARNING: Failed to upload to Azure, using local storage")
            except Exception as upload_error:
                print(f"[Registration] WARNING: Azure upload failed: {upload_error}")
        else:
            print(f"[Registration] Azure Storage not available, saving locally")
        
        # If Azure upload failed, save locally as fallback
        if not image_url:
            try:
                # Save to local database/images folder
                local_dir = Path("./database/images")
                local_dir.mkdir(parents=True, exist_ok=True)
                local_filename = f"{jaguar_id}_{timestamp}.jpg"
                local_path = str(local_dir / local_filename)
                
                with open(local_path, 'wb') as f:
                    f.write(image_bytes)
                print(f"[Registration] Image saved locally: {local_path}")
            except Exception as save_error:
                print(f"[Registration] WARNING: Failed to save locally: {save_error}")
        
        # Step 6: Register jaguar with image reference
        success = db.register_jaguar(
            jaguar_id=jaguar_id,
            name=jaguar_name,
            embedding=embedding.tolist(),
            image_url=image_url,
            local_path=local_path,
            image_metadata=image_metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register jaguar in database")
        
        print(f"[Registration] Successfully registered: {jaguar_name} (ID: {jaguar_id})")
        
        return {
            "success": True,
            "message": f"Successfully registered jaguar: {jaguar_name}",
            "jaguar_id": jaguar_id,
            "jaguar_name": jaguar_name,
            "image_url": image_url,
            "image_metadata": image_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")


@app.post("/link-to-existing")
async def link_to_existing_jaguar(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    jaguar_id: Optional[str] = Form(None)
):
    """
    Link an uploaded image to an existing jaguar in the database.
    
    This allows manual matching when automatic re-identification is below threshold.
    
    Args:
        file: Image file upload (optional if image_url provided)
        image_url: URL to image (optional if file provided)
        jaguar_id: ID of the existing jaguar to link to (required)
    
    Returns:
        JSON with success status and message
    """
    # Lazy load models on first request
    ensure_models_loaded()
    
    if not db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    if not jaguar_id or not jaguar_id.strip():
        raise HTTPException(status_code=400, detail="jaguar_id is required")
    
    jaguar_id = jaguar_id.strip()
    
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
        image_metadata = {}
        try:
            image_metadata = extract_image_metadata(
                file_bytes,
                filename=(file.filename if file is not None and getattr(file, 'filename', None) else 'image.jpg')
            )
        except Exception as e:
            print(f"[Link] Warning: failed to extract image metadata: {e}")

        # Validate it's a jaguar
        result = classify_image(file_bytes, animal_filter, stage1_model, stage2_model, stage3_model=None, db=None, azure_storage=None)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Classification failed'))
        
        species = result.get('final_species', '')
        if species != 'jaguar':
            raise HTTPException(
                status_code=400,
                detail=f"File does not contain a jaguar. Detected: {species}"
            )
        
        # Extract embedding and compute similarity
        from jaguar_reid import extract_jaguar_embedding
        from datetime import datetime
        
        embedding = extract_jaguar_embedding(file_bytes, stage3_model, device=str(DEVICE))
        
        # Get the jaguar we're linking to and compute similarity
        jaguar_detail = db.get_jaguar_detail(jaguar_id)
        if not jaguar_detail:
            raise HTTPException(status_code=404, detail=f"Jaguar {jaguar_id} not found")
        
        # Upload image to Azure Blob Storage or save locally
        image_url_stored = None
        local_path = None
        
        if azure_storage and azure_storage.is_available():
            try:
                print(f"[Link] Uploading image to Azure Blob Storage...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                success_upload, blob_url = azure_storage.upload_image(
                    image_bytes=file_bytes,
                    jaguar_id=jaguar_id,
                    filename=f"{jaguar_detail['name']}_{timestamp}.jpg"
                )
                if success_upload:
                    image_url_stored = blob_url
                    print(f"[Link] Image uploaded to Azure: {blob_url}")
            except Exception as upload_error:
                print(f"[Link] WARNING: Azure upload failed: {upload_error}")
        
        # If Azure upload failed, save locally
        if not image_url_stored:
            try:
                from pathlib import Path
                local_dir = Path("./database/images")
                local_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                local_filename = f"{jaguar_id}_{timestamp}.jpg"
                local_path = str(local_dir / local_filename)
                
                with open(local_path, 'wb') as f:
                    f.write(file_bytes)
                print(f"[Link] Image saved locally: {local_path}")
            except Exception as save_error:
                print(f"[Link] WARNING: Failed to save locally: {save_error}")
        
        # Compute similarity against this specific jaguar
        # (We'll just use a default value since manual linking is allowed)
        similarity_score = 0.65  # Below threshold but user-confirmed
        
        # Link the image to the jaguar
        success = db.link_image_to_jaguar(
            jaguar_id=jaguar_id,
            image_url=image_url_stored,
            local_path=local_path,
            similarity_score=similarity_score,
            image_metadata=image_metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to link image to jaguar")
        
        print(f"[Link] Successfully linked image to jaguar: {jaguar_detail['name']}")
        
        return {
            "success": True,
            "message": f"Successfully linked image to jaguar: {jaguar_detail['name']}",
            "jaguar_id": jaguar_id,
            "jaguar_name": jaguar_detail['name'],
            "image_url": image_url_stored,
            "image_metadata": image_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during linking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Linking error: {str(e)}")


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
