#!/usr/bin/env python3
"""
Pytest for Stage 1 Binary Classification on Videos

Tests Stage 1 (BigCat vs NotBigCat) on actual video files.
Videos contain real species - extracted frames are classified and aggregated.

Video Species Mapping:
- cheetah.mp4: Cheetah (BigCat)
- elephant.mp4: Elephant (NotBigCat)
- gazelle.mp4: Gazelle (NotBigCat)
- leopard.mp4: Leopard (BigCat)
- lion.mp4: Lion (BigCat)
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
# VIDEO TEST DATA
# ============================================================================

VIDEOS_DIR = Path(__file__).parent.parent.parent / "assets" / "videos"

VIDEO_TEST_DATA = {
    "cheetah": {
        "path": VIDEOS_DIR / "cheetah.mp4",
        "species": "Cheetah",
        "expected": "BigCat",
        "description": "Cheetah (Video)"
    },
    "elephant": {
        "path": VIDEOS_DIR / "elephant.mp4",
        "species": "Elephant",
        "expected": "NotBigCat",
        "description": "Elephant (Video)"
    },
    "gazelle": {
        "path": VIDEOS_DIR / "gazelle.mp4",
        "species": "Gazelle",
        "expected": "NotBigCat",
        "description": "Gazelle (Video)"
    },
    "leopard": {
        "path": VIDEOS_DIR / "leopard.mp4",
        "species": "Leopard",
        "expected": "BigCat",
        "description": "Leopard (Video)"
    },
    "lion": {
        "path": VIDEOS_DIR / "lion.mp4",
        "species": "Lion",
        "expected": "BigCat",
        "description": "Lion (Video)"
    },
}

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def config():
    """Load configuration"""
    from config import DEVICE, IMAGE_SIZE
    return {
        'device': DEVICE,
        'image_size': IMAGE_SIZE,
    }

@pytest.fixture(scope="module")
def stage1_model(config):
    """Load Stage 1 model"""
    from models import load_stage1_model
    return load_stage1_model()

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
    """
    Extract frames from video file using OpenCV
    
    Args:
        video_path: Path to video file
        frame_interval: Extract every nth frame (15 = ~2fps at 30fps video)
    
    Returns:
        List of PIL Image objects
    """
    try:
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        return frames
    except Exception as e:
        print(f"  Video extraction error: {e}")
        return []

def classify_video_stage1(video_path, model, transform, device, frame_interval=15, threshold=0.7, video_threshold=0.3):
    """
    Run Stage 1 inference on video by extracting and classifying frames
    
    Frame-level threshold: 0.7 (70% confidence per frame)
    Video-level threshold: 0.3 (30% of frames must be BigCat)
    
    Args:
        video_path: Path to video file
        model: Loaded Stage 1 model
        transform: Image preprocessing transform
        device: torch device
        frame_interval: Extract every nth frame
        threshold: Confidence threshold per frame
        video_threshold: % of frames that must be BigCat
    
    Returns:
        dict with is_bigcat, confidence (ratio), frames_analyzed, bigcat_frames, etc.
    """
    try:
        frames = extract_video_frames(video_path, frame_interval=frame_interval)
        
        if not frames:
            return {
                'error': 'No frames extracted from video',
                'success': False
            }
        
        bigcat_count = 0
        frame_confidences = []
        
        # Classify each frame
        for frame in frames:
            image_tensor = transform(frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                output = model(image_tensor)
                probs = F.softmax(output, dim=1)
            
            bigcat_confidence = probs[0, 0].item()  # Class 0 = BigCat
            is_frame_bigcat = bigcat_confidence >= threshold
            
            if is_frame_bigcat:
                bigcat_count += 1
            
            frame_confidences.append(bigcat_confidence)
        
        # Calculate ratio and determine video classification
        bigcat_ratio = bigcat_count / len(frames)
        is_video_bigcat = bigcat_ratio >= video_threshold
        
        return {
            'is_bigcat': is_video_bigcat,
            'confidence': bigcat_ratio,
            'frames_analyzed': len(frames),
            'bigcat_frames': bigcat_count,
            'bigcat_ratio': bigcat_ratio,
            'frame_confidences': frame_confidences,
            'avg_frame_confidence': sum(frame_confidences) / len(frame_confidences),
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

class TestStage1Videos:
    """Test Stage 1 on video files"""
    
    @pytest.mark.parametrize("video_key,video_data", VIDEO_TEST_DATA.items())
    def test_stage1_video_classification(self, video_key, video_data, stage1_model, image_transform, config):
        """
        Test Stage 1 classification on a video
        
        Extracts frames from video -> classifies each frame -> aggregates results
        """
        print(f"\n{'='*100}")
        print(f"[STAGE 1 VIDEO TEST] {video_data['description']}")
        print(f"Species in Video: {video_data['species']}")
        print(f"Expected: {video_data['expected']}")
        print(f"{'='*100}")
        
        # Verify video exists
        video_path = video_data['path']
        assert video_path.exists(), f"Video not found: {video_path}"
        print(f"[1/3] Video file: {video_path.name}")
        
        # Run video classification
        print(f"[2/3] Extracting frames and classifying...")
        result = classify_video_stage1(
            str(video_path),
            stage1_model,
            image_transform,
            config['device'],
            frame_interval=15,      # ~2fps
            threshold=0.7,          # 70% confidence per frame
            video_threshold=0.3     # 30% of frames
        )
        
        assert result['success'], f"Video classification failed: {result.get('error')}"
        
        print(f"  [OK] Analyzed {result['frames_analyzed']} frames")
        print(f"  [OK] BigCat frames: {result['bigcat_frames']}/{result['frames_analyzed']}")
        print(f"  [OK] BigCat ratio: {result['bigcat_ratio']:.1%}")
        print(f"  [OK] Avg frame confidence: {result['avg_frame_confidence']:.2%}")
        
        # Display results
        print(f"\n{'STAGE 1 VIDEO CLASSIFICATION RESULTS':^100}")
        print(f"{'-'*100}")
        print(f"  Video Decision: {'BigCat' if result['is_bigcat'] else 'NotBigCat'}")
        print(f"  BigCat Ratio:   {result['bigcat_ratio']:.1%} ({result['bigcat_frames']}/{result['frames_analyzed']} frames)")
        print(f"  Threshold:      30% (>{0.3:.0%} of frames needed)")
        print(f"{'-'*100}")
        
        # Verify prediction
        expected = video_data['expected']
        actual = "BigCat" if result['is_bigcat'] else "NotBigCat"
        
        match = "[OK] CORRECT" if actual == expected else "[FAIL] INCORRECT"
        print(f"\n  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print(f"  Result:   {match}")
        
        # Assert
        assert actual == expected, \
            f"Expected {expected} but got {actual}\n" \
            f"  BigCat ratio: {result['bigcat_ratio']:.1%}\n" \
            f"  BigCat frames: {result['bigcat_frames']}/{result['frames_analyzed']}"

# ============================================================================
# SESSION SUMMARY
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print summary report after all tests"""
    print("\n\n" + "="*110)
    print("STAGE 1 VIDEO CLASSIFICATION TEST RESULTS".center(110))
    print("="*110)
    
    print(f"""
TEST SUMMARY:
  Total Videos Tested: 5
    - BigCat Species: Cheetah, Leopard, Lion (3 videos)
    - NotBigCat Species: Elephant, Gazelle (2 videos)

METHODOLOGY:
  1. Extract frames from video (every 15th frame = ~2fps)
  2. Classify each frame with Stage 1 model
  3. Aggregate: if >= 30% of frames detected as BigCat, video = BigCat
  
EXPECTED RESULTS:
  - Cheetah: BigCat (100% detection expected)
  - Leopard: BigCat (100% detection expected)
  - Lion: BigCat (100% detection expected)
  - Elephant: NotBigCat (should be rejected)
  - Gazelle: NotBigCat (should be rejected)

FRAME-LEVEL THRESHOLDS:
  - Per-frame confidence threshold: 0.7 (70%)
  - Video aggregation threshold: 0.3 (30% of frames)

RUN COMMAND:
  cd c:\\Users\\user\\techzone\\patterns-ai-wildlife\\src\\backend
  python -m pytest _test/test_stage1_videos.py -v -s
""")
    
    print("="*110 + "\n")
