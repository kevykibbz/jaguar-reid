"""
Three-Stage Image/Video Classification Pipeline

Pipeline:
0. Load and preprocess image/video
   - Validate video length <= 30 seconds
   - Extract frames from video (every 15th frame)
1. Stage 0: Animal Filter (Vision Transformer)
   - If Not Animal: Reject 
   - If Animal: Continue to Stage 1
2. Stage 1: Binary filter (BigCat vs NotBigCat)
   - If NotBigCat: Reject
   - If BigCat: Continue to Stage 2
3. Stage 2: Species classifier
   - Classify species: Jaguar, Leopard, Tiger, Lion, or Cheetah
4. Return classification results with confidence scores
"""
import io
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
from config import (
    DEVICE,
    IMAGE_SIZE,
    STAGE1_CONFIDENCE_THRESHOLD,
    STAGE2_CONFIDENCE_THRESHOLD,
    STAGE2_CLASSES
)

# Image preprocessing transform
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def validate_video_duration(file_path_or_bytes, max_duration=30):
    """
    Validate video duration is within limit (default: <=30 seconds)
    
    Args:
        file_path_or_bytes: Path to video file or bytes
        max_duration: Maximum allowed duration in seconds
    
    Returns:
        dict with:
            - valid: bool (True if video length <= max_duration)
            - duration: float (video duration in seconds)
            - fps: float (frames per second)
            - frame_count: int (total frames)
            - error: str (error message if invalid)
    """
    try:
        # Handle both file paths and bytes
        if isinstance(file_path_or_bytes, bytes):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(file_path_or_bytes)
                tmp_path = tmp.name
            cap = cv2.VideoCapture(tmp_path)
        else:
            cap = cv2.VideoCapture(str(file_path_or_bytes))
        
        if not cap.isOpened():
            return {
                'valid': False,
                'duration': 0,
                'fps': 0,
                'frame_count': 0,
                'error': 'Failed to open video file'
            }
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        # Validate duration
        is_valid = duration <= max_duration
        
        if not is_valid:
            error_msg = f"Video duration {duration:.1f}s exceeds maximum {max_duration}s"
        else:
            error_msg = None
        
        print(f"[VideoValidator] Duration: {duration:.1f}s, FPS: {fps:.1f}, Frames: {frame_count}")
        
        return {
            'valid': is_valid,
            'duration': duration,
            'fps': fps,
            'frame_count': frame_count,
            'error': error_msg
        }
    
    except Exception as e:
        return {
            'valid': False,
            'duration': 0,
            'fps': 0,
            'frame_count': 0,
            'error': str(e)
        }


def extract_video_frames(file_path_or_bytes, frame_interval=15):
    """
    Extract frames from video file
    
    Args:
        file_path_or_bytes: Path to video or video bytes
        frame_interval: Extract every nth frame (15 = ~2fps at 30fps)
    
    Returns:
        list of PIL Image objects
    """
    frames = []
    
    try:
        # Handle both file paths and bytes
        if isinstance(file_path_or_bytes, bytes):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(file_path_or_bytes)
                tmp_path = tmp.name
            cap = cv2.VideoCapture(tmp_path)
        else:
            cap = cv2.VideoCapture(str(file_path_or_bytes))
        
        if not cap.isOpened():
            raise ValueError("Failed to open video file")
        
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        
        print(f"[VideoExtractor] Extracted {extracted_count} frames from {frame_count} total frames")
        
        return frames
    
    except Exception as e:
        print(f"[VideoExtractor] Error: {e}")
        return []


def classify_video_frames(frames, animal_filter):
    """
    Classify if video contains animals using sampled frames
    Uses majority voting across frames
    
    Args:
        frames: List of PIL Image objects
        animal_filter: Loaded AnimalFilter instance
    
    Returns:
        dict with aggregated results
    """
    if not frames:
        return {'is_animal': False, 'animal_frames': 0, 'total_frames': 0}
    
    animal_count = 0
    
    for i, frame in enumerate(frames):
        result = animal_filter.classify(frame)
        if result['is_animal']:
            animal_count += 1
    
    is_animal = (animal_count / len(frames)) > 0.3  # 30% threshold
    
    print(f"[VideoAnimalClassifier] {animal_count}/{len(frames)} frames detected as animal ({(animal_count/len(frames))*100:.1f}%)")
    
    return {
        'is_animal': is_animal,
        'animal_frames': animal_count,
        'total_frames': len(frames),
        'animal_ratio': animal_count / len(frames)
    }


def classify_video_bigcat(frames, stage1_model):
    """
    Classify if video contains BigCats using sampled frames
    Uses aggregation across frames
    
    Args:
        frames: List of PIL Image objects
        stage1_model: Loaded Stage 1 model
    
    Returns:
        dict with aggregated results
    """
    if not frames:
        return {'is_bigcat': False, 'bigcat_frames': 0, 'total_frames': 0}
    
    bigcat_count = 0
    confidences = []
    
    for frame in frames:
        # Preprocess frame
        image_tensor = transform(frame).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            output = stage1_model(image_tensor)
            probs = F.softmax(output, dim=1)
        
        bigcat_conf = probs[0, 0].item()
        confidences.append(bigcat_conf)
        
        if bigcat_conf >= STAGE1_CONFIDENCE_THRESHOLD:
            bigcat_count += 1
    
    is_bigcat = (bigcat_count / len(frames)) > 0.3  # 30% threshold
    avg_confidence = np.mean(confidences)
    
    print(f"[VideoBigCatClassifier] {bigcat_count}/{len(frames)} frames detected BigCat ({(bigcat_count/len(frames))*100:.1f}%)")
    
    return {
        'is_bigcat': is_bigcat,
        'bigcat_frames': bigcat_count,
        'total_frames': len(frames),
        'bigcat_ratio': bigcat_count / len(frames),
        'avg_confidence': avg_confidence
    }


def classify_video_species(frames, stage2_model):
    """
    Classify species in video using sampled frames
    Uses majority voting
    
    Args:
        frames: List of PIL Image objects
        stage2_model: Loaded Stage 2 model
    
    Returns:
        dict with aggregated results
    """
    if not frames:
        return {'species': 'unknown', 'confidence': 0.0, 'frame_votes': {}}
    
    species_votes = {}
    confidences = []
    
    for frame in frames:
        # Preprocess frame
        image_tensor = transform(frame).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            output = stage2_model(image_tensor)
            probs = F.softmax(output, dim=1)
        
        confidence, predicted_idx = probs.max(1)
        species_idx = predicted_idx.item()
        species_name = STAGE2_CLASSES.get(species_idx, "unknown")
        
        species_votes[species_name] = species_votes.get(species_name, 0) + 1
        confidences.append(confidence.item())
    
    # Majority vote
    final_species = max(species_votes, key=species_votes.get)
    final_confidence = np.mean(confidences)
    
    print(f"[VideoSpeciesClassifier] Species votes: {species_votes}")
    
    return {
        'species': final_species,
        'confidence': final_confidence,
        'frame_votes': species_votes
    }



def classify_animal(image_bytes, animal_filter):
    """
    Stage 0: Animal classification - is this an animal image?
    
    Args:
        image_bytes: Raw image bytes
        animal_filter: Loaded AnimalFilter instance
    
    Returns:
        dict with keys:
            - is_animal: bool (True if animal detected)
            - label: str (ImageNet label)
            - confidence: float (0-1)
    """
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    result = animal_filter.classify(image)
    
    if result['is_animal']:
        print(f"[Stage0] Result: ANIMAL - {result['label']} ({result['confidence']:.2%})")
    else:
        print(f"[Stage0] Result: NOT ANIMAL - {result['label']} ({result['confidence']:.2%})")
    
    return {
        'is_animal': result['is_animal'],
        'label': result['label'],
        'confidence': result['confidence']
    }


def classify_bigcat(image_bytes, stage1_model):
    """
    Stage 1: Binary classification - is this a big cat?
    
    Args:
        image_bytes: Raw image bytes
        stage1_model: Loaded Stage 1 model
    
    Returns:
        dict with keys:
            - is_bigcat: bool (True if BigCat detected)
            - confidence: float (0-1)
            - label: str ("BigCat" or "NotBigCat")
    """
    # Load and preprocess image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(DEVICE)
    
    # Run Stage 1 inference
    with torch.no_grad():
        stage1_output = stage1_model(image_tensor)
        stage1_probs = F.softmax(stage1_output, dim=1)
    
    # Model trained with class mapping: {'bigcat': 0, 'not_bigcat': 1}
    bigcat_confidence = stage1_probs[0, 0].item()  # Probability of BigCat (class 0)
    is_bigcat = bigcat_confidence >= STAGE1_CONFIDENCE_THRESHOLD
    
    print(f"[Stage1] Result: {'BigCat' if is_bigcat else 'NotBigCat'} ({bigcat_confidence:.2%})")
    
    return {
        'is_bigcat': is_bigcat,
        'confidence': bigcat_confidence,
        'label': 'BigCat' if is_bigcat else 'NotBigCat'
    }


def classify_species(image_bytes, stage2_model):
    """
    Stage 2: Multi-class species classification
    Only run this if Stage 1 detected a BigCat
    
    Args:
        image_bytes: Raw image bytes
        stage2_model: Loaded Stage 2 model
    
    Returns:
        dict with keys:
            - species: str (species name)
            - confidence: float (0-1)
            - all_scores: dict (confidence for each species)
    """
    # Load and preprocess image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(DEVICE)
    
    # Run Stage 2 inference
    with torch.no_grad():
        stage2_output = stage2_model(image_tensor)
        stage2_probs = F.softmax(stage2_output, dim=1)
    
    # Get predicted species
    confidence, predicted_idx = stage2_probs.max(1)
    species_idx = predicted_idx.item()
    species_name = STAGE2_CLASSES.get(species_idx, "unknown")
    confidence_score = confidence.item()
    
    # Get all species scores
    all_scores = {STAGE2_CLASSES.get(i, f"class_{i}"): float(prob) 
                  for i, prob in enumerate(stage2_probs[0])}
    
    print(f"[Stage2] Result: {species_name.title()} ({confidence_score:.2%})")
    
    return {
        'species': species_name,
        'confidence': confidence_score,
        'all_scores': all_scores
    }


def classify_image(image_bytes, animal_filter, stage1_model, stage2_model):
    """
    Complete three-stage classification pipeline for images
    
    Args:
        image_bytes: Raw image bytes
        animal_filter: Loaded AnimalFilter instance
        stage1_model: Loaded Stage 1 model (BigCat detector)
        stage2_model: Loaded Stage 2 model (Species classifier)
    
    Returns:
        dict with results from all stages or error message
    """
    try:
        # Validate image
        Image.open(io.BytesIO(image_bytes)).convert('RGB')
    except Exception as e:
        return {
            'success': False,
            'error': f"Failed to load image: {str(e)}"
        }
    
    print("\n" + "="*50)
    print("THREE-STAGE WILDLIFE CLASSIFICATION (IMAGE)")
    print("="*50)
    
    # Stage 0: Animal Filter
    stage0_result = classify_animal(image_bytes, animal_filter)
    
    if not stage0_result['is_animal']:
        print(f"[REJECT] Not an animal image")
        return {
            'success': True,
            'input_type': 'image',
            'stage0': stage0_result,
            'stage1': None,
            'stage2': None,
            'message': f"Image detected as non-animal: {stage0_result['label']} (confidence: {stage0_result['confidence']:.2%})"
        }
    
    print("[OK] Animal detected, proceeding to Stage 1...\n")
    
    # Stage 1: BigCat Binary Filter
    stage1_result = classify_bigcat(image_bytes, stage1_model)
    
    if not stage1_result['is_bigcat']:
        print(f"[REJECT] Not a BigCat")
        return {
            'success': True,
            'input_type': 'image',
            'stage0': stage0_result,
            'stage1': stage1_result,
            'stage2': None,
            'message': f"Animal detected but not a BigCat: {stage1_result['label']} (confidence: {stage1_result['confidence']:.2%})"
        }
    
    print("[OK] BigCat detected, proceeding to Stage 2...\n")
    
    # Stage 2: Species Classification
    stage2_result = classify_species(image_bytes, stage2_model)
    
    print("="*50)
    print(f"[SUCCESS] FINAL RESULT: {stage2_result['species'].upper()}")
    print("="*50 + "\n")
    
    return {
        'success': True,
        'input_type': 'image',
        'stage0': stage0_result,
        'stage1': stage1_result,
        'stage2': stage2_result,
        'final_species': stage2_result['species'],
        'final_confidence': stage2_result['confidence']
    }


def classify_video(video_bytes, animal_filter, stage1_model, stage2_model, max_duration=30):
    """
    Complete three-stage classification pipeline for videos
    
    Args:
        video_bytes: Raw video bytes
        animal_filter: Loaded AnimalFilter instance
        stage1_model: Loaded Stage 1 model (BigCat detector)
        stage2_model: Loaded Stage 2 model (Species classifier)
        max_duration: Maximum allowed video duration in seconds
    
    Returns:
        dict with results from all stages or error message
    """
    import tempfile
    
    # Save bytes to temporary file for video processing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    
    try:
        # Validate video duration
        validation = validate_video_duration(tmp_path, max_duration=max_duration)
        
        if not validation['valid']:
            return {
                'success': False,
                'error': validation['error'],
                'video_info': {
                    'duration': validation['duration'],
                    'fps': validation['fps'],
                    'frame_count': validation['frame_count']
                }
            }
        
        print("\n" + "="*50)
        print("THREE-STAGE WILDLIFE CLASSIFICATION (VIDEO)")
        print("="*50)
        print(f"Video Duration: {validation['duration']:.1f}s (max: {max_duration}s) ✓")
        
        # Extract frames
        frames = extract_video_frames(tmp_path, frame_interval=15)
        
        if not frames:
            return {
                'success': False,
                'error': 'Failed to extract frames from video'
            }
        
        print("[OK] Extracted frames, proceeding with classification...\n")
        
        # Stage 0: Animal Filter on frames
        stage0_result = classify_video_frames(frames, animal_filter)
        
        if not stage0_result['is_animal']:
            print(f"[REJECT] Video does not contain animals")
            return {
                'success': True,
                'input_type': 'video',
                'video_info': {
                    'duration': validation['duration'],
                    'fps': validation['fps'],
                    'frame_count': validation['frame_count'],
                    'extracted_frames': len(frames)
                },
                'stage0': stage0_result,
                'stage1': None,
                'stage2': None,
                'message': f"Video does not contain animals ({stage0_result['animal_ratio']:.1%} frames)"
            }
        
        print("[OK] Animal detected in video, proceeding to Stage 1...\n")
        
        # Stage 1: BigCat Filter on frames
        stage1_result = classify_video_bigcat(frames, stage1_model)
        
        if not stage1_result['is_bigcat']:
            print(f"[REJECT] Video does not contain BigCats")
            return {
                'success': True,
                'input_type': 'video',
                'video_info': {
                    'duration': validation['duration'],
                    'fps': validation['fps'],
                    'frame_count': validation['frame_count'],
                    'extracted_frames': len(frames)
                },
                'stage0': stage0_result,
                'stage1': stage1_result,
                'stage2': None,
                'message': f"Video contains animals but not BigCats ({stage1_result['bigcat_ratio']:.1%} frames)"
            }
        
        print("[OK] BigCat detected in video, proceeding to Stage 2...\n")
        
        # Stage 2: Species Classification
        stage2_result = classify_video_species(frames, stage2_model)
        
        print("="*50)
        print(f"[SUCCESS] FINAL RESULT: {stage2_result['species'].upper()}")
        print("="*50 + "\n")
        
        return {
            'success': True,
            'input_type': 'video',
            'video_info': {
                'duration': validation['duration'],
                'fps': validation['fps'],
                'frame_count': validation['frame_count'],
                'extracted_frames': len(frames)
            },
            'stage0': stage0_result,
            'stage1': stage1_result,
            'stage2': stage2_result,
            'final_species': stage2_result['species'],
            'final_confidence': stage2_result['confidence']
        }
    
    finally:
        # Clean up temporary file
        import os
        try:
            os.unlink(tmp_path)
        except:
            pass



def is_already_segmented(image_bytes):
    """
    Detect if image is already segmented/cropped.
    Checks for: transparent background, uniform background, or small size.
    
    Returns:
        bool: True if image appears to be already processed
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Check 1: Has transparency (RGBA or with alpha channel)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            print("[OK] Detected pre-segmented image (has transparency)")
            return True
        
        # Check 2: Small image size (likely already cropped)
        width, height = image.size
        if width < 500 and height < 500:
            print("[OK] Detected pre-cropped image (small dimensions)")
            return True
        
        # Check 3: Check for uniform background (already has clean background)
        img_array = np.array(image.convert('RGB'))
        # Sample border pixels
        border_pixels = np.concatenate([
            img_array[0, :].reshape(-1, 3),  # Top edge
            img_array[-1, :].reshape(-1, 3),  # Bottom edge
            img_array[:, 0].reshape(-1, 3),  # Left edge
            img_array[:, -1].reshape(-1, 3)  # Right edge
        ])
        
        # Calculate variance of border pixels
        variance = np.var(border_pixels)
        if variance < 100:  # Low variance = uniform background
            print("[OK] Detected processed image (uniform background)")
            return True
        
        return False
    except Exception as e:
        print(f"[WARNING] Error checking segmentation: {e}")
        return False


# Image transformation pipeline
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def detect_and_crop_jaguar(image_bytes, yolo_model):
    """
    Detect jaguar in image using YOLO and crop the region.
    
    Args:
        image_bytes: Raw image bytes
        yolo_model: Loaded YOLO model instance
    
    Returns:
        tuple: (PIL Image cropped, bounding box coordinates [x1, y1, x2, y2], original cv2 image, detection_info dict)
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img_cv is None:
        raise ValueError("Failed to decode image")
    
    # Run YOLO detection
    results = yolo_model(img_cv, conf=YOLO_CONFIDENCE_THRESHOLD, verbose=False)
    
    if len(results) == 0 or len(results[0].boxes) == 0:
        # No detection, return original image
        print("[WARNING] No animal detected in image")
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        h, w = img_cv.shape[:2]
        detection_info = {
            "detected": False,
            "class_id": None,
            "class_name": "none",
            "confidence": 0.0,
            "is_jaguar": False
        }
        return pil_image, [0, 0, w, h], img_cv, detection_info
    
    # Get the first detection (highest confidence)
    boxes = results[0].boxes
    box = boxes[0]
    confidence = float(box.conf[0])
    class_id = int(box.cls[0])
    
    # YOLO class names (COCO dataset)
    # Class 0 = 'person', but we're using YOLOv8n which should detect various animals
    # For wildlife: typically big cats might be detected as 'cat' (class 15) or similar
    # Since YOLOv8n is trained on general objects, it may not specifically identify jaguars
    # We'll use a heuristic: if it detects an animal-like class, proceed
    class_names = results[0].names
    class_name = class_names.get(class_id, "unknown")
    
    # Check if detected class is jaguar-compatible
    # YOLO doesn't have a specific "jaguar" class, but jaguars are big cats
    # We'll only accept "cat" class (15) as a proxy for big cats
    # Reject all other animals like zebra, dog, horse, etc.
    jaguar_compatible_classes = ['cat']  # Only accept cat class as potential jaguar
    is_jaguar = class_name.lower() in jaguar_compatible_classes
    
    print(f"[OK] Detected: {class_name} (class {class_id}) with confidence: {confidence:.2f}")
    
    detection_info = {
        "detected": True,
        "class_id": class_id,
        "class_name": class_name,
        "confidence": confidence,
        "is_jaguar": is_jaguar
    }
    
    # Get bounding box coordinates
    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
    
    # Add padding around the box
    height, width = img_cv.shape[:2]
    pad_x = int((x2 - x1) * CROP_PADDING_PERCENT)
    pad_y = int((y2 - y1) * CROP_PADDING_PERCENT)
    
    x1_pad = max(0, x1 - pad_x)
    y1_pad = max(0, y1 - pad_y)
    x2_pad = min(width, x2 + pad_x)
    y2_pad = min(height, y2 + pad_y)
    
    # Crop the image
    cropped = img_cv[y1_pad:y2_pad, x1_pad:x2_pad]
    
    # Convert back to PIL Image
    cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(cropped_rgb)
    
    return pil_image, [x1, y1, x2, y2], img_cv, detection_info


def segment_with_sam(image_bytes, yolo_model, sam_predictor):
    """
    Segment jaguar using SAM (Segment Anything Model) for precise background removal.
    
    Args:
        image_bytes: Raw image bytes
        yolo_model: Loaded YOLO model instance
        sam_predictor: Loaded SAM predictor instance
    
    Returns:
        tuple: (PIL Image: Segmented jaguar, detection_info dict)
    """
    if sam_predictor is None:
        # Fallback to bounding box crop if SAM not available
        print("[WARNING] SAM not available, using bounding box crop")
        pil_image, _, _, detection_info = detect_and_crop_jaguar(image_bytes, yolo_model)
        return pil_image, detection_info
    
    # First, detect jaguar with YOLO
    _, bbox, img_cv, detection_info = detect_and_crop_jaguar(image_bytes, yolo_model)
    
    # Convert to RGB for SAM
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    
    # Set image for SAM
    sam_predictor.set_image(img_rgb)
    
    # Use bounding box as prompt for SAM
    input_box = np.array(bbox)
    
    # Generate mask
    print("[SEGMENTATION] Generating precise segmentation mask...")
    masks, scores, _ = sam_predictor.predict(
        box=input_box,
        multimask_output=False
    )
    
    # Get the best mask
    mask = masks[0]
    print(f"[OK] Segmentation complete (score: {scores[0]:.3f})")
    
    # Ensure mask matches image dimensions
    if mask.shape != img_rgb.shape[:2]:
        mask = cv2.resize(mask.astype(np.uint8), (img_rgb.shape[1], img_rgb.shape[0]), 
                         interpolation=cv2.INTER_NEAREST).astype(bool)
    
    # Create RGBA image with transparent background
    rgba = np.dstack((img_rgb, np.zeros(img_rgb.shape[:2], dtype=np.uint8)))
    rgba[:, :, 3] = (mask * 255).astype(np.uint8)
    
    # Crop to bounding box of the mask to remove excess
    coords = np.column_stack(np.where(mask))
    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        
        # Add small padding
        pad = 10
        y_min = max(0, y_min - pad)
        x_min = max(0, x_min - pad)
        y_max = min(rgba.shape[0], y_max + pad)
        x_max = min(rgba.shape[1], x_max + pad)
        
        rgba = rgba[y_min:y_max, x_min:x_max]
    
    # Convert to PIL Image
    pil_image = Image.fromarray(rgba, mode='RGBA')
    
    # Convert RGBA to RGB with white background
    rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
    rgb_image.paste(pil_image, mask=pil_image.split()[3])
    
    return rgb_image, detection_info


def extract_embedding(image_bytes, yolo_model, reid_model, sam_predictor=None, use_sam=False, species_classifier=None):
    """
    Complete preprocessing pipeline:
    1. Check if image is already segmented
    2. Detect jaguar using YOLO (if needed)
    3. Validate species using species classifier (if available)
    4. Segment with SAM (if available and needed) or crop with bounding box
    5. Resize and normalize image
    6. Extract embedding using Re-ID model
    
    Args:
        image_bytes: Raw image bytes
        yolo_model: Loaded YOLO model instance
        reid_model: Loaded Re-ID model instance
        sam_predictor: Optional SAM predictor for precise segmentation
        use_sam: Set to True to enable SAM segmentation (default: False for speed)
        species_classifier: Optional species classifier dict with 'model', 'classes', 'transform'
    
    Returns:
        tuple: (torch.Tensor: 512-dimensional embedding vector, detection_info dict)
    """
    detection_info = {"detected": True, "is_jaguar": True, "class_name": "pre-processed", "confidence": 1.0}
    
    # Step 1: Check if already processed
    if is_already_segmented(image_bytes):
        print("[SKIP] Skipping segmentation for pre-processed image")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    else:
        # Step 2: Detect and crop jaguar using YOLO
        if use_sam and sam_predictor is not None:
            print("[SEGMENTATION] Applying SAM segmentation...")
            image, detection_info = segment_with_sam(image_bytes, yolo_model, sam_predictor)
        else:
            image, _, _, detection_info = detect_and_crop_jaguar(image_bytes, yolo_model)
        
        # Step 3: Species-level validation (if available)
        if species_classifier is not None and detection_info.get("is_jaguar", False):
            print("🔍 Running species classification...")
            from species_classifier import classify_from_pil_image
            
            species_result = classify_from_pil_image(
                image, 
                species_classifier['model'], 
                device=str(DEVICE)
            )
            print(f"✓ Species classification complete: {species_result['species']} ({species_result['confidence']:.2%})")
            
            # Merge species info into detection_info
            detection_info['species_classification'] = species_result
            
            # Override is_jaguar based on species classifier
            if not species_result['is_jaguar']:
                detection_info['is_jaguar'] = False
                detection_info['species_name'] = species_result['species']
                detection_info['species_confidence'] = species_result['confidence']
                print(f"   ⚠️  Species mismatch: {species_result['species']} ({species_result['confidence']:.2%})")
            else:
                print(f"   ✓ Jaguar confirmed ({species_result['confidence']:.2%})")
    
    # Step 4: Transform image
    print("🔄 Transforming image for Re-ID model...")
    image_tensor = transform(image).unsqueeze(0).to(DEVICE)
    
    # Step 5: Extract embedding
    print("🧬 Extracting Re-ID embedding...")
    with torch.no_grad():
        embedding = reid_model(image_tensor)
    print("✓ Embedding extraction complete")
    
    return embedding.squeeze(0), detection_info
