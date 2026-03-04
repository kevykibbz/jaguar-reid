#!/usr/bin/env python3
"""
Pytest for Stage 2 Species Classification on Videos

Tests Stage 2 (5-class species classifier) on video frames.
Only runs on videos where Stage 1 detects BigCat.

Video Species:
- cheetah.mp4: Cheetah (Class 0)
- leopard.mp4: Leopard (Class 2)
- lion.mp4: Lion (Class 3)
"""

import pytest
import os
import cv2
import torch
import torch.nn.functional as F
from PIL import Image
from pathlib import Path
from torchvision import transforms
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# VIDEO TEST DATA - Only BigCats
# ============================================================================

VIDEOS_DIR = Path(__file__).parent.parent.parent / "assets" / "videos"

VIDEO_TEST_DATA = {
    "cheetah": {
        "path": VIDEOS_DIR / "cheetah.mp4",
        "expected_species": "cheetah",
        "description": "Cheetah (Video)"
    },
    "leopard": {
        "path": VIDEOS_DIR / "leopard.mp4",
        "expected_species": "leopard",
        "description": "Leopard (Video)"
    },
    "lion": {
        "path": VIDEOS_DIR / "lion.mp4",
        "expected_species": "lion",
        "description": "Lion (Video)"
    },
}

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def config():
    """Load configuration"""
    from config import DEVICE, STAGE2_CLASSES, IMAGE_SIZE
    return {
        'device': DEVICE,
        'stage2_classes': STAGE2_CLASSES,
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
# HELPER FUNCTIONS
# ============================================================================

def extract_video_frames(video_path, frame_interval=15):
    """Extract frames from video file using OpenCV"""
    try:
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
            
            frame_count += 1
        
        cap.release()
        return frames
    except Exception as e:
        print(f"  Video extraction error: {e}")
        return []

def classify_video_stage2(video_path, model, transform, device, stage2_classes, frame_interval=15):
    """
    Run Stage 2 inference on video frames
    Returns aggregated species predictions across all frames
    
    Args:
        video_path: Path to video file
        model: Loaded Stage 2 model
        transform: Image preprocessing transform
        device: torch device
        stage2_classes: Dict mapping class_id -> species_name
        frame_interval: Extract every nth frame
    
    Returns:
        dict with aggregated predictions
    """
    try:
        frames = extract_video_frames(video_path, frame_interval=frame_interval)
        
        if not frames:
            return {
                'error': 'No frames extracted from video',
                'success': False
            }
        
        # Count species predictions across all frames
        species_counts = {species: 0 for species in stage2_classes.values()}
        frame_predictions = []
        
        # Classify each frame
        for frame in frames:
            image_tensor = transform(frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                output = model(image_tensor)
                probs = F.softmax(output, dim=1)
            
            # Get top prediction
            predicted_class_id = torch.argmax(probs[0]).item()
            predicted_species = stage2_classes[predicted_class_id]
            confidence = probs[0, predicted_class_id].item()
            
            species_counts[predicted_species] += 1
            
            frame_predictions.append({
                'species': predicted_species,
                'confidence': confidence,
                'all_scores': {species: probs[0, class_id].item() 
                              for class_id, species in stage2_classes.items()}
            })
        
        # Determine final species by majority vote
        final_species = max(species_counts.items(), key=lambda x: x[1])[0]
        final_species_count = species_counts[final_species]
        final_confidence = final_species_count / len(frames)
        
        return {
            'predicted_species': final_species,
            'confidence': final_confidence,
            'species_counts': species_counts,
            'frames_analyzed': len(frames),
            'frame_predictions': frame_predictions,
            'success': True
        }
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

# ============================================================================
# TESTS
# ============================================================================

class TestStage2Videos:
    """Test Stage 2 species classification on video frames"""
    
    @pytest.mark.parametrize("video_key,video_data", VIDEO_TEST_DATA.items())
    def test_stage2_video_classification(self, video_key, video_data, stage2_model, image_transform, config):
        """
        Test Stage 2 species classification on a video
        Uses majority voting across all extracted frames
        """
        print(f"\n{'='*100}")
        print(f"[STAGE 2 VIDEO TEST] {video_data['description']}")
        print(f"Expected Species: {video_data['expected_species']}")
        print(f"{'='*100}")
        
        # Verify video exists
        video_path = video_data['path']
        assert video_path.exists(), f"Video not found: {video_path}"
        print(f"[1/3] Video file: {video_path.name}")
        
        # Run video classification
        print(f"[2/3] Extracting frames and classifying...")
        result = classify_video_stage2(
            str(video_path),
            stage2_model,
            image_transform,
            config['device'],
            config['stage2_classes'],
            frame_interval=15
        )
        
        assert result['success'], f"Video classification failed: {result.get('error')}"
        
        print(f"  [OK] Analyzed {result['frames_analyzed']} frames")
        print(f"  [OK] Species distribution:")
        for species, count in sorted(result['species_counts'].items(), key=lambda x: x[1], reverse=True):
            pct = (count / result['frames_analyzed']) * 100
            print(f"      {species:<12} {count:>3} frames ({pct:>5.1f}%)")
        print(f"  [OK] Final prediction: {result['predicted_species']} ({result['confidence']:.1%})")
        
        # Display detailed results
        print(f"\n{'STAGE 2 VIDEO CLASSIFICATION RESULTS':^100}")
        print(f"{'-'*100}")
        print(f"  Predicted Species: {result['predicted_species'].upper()}")
        print(f"  Confidence: {result['confidence']:.1%} ({result['species_counts'][result['predicted_species']]}/{result['frames_analyzed']} frames)")
        print(f"  Method: Majority voting across all frames")
        print(f"{'-'*100}")
        
        # Verify prediction
        expected = video_data['expected_species']
        actual = result['predicted_species']
        
        match = "[OK] CORRECT" if actual == expected else "[FAIL] INCORRECT"
        print(f"\n  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print(f"  Result:   {match}")
        
        # Assert
        assert actual == expected, \
            f"Expected {expected} but got {actual}\n" \
            f"  Confidence: {result['confidence']:.1%}\n" \
            f"  Species count: {result['species_counts'][actual]}/{result['frames_analyzed']}"

# ============================================================================
# SESSION SUMMARY
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print summary report"""
    print("\n\n" + "="*110)
    print("STAGE 2 VIDEO SPECIES CLASSIFICATION TEST RESULTS".center(110))
    print("="*110)
    
    print(f"""
TEST SUMMARY:
  Total BigCat Videos Tested: 3
    - Cheetah: Expected to classify as 'cheetah'
    - Leopard: Expected to classify as 'leopard'
    - Lion: Expected to classify as 'lion'

METHODOLOGY:
  1. Extract frames from video (every 15th frame = ~2fps)
  2. Classify each frame with Stage 2 species classifier
  3. Aggregate: Use majority voting (most common species prediction)

SPECIES CLASSES (Stage 2):
  - Class 0: cheetah
  - Class 1: jaguar
  - Class 2: leopard
  - Class 3: lion
  - Class 4: tiger

PREDICTION METHOD:
  Count species predictions across all frames, select most common

RUN COMMAND:
  cd c:\\Users\\user\\techzone\\patterns-ai-wildlife\\src\\backend
  python -m pytest _test/test_stage2_videos.py -v -s
""")
    
    print("="*110 + "\n")
