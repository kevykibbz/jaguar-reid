#!/usr/bin/env python3
"""
Pytest for Combined Two-Stage Pipeline on Videos

Tests both Stage 1 (BigCat filter) and Stage 2 (species classification) together on video files.

Pipeline Flow:
1. Stage 1: Extract frames -> classify each -> aggregate (30% threshold)
2. If BigCat detected:
   - Stage 2: Extract frames -> classify species -> majority vote
3. If NotBigCat: Stop, output "Not a BigCat"

Video Species:
- cheetah.mp4: Cheetah (BigCat) -> should identify as 'cheetah'
- elephant.mp4: Elephant (NotBigCat) -> should reject at Stage 1
- gazelle.mp4: Gazelle (NotBigCat) -> should reject at Stage 1
- leopard.mp4: Leopard (BigCat) -> should identify as 'leopard'
- lion.mp4: Lion (BigCat) -> should identify as 'lion'
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
# VIDEO TEST DATA - All 5 Species
# ============================================================================

VIDEOS_DIR = Path(__file__).parent.parent.parent / "assets" / "videos"

VIDEO_TEST_DATA = {
    "cheetah": {
        "path": VIDEOS_DIR / "cheetah.mp4",
        "species": "Cheetah",
        "is_bigcat": True,
        "expected_stage1": "BigCat",
        "expected_species": "cheetah",
        "description": "Cheetah (Video)"
    },
    "elephant": {
        "path": VIDEOS_DIR / "elephant.mp4",
        "species": "Elephant",
        "is_bigcat": False,
        "expected_stage1": "NotBigCat",
        "expected_species": None,  # Should reject at Stage 1
        "description": "Elephant (Video)"
    },
    "gazelle": {
        "path": VIDEOS_DIR / "gazelle.mp4",
        "species": "Gazelle",
        "is_bigcat": False,
        "expected_stage1": "NotBigCat",
        "expected_species": None,  # Should reject at Stage 1
        "description": "Gazelle (Video)"
    },
    "leopard": {
        "path": VIDEOS_DIR / "leopard.mp4",
        "species": "Leopard",
        "is_bigcat": True,
        "expected_stage1": "BigCat",
        "expected_species": "leopard",
        "description": "Leopard (Video)"
    },
    "lion": {
        "path": VIDEOS_DIR / "lion.mp4",
        "species": "Lion",
        "is_bigcat": True,
        "expected_stage1": "BigCat",
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
def stage1_model(config):
    """Load Stage 1 model"""
    from models import load_stage1_model
    return load_stage1_model()

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
    """Extract frames from video file"""
    try:
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)
            
            frame_count += 1
        
        cap.release()
        return frames
    except Exception as e:
        print(f"  Video extraction error: {e}")
        return []

def classify_video_stage1(video_path, model, transform, device, frame_interval=15, threshold=0.7, video_threshold=0.3):
    """Run Stage 1 inference on video frames"""
    try:
        frames = extract_video_frames(video_path, frame_interval=frame_interval)
        
        if not frames:
            return {'error': 'No frames extracted', 'success': False}
        
        bigcat_count = 0
        frame_confidences = []
        
        for frame in frames:
            image_tensor = transform(frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                output = model(image_tensor)
                probs = F.softmax(output, dim=1)
            
            bigcat_confidence = probs[0, 0].item()
            is_frame_bigcat = bigcat_confidence >= threshold
            
            if is_frame_bigcat:
                bigcat_count += 1
            
            frame_confidences.append(bigcat_confidence)
        
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
        return {'error': str(e), 'success': False}

def classify_video_stage2(video_path, model, transform, device, stage2_classes, frame_interval=15):
    """Run Stage 2 inference on video frames (majority voting)"""
    try:
        frames = extract_video_frames(video_path, frame_interval=frame_interval)
        
        if not frames:
            return {'error': 'No frames extracted', 'success': False}
        
        species_counts = {species: 0 for species in stage2_classes.values()}
        frame_predictions = []
        
        for frame in frames:
            image_tensor = transform(frame).unsqueeze(0).to(device)
            
            with torch.no_grad():
                output = model(image_tensor)
                probs = F.softmax(output, dim=1)
            
            predicted_class_id = torch.argmax(probs[0]).item()
            predicted_species = stage2_classes[predicted_class_id]
            confidence = probs[0, predicted_class_id].item()
            
            species_counts[predicted_species] += 1
            
            frame_predictions.append({
                'species': predicted_species,
                'confidence': confidence
            })
        
        final_species = max(species_counts, key=lambda x: species_counts[x])
        final_species_count = species_counts[final_species]
        final_confidence = final_species_count / len(frames)
        
        return {
            'predicted_species': final_species,
            'confidence': final_confidence,
            'species_counts': species_counts,
            'frames_analyzed': len(frames),
            'success': True
        }
    except Exception as e:
        return {'error': str(e), 'success': False}

# ============================================================================
# TESTS
# ============================================================================

class TestCombinedPipeline:
    """Test complete two-stage pipeline on videos"""
    
    @pytest.mark.parametrize("video_key,video_data", VIDEO_TEST_DATA.items())
    def test_combined_pipeline(self, video_key, video_data, stage1_model, stage2_model, image_transform, config):
        """
        Test complete two-stage pipeline
        Stage 1: BigCat detection
        Stage 2: Species classification (only if Stage 1 passes)
        """
        print(f"\n{'='*110}")
        print(f"[COMBINED PIPELINE TEST] {video_data['description']}")
        print(f"Species: {video_data['species']}")
        print(f"Expected Stage 1: {video_data['expected_stage1']}")
        if video_data['is_bigcat']:
            print(f"Expected Species (Stage 2): {video_data['expected_species']}")
        print(f"{'='*110}")
        
        # Verify video exists
        video_path = video_data['path']
        assert video_path.exists(), f"Video not found: {video_path}"
        print(f"[1/4] Video file: {video_path.name}")
        
        # Stage 1: Binary Classification
        print(f"[2/4] Running Stage 1 (BigCat Detection)...")
        stage1_result = classify_video_stage1(
            str(video_path),
            stage1_model,
            image_transform,
            config['device'],
            frame_interval=15,
            threshold=0.7,
            video_threshold=0.3
        )
        
        assert stage1_result['success'], f"Stage 1 failed: {stage1_result.get('error')}"
        
        stage1_decision = "BigCat" if stage1_result['is_bigcat'] else "NotBigCat"
        print(f"  [OK] Analyzed {stage1_result['frames_analyzed']} frames")
        print(f"  [OK] Stage 1 Decision: {stage1_decision}")
        print(f"  [OK] BigCat ratio: {stage1_result['bigcat_ratio']:.1%}")
        
        # Stage 2: Species Classification (only if BigCat detected)
        stage2_result = None
        stage2_decision = None
        
        if stage1_result['is_bigcat']:
            print(f"[3/4] Running Stage 2 (Species Classification)...")
            stage2_result = classify_video_stage2(
                str(video_path),
                stage2_model,
                image_transform,
                config['device'],
                config['stage2_classes'],
                frame_interval=15
            )
            
            assert stage2_result['success'], f"Stage 2 failed: {stage2_result.get('error')}"
            
            stage2_decision = stage2_result['predicted_species']
            print(f"  [OK] Analyzed {stage2_result['frames_analyzed']} frames")
            print(f"  [OK] Stage 2 Decision: {stage2_decision}")
            print(f"  [OK] Species confidence: {stage2_result['confidence']:.1%}")
        else:
            print(f"[3/4] Stage 2 skipped (Stage 1 rejected)")
            stage2_decision = None
        
        # Final result
        print(f"[4/4] Final Pipeline Result")
        
        print(f"\n{'TWO-STAGE PIPELINE RESULTS':^110}")
        print(f"{'-'*110}")
        print(f"  Stage 1 (BigCat Filter):")
        print(f"    Decision: {stage1_decision}")
        print(f"    Ratio: {stage1_result['bigcat_ratio']:.1%} ({stage1_result['bigcat_frames']}/{stage1_result['frames_analyzed']} frames)")
        print(f"    Avg Confidence: {stage1_result['avg_frame_confidence']:.2%}")
        
        if stage2_result:
            print(f"  Stage 2 (Species Classifier):")
            print(f"    Decision: {stage2_decision}")
            print(f"    Confidence: {stage2_result['confidence']:.1%}")
            print(f"    Species Distribution:")
            for species, count in sorted(stage2_result['species_counts'].items(), key=lambda x: x[1], reverse=True)[:3]:
                pct = (count / stage2_result['frames_analyzed']) * 100
                print(f"      {species:<12} {count:>3} frames ({pct:>5.1f}%)")
        
        print(f"  Final Output: {'[BigCat] ' + stage2_decision if stage2_decision else '[NotBigCat]'}")
        print(f"{'-'*110}")
        
        # Verify predictions
        stage1_expected = video_data['expected_stage1']
        stage1_actual = stage1_decision
        
        stage1_match = stage1_actual == stage1_expected
        print(f"\n  Stage 1 Verification:")
        print(f"    Expected: {stage1_expected}")
        print(f"    Actual:   {stage1_actual}")
        print(f"    Result:   {'[OK] CORRECT' if stage1_match else '[FAIL] INCORRECT'}")
        
        if stage2_result:
            stage2_expected = video_data['expected_species']
            stage2_actual = stage2_decision
            
            stage2_match = stage2_actual == stage2_expected
            print(f"\n  Stage 2 Verification:")
            print(f"    Expected: {stage2_expected}")
            print(f"    Actual:   {stage2_actual}")
            print(f"    Result:   {'[OK] CORRECT' if stage2_match else '[FAIL] INCORRECT'}")
            
            assert stage2_match, \
                f"Stage 2: Expected {stage2_expected} but got {stage2_actual}"
        
        # Assert Stage 1
        assert stage1_match, \
            f"Stage 1: Expected {stage1_expected} but got {stage1_actual}"

# ============================================================================
# SESSION SUMMARY
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print summary report"""
    print("\n\n" + "="*120)
    print("COMBINED TWO-STAGE PIPELINE VIDEO TEST RESULTS".center(120))
    print("="*120)
    
    print(f"""
PIPELINE ARCHITECTURE:
  
  Input Video
       |
       v
  [Stage 1: BigCat Binary Filter]
       |
       +-- NotBigCat (ratio < 30%) --> OUTPUT: [Not a BigCat]
       |
       +-- BigCat (ratio >= 30%) --> [Stage 2: Species Classifier]
                                       |
                                       v
                                    Species Decision
                                       |
                                       v
                                  OUTPUT: [BigCat + Species]

METHODOLOGY:
  Stage 1 (Frame-level):
    - Extract frames from video (every 15th = ~2fps)
    - Classify each frame with binary model
    - Threshold per frame: 70% confidence
    - Aggregate: if >=30% of frames are BigCat, pass to Stage 2
  
  Stage 2 (Frame-level):
    - Extract same frames from video
    - Classify each frame with species model
    - Aggregate: Use majority voting across all frames
    - Output: Most common species prediction

VIDEO TEST DATA (5 videos):
  BigCat Videos (3):
    - cheetah.mp4: Expected to pass Stage 1 + classify as 'cheetah'
    - leopard.mp4: Expected to pass Stage 1 + classify as 'leopard'
    - lion.mp4: Expected to pass Stage 1 + classify as 'lion'
  
  NotBigCat Videos (2):
    - elephant.mp4: Expected to FAIL Stage 1 (reject)
    - gazelle.mp4: Expected to FAIL Stage 1 (reject)

EXPECTED RESULTS:
  SUCCESS: 5/5 videos classified correctly
    - BigCats detected at Stage 1 + correct species at Stage 2
    - Non-BigCats rejected at Stage 1 (no Stage 2 run)

RUN COMMAND:
  cd c:\\Users\\user\\techzone\\patterns-ai-wildlife\\src\\backend
  python -m pytest _test/test_combined_videos.py -v -s
""")
    
    print("="*120 + "\n")
