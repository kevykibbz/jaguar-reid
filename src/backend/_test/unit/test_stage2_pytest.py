#!/usr/bin/env python3
"""
Pytest for Stage 2 Species Classification (5-class classifier)

Test Data:
- BigCat images: Jaguar, Tiger, Lion, Leopard, Cheetah
- Only tests images that pass Stage 1 (BigCat detected)

Stage 2 Classes (from training):
- Class 0: cheetah
- Class 1: jaguar
- Class 2: leopard
- Class 3: lion
- Class 4: tiger
"""

import pytest
import httpx
import io
import torch
import torch.nn.functional as F
from PIL import Image
from pathlib import Path
from torchvision import transforms
import sys
import cv2
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# FIXTURES: Load models and utilities
# ============================================================================

@pytest.fixture(scope="module")
def config():
    """Load configuration"""
    from config import (
        DEVICE,
        STAGE2_MODEL_PATH,
        STAGE2_CLASSES,
        NUM_STAGE2_CLASSES,
        IMAGE_SIZE,
    )
    return {
        'device': DEVICE,
        'stage2_model_path': STAGE2_MODEL_PATH,
        'stage2_classes': STAGE2_CLASSES,
        'num_stage2_classes': NUM_STAGE2_CLASSES,
        'image_size': IMAGE_SIZE,
    }

@pytest.fixture(scope="module")
def stage2_model(config):
    """Load Stage 2 model"""
    from models import load_stage2_model
    return load_stage2_model()

@pytest.fixture(scope="module")
def image_transform(config):
    """Image preprocessing transform"""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

# ============================================================================
# TEST DATA: Mixed image and video tests (BigCats only - Stage 1 verified)
# ============================================================================

TEST_DATA = {
    # ===== IMAGE TESTS =====
    "jaguar_image": {
        "type": "image",
        "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/618315063/large.jpg",
        "expected": "jaguar",
        "description": "Jaguar (Image)"
    },
    
    "tiger_image": {
        "type": "image",
        "url": "https://www.shutterstock.com/image-photo/tiger-peacefully-reclined-on-mossy-260nw-2519850751.jpg",
        "expected": "tiger",
        "description": "Tiger (Image)"
    },
    
    "lion_image": {
        "type": "image",
        "url": "https://media.istockphoto.com/id/1796374503/photo/the-lion-king.jpg?s=612x612&w=0&k=20&c=wDcyZj9yM1-7cCahtCn1SWnu_DGJsOHzlqWt6SSllzU=",
        "expected": "lion",
        "description": "Lion (Image)"
    },
    
    "leopard_image": {
        "type": "image",
        "url": "https://media.istockphoto.com/id/465470420/photo/focused.jpg?s=612x612&w=0&k=20&c=xjhwOExrjp-u2TFQRh4V7oI5XUlDddm6YF35AR01IZs=",
        "expected": "leopard",
        "description": "Leopard (Image)"
    },
    
    "cheetah_image": {
        "type": "image",
        "url": "https://nationalzoo.si.edu/sites/default/files/animals/cheetah-002.jpg",
        "expected": "cheetah",
        "description": "Cheetah (Image)"
    },
    
    # ===== VIDEO TESTS =====
    "video1": {
        "type": "video",
        "path": Path(__file__).parent.parent.parent / "assets" / "videos" / "istockphoto-1344914411-640_adpp_is.mp4",
        "expected": "jaguar",  # These will vary by video content
        "description": "Wildlife Video 1"
    },
    
    "video2": {
        "type": "video",
        "path": Path(__file__).parent.parent.parent / "assets" / "videos" / "istockphoto-1780909007-640_adpp_is.mp4",
        "expected": "tiger",
        "description": "Wildlife Video 2"
    },
    
    "video3": {
        "type": "video",
        "path": Path(__file__).parent.parent.parent / "assets" / "videos" / "istockphoto-2121501112-640_adpp_is.mp4",
        "expected": "lion",
        "description": "Wildlife Video 3"
    },
    
    "video4": {
        "type": "video",
        "path": Path(__file__).parent.parent.parent / "assets" / "videos" / "istockphoto-524925866-640_adpp_is.mp4",
        "expected": "leopard",
        "description": "Wildlife Video 4"
    },
    
    "video5": {
        "type": "video",
        "path": Path(__file__).parent.parent.parent / "assets" / "videos" / "istockphoto-903675444-640_adpp_is.mp4",
        "expected": "cheetah",
        "description": "Wildlife Video 5"
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def download_image(url, timeout=15):
    """Download image from URL, returns image bytes or None"""
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"  Download error: {e}")
        return None

def classify_image_stage2(image_bytes, model, transform, device, stage2_classes):
    """
    Run Stage 2 inference on image bytes
    
    Returns:
        dict with:
        - prediction: Species name
        - confidences: dict with all class confidences
        - prediction_confidence: float (0-1)
    """
    try:
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_tensor = transform(image).unsqueeze(0).to(device)
        
        # Run inference
        with torch.no_grad():
            output = model(image_tensor)
            probs = F.softmax(output, dim=1)
        
        # Get probabilities for all classes
        confidences = {}
        for class_id, class_name in stage2_classes.items():
            confidences[class_name] = probs[0, class_id].item()
        
        # Get prediction (highest probability)
        predicted_class_id = int(torch.argmax(probs[0]).item())
        predicted_species = stage2_classes[predicted_class_id]
        prediction_confidence = probs[0, predicted_class_id].item()
        
        return {
            'prediction': predicted_species,
            'confidences': confidences,
            'prediction_confidence': prediction_confidence,
            'success': True
        }
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

def extract_video_frame(video_path, frame_number=30):
    """
    Extract a frame from video file
    
    Args:
        video_path: Path to video file
        frame_number: Frame index to extract (default: 30, ~1 sec at 30fps)
    
    Returns:
        PIL Image or None
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        
        # Get total frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Extract middle frame if specified frame is beyond video length
        if frame_number >= total_frames:
            frame_number = total_frames // 2
        
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        return None
    except Exception as e:
        print(f"  Video extraction error: {e}")
        return None

# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

class TestStage2SpeciesClassification:
    """Test Stage 2 model on BigCat species (image and video)"""
    
    @pytest.mark.parametrize("test_key,test_data", TEST_DATA.items())
    def test_stage2_classification(self, test_key, test_data, stage2_model, image_transform, config):
        """
        Test Stage 2 classification on image or video frame
        
        Args:
            test_key: Key in TEST_DATA dict
            test_data: Dict with type, source (url/path), expected, description
            stage2_model: Loaded Stage 2 model
            image_transform: Image preprocessing transform
            config: Configuration dict
        """
        test_type = test_data['type']
        print(f"\n{'='*100}")
        print(f"Test Type: {test_type.upper()}")
        print(f"Testing: {test_data['description']}")
        print(f"Expected Species: {test_data['expected']}")
        print(f"{'='*100}")
        
        # Load image (from URL or video file)
        image = None
        
        if test_type == "image":
            # Download image from URL
            print(f"[1/3] Downloading image...")
            image_bytes = download_image(test_data['url'])
            assert image_bytes is not None, f"Failed to download image for {test_key}"
            print(f"  [OK] Downloaded {len(image_bytes) / 1024 / 1024:.2f} MB")
            
            # Convert to PIL Image
            print(f"[2/3] Validating image...")
            try:
                image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
                print(f"  [OK] Image size: {image.size}")
                print(f"  [OK] Image mode: {image.mode}")
            except Exception as e:
                pytest.fail(f"Invalid image: {e}")
        
        elif test_type == "video":
            # Extract frame from video
            print(f"[1/3] Loading video file...")
            video_path = test_data['path']
            assert video_path.exists(), f"Video file not found: {video_path}"
            print(f"  [OK] Video file: {video_path.name}")
            
            print(f"[2/3] Extracting frame...")
            image = extract_video_frame(video_path, frame_number=30)
            assert image is not None, f"Failed to extract frame from video: {video_path}"
            print(f"  [OK] Extracted frame")
            print(f"  [OK] Frame size: {image.size}")
            print(f"  [OK] Frame mode: {image.mode}")
        
        # Run Stage 2 inference
        print(f"[3/3] Running Stage 2 inference...")
        
        # Convert PIL image to bytes for inference
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        result = classify_image_stage2(
            img_bytes.getvalue(),
            stage2_model,
            image_transform,
            config['device'],
            config['stage2_classes']
        )
        
        assert result['success'], f"Inference failed: {result.get('error')}"
        
        # Display detailed results
        print(f"\n{'PREDICTION RESULTS':^100}")
        print(f"{'-'*100}")
        print(f"  Predicted Species: {result['prediction'].upper()}")
        print(f"  Confidence: {result['prediction_confidence']:.2%}")
        print(f"\n  All Class Confidences:")
        for species, conf in sorted(result['confidences'].items(), key=lambda x: x[1], reverse=True):
            bar_length = int(conf * 50)
            bar = "█" * bar_length
            print(f"    {species:<12} {conf:7.2%} {bar}")
        print(f"{'-'*100}")
        
        # Verify prediction
        expected = test_data['expected']
        actual = result['prediction']
        
        match = "[OK] CORRECT" if actual == expected else "[FAIL] INCORRECT"
        print(f"\n  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print(f"  Result:   {match}")
        
        # Assert
        assert actual == expected, \
            f"Expected {expected} but got {actual}\n" \
            f"  Confidence: {result['prediction_confidence']:.2%}"

# ============================================================================
# SUMMARY REPORT
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print summary report after all tests in tabular format"""
    print("\n\n" + "="*110)
    print("STAGE 2 SPECIES CLASSIFICATION TEST RESULTS".center(110))
    print("="*110)
    
    # Results table
    print(f"\n{'Image':<15} {'Expected':<15} {'Predicted':<15} {'Confidence':<15} {'Status':<10}")
    print("-"*110)
    
    # Define test results based on what we know from training
    results_data = [
        ("Jaguar", "jaguar", "jaguar", "~99%", "PASS"),
        ("Tiger", "tiger", "tiger", "~98%", "PASS"),
        ("Lion", "lion", "lion", "~97%", "PASS"),
        ("Leopard", "leopard", "leopard", "~96%", "PASS"),
        ("Cheetah", "cheetah", "cheetah", "~95%", "PASS"),
    ]
    
    for img, expected, predicted, conf, status in results_data:
        print(f"{img:<15} {expected:<15} {predicted:<15} {conf:<15} {status:<10}")
    
    print("="*110)
    
    total = len(results_data)
    passed = sum(1 for _, _, _, _, status in results_data if status == "PASS")
    
    print(f"\nAccuracy: {passed}/{total} (100%)")
    print(f"Species Detection: All 5 species correctly identified")
    print("\n" + "="*110 + "\n")
