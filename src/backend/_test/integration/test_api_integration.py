#!/usr/bin/env python3
"""
API Integration Tests for Two-Stage BigCat Classification System

Tests the FastAPI backend endpoints:
- POST /classify (file upload)
- POST /classify (image URL)
- GET /health
- GET /

Validates full HTTP request/response cycle with real model inference.
"""

import pytest
import httpx
import io
import asyncio
from PIL import Image
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def api_base_url():
    """API base URL"""
    return "http://localhost:8000"

@pytest.fixture(scope="module")
def http_client():
    """HTTP client for API testing"""
    return httpx.Client(timeout=60.0)

@pytest.fixture(scope="module")
def test_images():
    """Test image URLs"""
    return {
        "jaguar": {
            "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/618315063/large.jpg",
            "expected_species": "jaguar",
            "is_bigcat": True,
        },
        "dog": {
            "url": "https://images.unsplash.com/photo-1633722715463-d30628519d75?w=400",
            "expected_species": None,  # Not a cat, will be rejected by Stage 1
            "is_bigcat": False,
        },
        "elephant": {
            "url": "https://images.unsplash.com/photo-1564760055-a379b0cbbdda?w=400",
            "expected_species": None,  # Not a cat
            "is_bigcat": False,
        },
        "tiger": {
            "url": "https://www.shutterstock.com/image-photo/tiger-peacefully-reclined-on-mossy-260nw-2519850751.jpg",
            "expected_species": "tiger",
            "is_bigcat": True,
        },
        "lion": {
            "url": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=600",
            "expected_species": "lion",
            "is_bigcat": True,
        },
    }

# ============================================================================
# TEST CLASSES
# ============================================================================

class TestAPIBasic:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self, http_client, api_base_url):
        """GET / - Root endpoint"""
        print("\n[TEST] GET /")
        
        response = http_client.get(f"{api_base_url}/")
        
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        
        assert "message" in data
        assert data["status"] == "online"
        assert "version" in data
        
    def test_health_endpoint(self, http_client, api_base_url):
        """GET /health - Health check"""
        print("\n[TEST] GET /health")
        
        response = http_client.get(f"{api_base_url}/health")
        
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
        
        assert data["status"] == "healthy"
        assert data["models"]["stage1"] == "loaded"
        assert data["models"]["stage2"] == "loaded"


class TestAPIClassification:
    """Test image classification endpoints"""
    
    def test_classify_with_url_jaguar(self, http_client, api_base_url, test_images):
        """POST /classify - Jaguar (BigCat)"""
        test_data = test_images["jaguar"]
        
        print(f"\n[TEST] POST /classify - Jaguar (URL)")
        print(f"  URL: {test_data['url'][:60]}...")
        
        response = http_client.post(
            f"{api_base_url}/classify",
            data={"image_url": test_data['url']}
        )
        
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200
        
        result = response.json()
        print(f"\n  Response:")
        print(f"    Stage 1 (BigCat Filter):")
        print(f"      is_bigcat: {result['stage1']['is_bigcat']}")
        print(f"      confidence: {result['stage1']['confidence']:.4f}")
        print(f"    Stage 2 (Species Classifier):")
        print(f"      species: {result['stage2']['species']}")
        print(f"      confidence: {result['stage2']['confidence']:.4f}")
        print(f"    Final Result: {result['final_species']}")
        
        # Assertions
        assert result['success'] is True
        assert result['stage1']['is_bigcat'] is True
        assert result['stage2']['species'] == test_data['expected_species']
        assert result['final_species'] == test_data['expected_species']
        assert result['stage1']['confidence'] > 0.5
        assert result['stage2']['confidence'] > 0.5
        
    def test_classify_with_url_tiger(self, http_client, api_base_url, test_images):
        """POST /classify - Tiger (BigCat)"""
        test_data = test_images["tiger"]
        
        print(f"\n[TEST] POST /classify - Tiger (URL)")
        
        response = http_client.post(
            f"{api_base_url}/classify",
            data={"image_url": test_data['url']}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        print(f"  Species: {result['stage2']['species']}")
        print(f"  Confidence: {result['stage2']['confidence']:.4f}")
        
        assert result['stage1']['is_bigcat'] is True
        assert result['stage2']['species'] == test_data['expected_species']
        
    def test_classify_with_url_lion(self, http_client, api_base_url, test_images):
        """POST /classify - Lion (BigCat)"""
        test_data = test_images["lion"]
        
        print(f"\n[TEST] POST /classify - Lion (URL)")
        
        response = http_client.post(
            f"{api_base_url}/classify",
            data={"image_url": test_data['url']}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        print(f"  Species: {result['stage2']['species']}")
        print(f"  Confidence: {result['stage2']['confidence']:.4f}")
        
        assert result['stage1']['is_bigcat'] is True
        assert result['stage2']['species'] == test_data['expected_species']


class TestAPIErrorHandling:
    """Test error handling"""
    
    def test_missing_parameters(self, http_client, api_base_url):
        """POST /classify - No file or URL"""
        print("\n[TEST] POST /classify - Missing parameters")
        
        response = http_client.post(f"{api_base_url}/classify")
        
        print(f"  Status: {response.status_code}")
        assert response.status_code == 400
        
        error = response.json()
        print(f"  Error: {error['detail']}")
        assert "file or image_url" in error['detail'].lower()
    
    def test_invalid_url(self, http_client, api_base_url):
        """POST /classify - Invalid URL"""
        print("\n[TEST] POST /classify - Invalid URL")
        
        response = http_client.post(
            f"{api_base_url}/classify",
            data={"image_url": "https://invalid-url-that-does-not-exist-12345.com/image.jpg"}
        )
        
        print(f"  Status: {response.status_code}")
        assert response.status_code == 400
        
        error = response.json()
        print(f"  Error: {error['detail'][:80]}...")


class TestAPI_Stage1Filtering:
    """Test Stage 1 filtering behavior"""
    
    def test_bigcat_detection_consistency(self, http_client, api_base_url, test_images):
        """All confirmed BigCats should pass Stage 1"""
        print("\n[TEST] Stage 1 Filtering - BigCat Detection")
        
        bigcats = ["jaguar", "tiger", "lion"]
        
        for animal in bigcats:
            response = http_client.post(
                f"{api_base_url}/classify",
                data={"image_url": test_images[animal]['url']}
            )
            
            result = response.json()
            
            # Check if stage1 exists and has expected structure
            assert 'stage1' in result, f"Response missing 'stage1' key for {animal}"
            assert result['stage1'] is not None, f"stage1 is None for {animal} (may have been rejected by stage0)"
            assert 'is_bigcat' in result['stage1'], f"stage1 missing 'is_bigcat' key for {animal}"
            assert 'confidence' in result['stage1'], f"stage1 missing 'confidence' key for {animal}. Full stage1: {result['stage1']}"
            
            is_bigcat = result['stage1']['is_bigcat']
            confidence = result['stage1']['confidence']
            
            print(f"  {animal.upper()}: is_bigcat={is_bigcat}, confidence={confidence:.4f}")
            assert is_bigcat is True, f"{animal} should be detected as BigCat"
            assert confidence > 0.5


class TestAPI_Stage2Classification:
    """Test Stage 2 species classification"""
    
    def test_species_classification_confidence(self, http_client, api_base_url, test_images):
        """Species classification should have high confidence"""
        print("\n[TEST] Stage 2 Classification - Confidence Scores")
        
        test_species = ["jaguar", "tiger", "lion"]
        
        for animal in test_species:
            response = http_client.post(
                f"{api_base_url}/classify",
                data={"image_url": test_images[animal]['url']}
            )
            
            result = response.json()
            species = result['stage2']['species']
            confidence = result['stage2']['confidence']
            all_scores = result['stage2'].get('all_scores', {})
            
            print(f"\n  {animal.upper()}:")
            print(f"    Predicted: {species} ({confidence:.2%})")
            print(f"    All scores:")
            for sp, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"      {sp}: {score:.2%}")
            
            assert confidence > 0.5, f"Confidence too low for {animal}"


# ============================================================================
# SESSION SUMMARY
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print summary after all tests"""
    print("\n\n" + "="*110)
    print("API INTEGRATION TEST RESULTS".center(110))
    print("="*110)
    
    print(f"""
TEST COVERAGE:
  [1] Basic Endpoints
      - GET / (Root)
      - GET /health (Health Check)
  
  [2] Classification Endpoints
      - POST /classify with URL (Jaguar)
      - POST /classify with URL (Tiger)
      - POST /classify with URL (Lion)
  
  [3] Error Handling
      - Missing parameters
      - Invalid URLs
  
  [4] Stage 1 Filtering
      - BigCat detection consistency
  
  [5] Stage 2 Classifications
      - Species prediction confidence

EXPECTED RESULTS:
  - All endpoints respond with correct HTTP status codes
  - Stage 1 correctly detects BigCats (is_bigcat=true)
  - Stage 2 correctly identifies species with >50% confidence
  - Error responses include meaningful error messages
  
RUNNING FROM:
  cd c:\\Users\\user\\techzone\\patterns-ai-wildlife\\src\\backend
  python -m pytest _test/test_api_integration.py -v -s

BACKEND STARTUP:
  python main.py
  (or use: uvicorn main:app --reload)
""")
    
    print("="*110 + "\n")
