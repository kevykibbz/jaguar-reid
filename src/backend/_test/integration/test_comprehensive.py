#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Wildlife Classification
Tests images and videos through the API endpoints
"""

import sys
from pathlib import Path

# Add test data directory to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir / "data"))

import requests
import time
from typing import Dict, List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fixtures.test_images import BIGCAT_IMAGES, OTHER_ANIMALS, NON_ANIMALS
from fixtures.test_videos import get_available_videos

API_URL = "http://localhost:8000"
TIMEOUT = 180  # Longer timeout for CPU inference


class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_type: str, name: str, expected: str, predicted: str, 
                   correct: bool, time: float, details: dict = None):
        """Add a test result"""
        self.total += 1
        if correct:
            self.passed += 1
        else:
            self.failed += 1
        
        self.results.append({
            'type': test_type,
            'name': name,
            'expected': expected,
            'predicted': predicted,
            'correct': correct,
            'time': time,
            'details': details or {}
        })
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests:  {self.total}")
        print(f"Passed:       {self.passed} ✓")
        print(f"Failed:       {self.failed} ✗")
        print(f"Success Rate: {(self.passed/self.total*100) if self.total > 0 else 0:.1f}%")
        
        if self.results:
            avg_time = sum(r['time'] for r in self.results if r['time'] > 0) / len([r for r in self.results if r['time'] > 0])
            print(f"Average Time: {avg_time:.2f}s")
        
        # Detailed results
        print(f"\n{'Type':<8} {'Name':<20} {'Expected':<15} {'Predicted':<15} {'Status':<8} {'Time':<8}")
        print("-"*80)
        for r in self.results:
            status = "✓" if r['correct'] else "✗"
            time_str = f"{r['time']:.2f}s" if r['time'] > 0 else "N/A"
            print(f"{r['type']:<8} {r['name']:<20} {r['expected']:<15} {r['predicted']:<15} {status:<8} {time_str:<8}")
        
        print("="*80)


def test_image(url: str, name: str, expected: dict, results: TestResults):
    """Test a single image URL"""
    print(f"\n{'─'*80}")
    print(f"Testing Image: {name}")
    print(f"URL: {url[:60]}...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/predict/url",
            json={"image_url": url},
            timeout=TIMEOUT
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract results
            stage0 = result.get('stage0', {})
            stage1 = result.get('stage1')
            stage2 = result.get('stage2')
            
            is_animal = stage0.get('is_animal', False) if stage0 else False
            stage0_label = stage0.get('label', 'N/A') if stage0 else 'N/A'
            
            if stage1:
                is_bigcat = stage1.get('is_bigcat', False)
                stage1_label = stage1.get('label', 'N/A')
                stage1_conf = stage1.get('confidence', 0)
            else:
                is_bigcat = False
                stage1_label = 'Skipped'
                stage1_conf = 0
            
            final_species = result.get('final_species', 'NotBigCat')
            final_conf = result.get('final_confidence', 0)
            
            # Print results
            print(f"  Stage 0: {stage0_label} (animal={is_animal})")
            if stage1:
                print(f"  Stage 1: {stage1_label} ({stage1_conf:.2%})")
            if is_bigcat and stage2:
                print(f"  Stage 2: {final_species} ({final_conf:.2%})")
            print(f"  Result: {final_species}")
            print(f"  Time: {elapsed_time:.2f}s")
            
            # Determine correctness
            expected_species = expected.get('expected_species')
            if expected_species:
                # Should be a big cat
                correct = (is_bigcat and final_species.lower() == expected_species.lower())
                if correct:
                    print(f"  ✓ CORRECT! Predicted {final_species}")
                else:
                    print(f"  ✗ FAILED! Expected {expected_species}, got {final_species}")
                
                results.add_result('Image', name, expected_species, final_species, 
                                 correct, elapsed_time, {'is_bigcat': is_bigcat})
            else:
                # Should NOT be a big cat
                correct = not is_bigcat
                expected_label = expected.get('expected_stage1', 'NotBigCat')
                if correct:
                    print(f"  ✓ CORRECT! Not a big cat")
                else:
                    print(f"  ✗ FAILED! Should not be a big cat")
                
                results.add_result('Image', name, expected_label, final_species, 
                                 correct, elapsed_time, {'is_bigcat': is_bigcat})
        else:
            print(f"  ✗ HTTP Error {response.status_code}")
            results.add_result('Image', name, 'N/A', 'ERROR', False, 0)
            
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        results.add_result('Image', name, 'N/A', 'EXCEPTION', False, 0)


def test_video(video_path: Path, name: str, expected: dict, results: TestResults):
    """Test a single video file"""
    print(f"\n{'─'*80}")
    print(f"Testing Video: {name}")
    print(f"Path: {video_path}")
    
    if not video_path.exists():
        print(f"  ⚠ SKIPPED - File not found")
        results.add_result('Video', name, 'N/A', 'SKIPPED', True, 0)
        return
    
    try:
        start_time = time.time()
        
        with open(video_path, 'rb') as f:
            files = {'file': (video_path.name, f, 'video/mp4')}
            response = requests.post(
                f"{API_URL}/predict",
                files=files,
                timeout=TIMEOUT
            )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract results
            stage0 = result.get('stage0', {})
            stage1 = result.get('stage1')
            stage2 = result.get('stage2')
            
            is_animal = stage0.get('is_animal', False) if stage0 else False
            stage0_label = stage0.get('label', 'N/A') if stage0 else 'N/A'
            
            if stage1:
                is_bigcat = stage1.get('is_bigcat', False)
                stage1_label = stage1.get('label', 'N/A')
                stage1_conf = stage1.get('confidence', 0)
            else:
                is_bigcat = False
                stage1_label = 'Skipped'
                stage1_conf = 0
            
            final_species = result.get('final_species', 'NotBigCat')
            final_conf = result.get('final_confidence', 0)
            
            # Print results
            print(f"  Stage 0: {stage0_label} (animal={is_animal})")
            if stage1:
                print(f"  Stage 1: {stage1_label} ({stage1_conf:.2%})")
            if is_bigcat and stage2:
                print(f"  Stage 2: {final_species} ({final_conf:.2%})")
            print(f"  Result: {final_species}")
            print(f"  Time: {elapsed_time:.2f}s")
            
            # Determine correctness
            expected_species = expected.get('expected_species')
            if expected_species:
                # Should be a big cat
                correct = (is_bigcat and final_species.lower() == expected_species.lower())
                if correct:
                    print(f"  ✓ CORRECT! Predicted {final_species}")
                else:
                    print(f"  ✗ FAILED! Expected {expected_species}, got {final_species}")
                
                results.add_result('Video', name, expected_species, final_species, 
                                 correct, elapsed_time, {'is_bigcat': is_bigcat})
            else:
                # Should NOT be a big cat
                correct = not is_bigcat
                expected_label = expected.get('expected_stage1', 'NotBigCat')
                if correct:
                    print(f"  ✓ CORRECT! Not a big cat")
                else:
                    print(f"  ✗ FAILED! Should not be a big cat")
                
                results.add_result('Video', name, expected_label, final_species, 
                                 correct, elapsed_time, {'is_bigcat': is_bigcat})
        else:
            print(f"  ✗ HTTP Error {response.status_code}")
            results.add_result('Video', name, 'N/A', 'ERROR', False, 0)
            
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
        results.add_result('Video', name, 'N/A', 'EXCEPTION', False, 0)


def main():
    """Run comprehensive test suite"""
    print("="*80)
    print("COMPREHENSIVE WILDLIFE CLASSIFICATION API TEST SUITE")
    print("="*80)
    print(f"API Endpoint: {API_URL}")
    print(f"Timeout: {TIMEOUT}s")
    
    results = TestResults()
    
    # Test Big Cat Images
    print("\n" + "="*80)
    print("TESTING BIG CAT IMAGES")
    print("="*80)
    for name, data in BIGCAT_IMAGES.items():
        test_image(data['url'], name, data, results)
        time.sleep(0.5)
    
    # Test Other Animals
    print("\n" + "="*80)
    print("TESTING OTHER ANIMALS")
    print("="*80)
    for name, data in OTHER_ANIMALS.items():
        test_image(data['url'], name, data, results)
        time.sleep(0.5)
    
    # Test Non-Animals
    print("\n" + "="*80)
    print("TESTING NON-ANIMALS")
    print("="*80)
    for name, data in NON_ANIMALS.items():
        test_image(data['url'], name, data, results)
        time.sleep(0.5)
    
    # Test Videos
    print("\n" + "="*80)
    print("TESTING VIDEOS")
    print("="*80)
    available_videos = get_available_videos()
    if available_videos:
        for name, data in available_videos.items():
            test_video(data['path'], name, data, results)
            time.sleep(0.5)
    else:
        print("  ⚠ No video files found")
    
    # Print summary
    results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
