"""
Image preprocessing pipeline for jaguar detection and segmentation.
"""
import io
import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from config import (
    DEVICE, 
    IMAGE_SIZE, 
    YOLO_CONFIDENCE_THRESHOLD, 
    CROP_PADDING_PERCENT
)


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
            print("✓ Detected pre-segmented image (has transparency)")
            return True
        
        # Check 2: Small image size (likely already cropped)
        width, height = image.size
        if width < 500 and height < 500:
            print("✓ Detected pre-cropped image (small dimensions)")
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
            print("✓ Detected processed image (uniform background)")
            return True
        
        return False
    except Exception as e:
        print(f"⚠ Error checking segmentation: {e}")
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
        tuple: (PIL Image cropped, bounding box coordinates [x1, y1, x2, y2], original cv2 image)
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
        print("⚠ No jaguar detected, using full image")
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        h, w = img_cv.shape[:2]
        return pil_image, [0, 0, w, h], img_cv
    
    # Get the first detection (highest confidence)
    boxes = results[0].boxes
    box = boxes[0]
    confidence = float(box.conf[0])
    
    print(f"✓ Jaguar detected with confidence: {confidence:.2f}")
    
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
    
    return pil_image, [x1, y1, x2, y2], img_cv


def segment_with_sam(image_bytes, yolo_model, sam_predictor):
    """
    Segment jaguar using SAM (Segment Anything Model) for precise background removal.
    
    Args:
        image_bytes: Raw image bytes
        yolo_model: Loaded YOLO model instance
        sam_predictor: Loaded SAM predictor instance
    
    Returns:
        PIL Image: Segmented jaguar with background removed (transparent)
    """
    if sam_predictor is None:
        # Fallback to bounding box crop if SAM not available
        print("⚠ SAM not available, using bounding box crop")
        pil_image, _, _ = detect_and_crop_jaguar(image_bytes, yolo_model)
        return pil_image
    
    # First, detect jaguar with YOLO
    _, bbox, img_cv = detect_and_crop_jaguar(image_bytes, yolo_model)
    
    # Convert to RGB for SAM
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    
    # Set image for SAM
    sam_predictor.set_image(img_rgb)
    
    # Use bounding box as prompt for SAM
    input_box = np.array(bbox)
    
    # Generate mask
    print("🎨 Generating precise segmentation mask...")
    masks, scores, _ = sam_predictor.predict(
        box=input_box,
        multimask_output=False
    )
    
    # Get the best mask
    mask = masks[0]
    print(f"✓ Segmentation complete (score: {scores[0]:.3f})")
    
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
    
    return rgb_image


def extract_embedding(image_bytes, yolo_model, reid_model, sam_predictor=None):
    """
    Complete preprocessing pipeline:
    1. Check if image is already segmented
    2. Detect jaguar using YOLO (if needed)
    3. Segment with SAM (if available and needed) or crop with bounding box
    4. Resize and normalize image
    5. Extract embedding using Re-ID model
    
    Args:
        image_bytes: Raw image bytes
        yolo_model: Loaded YOLO model instance
        reid_model: Loaded Re-ID model instance
        sam_predictor: Optional SAM predictor for precise segmentation
    
    Returns:
        torch.Tensor: 512-dimensional embedding vector
    """
    # Step 1: Check if already processed
    if is_already_segmented(image_bytes):
        print("⚡ Skipping segmentation for pre-processed image")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    else:
        # Step 2-3: Detect and segment/crop jaguar
        if sam_predictor is not None:
            print("🎨 Applying SAM segmentation...")
            image = segment_with_sam(image_bytes, yolo_model, sam_predictor)
        else:
            image, _, _ = detect_and_crop_jaguar(image_bytes, yolo_model)
    
    # Step 4: Transform image
    image_tensor = transform(image).unsqueeze(0).to(DEVICE)
    
    # Step 5: Extract embedding
    with torch.no_grad():
        embedding = reid_model(image_tensor)
    
    return embedding.squeeze(0)
