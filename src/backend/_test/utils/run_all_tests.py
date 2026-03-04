#!/usr/bin/env python3
"""
Comprehensive API Test Suite
Tests all images and videos via API calls

Usage:
    python run_all_tests.py              # Test everything
    python run_all_tests.py --images    # Test only images
    python run_all_tests.py --videos    # Test only videos
"""

import requests
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fixtures.test_images import BIGCAT_IMAGES, OTHER_ANIMALS, NON_ANIMALS
from fixtures.test_videos import BIGCAT_VIDEOS, OTHER_ANIMAL_VIDEOS, get_available_videos

API_URL = "http://localhost:8000"
TIMEOUT = 180  # 3 minutes for slow CPU inference


class TestResults:
    """Track test results"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.details = []
        self.times = []
    
    def add_pass(self, name: str, time: float, details: str = ""):
        self.total += 1
        self.passed += 1
        self.times.append(time)
        self.details.append({"name": name, "status": "✓ PASS", "time": time, "details": details})
    
    def add_fail(self, name: str, time: float, details: str = ""):
        self.total += 1
        self.failed += 1
        self.times.append(time)
        self.details.append({"name": name, "status": "✗ FAIL", "time": time, "details": details})
    
    def add_error(self, name: str, error: str):
        self.total += 1
        self.errors += 1
        self.details.append({"name": name, "status": "! ERROR", "time": 0, "details": error})
    
    def summary(self):
        avg_time = sum(self.times) / len(self.times) if self.times else 0
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "avg_time": avg_time,
            "accuracy": (self.passed / self.total * 100) if self.total > 0 else 0
        }


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_section(title: str):
    """Print a section header"""
    print(f"\n{title}")
    print("-"*80)


def test_image_url(name: str, url: str, expected: Dict) -> tuple:
    """Test a single image URL"""
    print(f"Testing: {name:<20}", end=" ", flush=True)
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/predict/url",
            json={"image_url": url},
            timeout=TIMEOUT
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"✗ FAIL ({elapsed_time:.2f}s) - HTTP {response.status_code}")
            return False, elapsed_time, f"HTTP {response.status_code}: {response.text[:100]}"
        
        result = response.json()
        stage1 = result.get('stage1')
        
        # Check if it's a big cat
        expected_species = expected.get('expected_species')
        if expected_species:
            # Should be classified as a big cat
            is_bigcat = stage1 and stage1.get('is_bigcat', False)
            final_species = result.get('final_species', '')
            
            if is_bigcat and final_species.lower() == expected_species.lower():
                conf = result.get('final_confidence', 0)
                print(f"✓ PASS ({elapsed_time:.2f}s) - {final_species} ({conf:.1%})")
                return True, elapsed_time, f"{final_species} ({conf:.1%})"
            else:
                print(f"✗ FAIL ({elapsed_time:.2f}s) - Expected {expected_species}, got {final_species if is_bigcat else 'NotBigCat'}")
                return False, elapsed_time, f"Expected {expected_species}, got {final_species if is_bigcat else 'NotBigCat'}"
        else:
            # Should NOT be a big cat
            is_bigcat = stage1 and stage1.get('is_bigcat', False) if stage1 else False
            
            if not is_bigcat:
                stage0 = result.get('stage0', {})
                label = stage0.get('label', 'Unknown')
                print(f"✓ PASS ({elapsed_time:.2f}s) - Correctly identified as not a big cat ({label})")
                return True, elapsed_time, f"NotBigCat ({label})"
            else:
                final_species = result.get('final_species', 'Unknown')
                print(f"✗ FAIL ({elapsed_time:.2f}s) - Incorrectly classified as {final_species}")
                return False, elapsed_time, f"Incorrectly classified as {final_species}"
        
    except Exception as e:
        print(f"! ERROR - {str(e)[:50]}")
        return None, 0, str(e)


def test_video_file(name: str, video_path: Path, expected: Dict) -> tuple:
    """Test a single video file"""
    print(f"Testing: {name:<20}", end=" ", flush=True)
    
    if not video_path.exists():
        print(f"! SKIP - File not found")
        return None, 0, "File not found"
    
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
        
        if response.status_code != 200:
            print(f"✗ FAIL ({elapsed_time:.2f}s) - HTTP {response.status_code}")
            return False, elapsed_time, f"HTTP {response.status_code}: {response.text[:100]}"
        
        result = response.json()
        stage1 = result.get('stage1')
        
        # Check if it's a big cat
        expected_species = expected.get('expected_species')
        if expected_species:
            # Should be classified as a big cat
            is_bigcat = stage1 and stage1.get('is_bigcat', False)
            final_species = result.get('final_species', '')
            
            if is_bigcat and final_species.lower() == expected_species.lower():
                conf = result.get('final_confidence', 0)
                print(f"✓ PASS ({elapsed_time:.2f}s) - {final_species} ({conf:.1%})")
                return True, elapsed_time, f"{final_species} ({conf:.1%})"
            else:
                print(f"✗ FAIL ({elapsed_time:.2f}s) - Expected {expected_species}, got {final_species if is_bigcat else 'NotBigCat'}")
                return False, elapsed_time, f"Expected {expected_species}, got {final_species if is_bigcat else 'NotBigCat'}"
        else:
            # Should NOT be a big cat
            is_bigcat = stage1 and stage1.get('is_bigcat', False) if stage1 else False
            
            if not is_bigcat:
                print(f"✓ PASS ({elapsed_time:.2f}s) - Correctly identified as not a big cat")
                return True, elapsed_time, "NotBigCat"
            else:
                final_species = result.get('final_species', 'Unknown')
                print(f"✗ FAIL ({elapsed_time:.2f}s) - Incorrectly classified as {final_species}")
                return False, elapsed_time, f"Incorrectly classified as {final_species}"
        
    except Exception as e:
        print(f"! ERROR - {str(e)[:50]}")
        return None, 0, str(e)


def test_all_images(results: TestResults):
    """Test all image URLs"""
    print_header("TESTING IMAGES VIA API")
    
    # Test Big Cats
    print_section("Big Cat Images (should be classified correctly)")
    for name, data in BIGCAT_IMAGES.items():
        success, elapsed, details = test_image_url(name, data['url'], data)
        if success is True:
            results.add_pass(f"Image: {name}", elapsed, details)
        elif success is False:
            results.add_fail(f"Image: {name}", elapsed, details)
        else:
            results.add_error(f"Image: {name}", details)
    
    # Test Other Animals
    print_section("Other Animals (should be NotBigCat)")
    for name, data in OTHER_ANIMALS.items():
        success, elapsed, details = test_image_url(name, data['url'], data)
        if success is True:
            results.add_pass(f"Image: {name}", elapsed, details)
        elif success is False:
            results.add_fail(f"Image: {name}", elapsed, details)
        else:
            results.add_error(f"Image: {name}", details)
    
    # Test Non-Animals
    print_section("Non-Animals (should be filtered)")
    for name, data in NON_ANIMALS.items():
        success, elapsed, details = test_image_url(name, data['url'], data)
        if success is True:
            results.add_pass(f"Image: {name}", elapsed, details)
        elif success is False:
            results.add_fail(f"Image: {name}", elapsed, details)
        else:
            results.add_error(f"Image: {name}", details)


def test_all_videos(results: TestResults):
    """Test all video files"""
    print_header("TESTING VIDEOS VIA API")
    
    available_videos = get_available_videos()
    
    if not available_videos:
        print("\n⚠️  No video files found. Skipping video tests.")
        return
    
    # Test Big Cat Videos
    print_section("Big Cat Videos (should be classified correctly)")
    for name, data in BIGCAT_VIDEOS.items():
        if name in available_videos:
            success, elapsed, details = test_video_file(name, data['path'], data)
            if success is True:
                results.add_pass(f"Video: {name}", elapsed, details)
            elif success is False:
                results.add_fail(f"Video: {name}", elapsed, details)
            else:
                results.add_error(f"Video: {name}", details)
    
    # Test Other Animal Videos
    print_section("Other Animal Videos (should be NotBigCat)")
    for name, data in OTHER_ANIMAL_VIDEOS.items():
        if name in available_videos:
            success, elapsed, details = test_video_file(name, data['path'], data)
            if success is True:
                results.add_pass(f"Video: {name}", elapsed, details)
            elif success is False:
                results.add_fail(f"Video: {name}", elapsed, details)
            else:
                results.add_error(f"Video: {name}", details)


def print_summary(results: TestResults):
    """Print test summary"""
    summary = results.summary()
    
    print_header("TEST SUMMARY")
    print(f"Total Tests:     {summary['total']}")
    print(f"✓ Passed:        {summary['passed']}")
    print(f"✗ Failed:        {summary['failed']}")
    print(f"! Errors:        {summary['errors']}")
    print(f"Accuracy:        {summary['accuracy']:.1f}%")
    if summary['avg_time'] > 0:
        print(f"Avg Time:        {summary['avg_time']:.2f}s")
    print("="*80)
    
    # Print details
    print("\nDetailed Results:")
    print("-"*80)
    for detail in results.details:
        time_str = f"{detail['time']:.2f}s" if detail['time'] > 0 else "N/A"
        print(f"{detail['status']:<8} {detail['name']:<30} {time_str:<8} {detail['details'][:40]}")
    print("="*80)
    
    return summary['failed'] + summary['errors']


def main():
    parser = argparse.ArgumentParser(description="Comprehensive API Test Suite")
    parser.add_argument('--images', action='store_true', help='Test only images')
    parser.add_argument('--videos', action='store_true', help='Test only videos')
    args = parser.parse_args()
    
    # If no specific flags, test everything
    test_images = args.images or not (args.images or args.videos)
    test_videos = args.videos or not (args.images or args.videos)
    
    print_header("WILDLIFE CLASSIFICATION API - COMPREHENSIVE TEST SUITE")
    print(f"API Endpoint: {API_URL}")
    print(f"Timeout: {TIMEOUT}s")
    print("="*80)
    
    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✓ API is healthy and ready")
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"✗ Cannot connect to API: {e}")
        print(f"\nMake sure the server is running:")
        print(f"  cd src/backend")
        print(f"  python start_dev.py")
        return 1
    
    results = TestResults()
    start_time = time.time()
    
    # Run tests
    if test_images:
        test_all_images(results)
    
    if test_videos:
        test_all_videos(results)
    
    total_time = time.time() - start_time
    
    # Print summary
    print(f"\n\nTotal Execution Time: {total_time:.2f}s")
    exit_code = print_summary(results)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
