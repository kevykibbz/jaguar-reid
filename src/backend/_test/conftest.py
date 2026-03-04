"""
Pytest configuration and shared fixtures for wildlife classification tests.

This module provides:
- Shared fixtures for API clients
- Test data loaders
- Common setup/teardown functions
- Pytest hooks for customization
"""

import pytest
import httpx
from pathlib import Path
import sys

# Add parent directory to path for imports
TEST_DIR = Path(__file__).parent
BACKEND_DIR = TEST_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 180.0  # Increased for CPU inference


# ============================================================================
# Fixtures - API Client
# ============================================================================

@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API endpoints."""
    return API_BASE_URL


@pytest.fixture(scope="session")
def api_client():
    """
    Create a reusable HTTP client for API tests.
    Uses session scope to reuse connection pool.
    """
    with httpx.Client(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
        yield client


@pytest.fixture(scope="function")
def async_api_client():
    """
    Create an async HTTP client for async API tests.
    Uses function scope for test isolation.
    """
    client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT)
    yield client
    # Cleanup is handled automatically by AsyncClient


# ============================================================================
# Fixtures - File Paths
# ============================================================================

@pytest.fixture(scope="session")
def test_dir():
    """Path to the test directory."""
    return TEST_DIR


@pytest.fixture(scope="session")
def fixtures_dir():
    """Path to the fixtures directory."""
    return TEST_DIR / "fixtures"


@pytest.fixture(scope="session")
def assets_dir():
    """Path to the assets directory."""
    return BACKEND_DIR / "assets"


@pytest.fixture(scope="session")
def videos_dir(assets_dir):
    """Path to the test videos directory."""
    return assets_dir / "videos"


# ============================================================================
# Fixtures - Test Data
# ============================================================================

@pytest.fixture(scope="session")
def test_image_urls(fixtures_dir):
    """Load test image URLs from fixtures."""
    urls_file = fixtures_dir / "test_image_urls.txt"
    if not urls_file.exists():
        return {}
    
    urls = {}
    with open(urls_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '->' in line:
                # Parse format: "1. URL ->label"
                parts = line.split('->')
                if len(parts) == 2:
                    url_part = parts[0].split('.', 1)
                    if len(url_part) == 2:
                        url = url_part[1].strip()
                        label = parts[1].strip()
                        urls[label] = url
    return urls


@pytest.fixture(scope="session")
def test_videos(videos_dir):
    """Get available test videos."""
    if not videos_dir.exists():
        return {}
    
    videos = {}
    for video_file in videos_dir.glob("*.mp4"):
        videos[video_file.stem] = str(video_file)
    return videos


# ============================================================================
# Fixtures - Server Health Check
# ============================================================================

@pytest.fixture(scope="session")
def check_server_running(api_client):
    """
    Check if the API server is running before tests start.
    This is NOT autouse - integration tests should explicitly use it.
    """
    try:
        response = api_client.get("/health", timeout=30.0)  # Increased timeout for model loading
        if response.status_code == 200:
            print("\n✓ API server is running and healthy")
            return True
        else:
            pytest.skip(
                f"API server returned status {response.status_code}. "
                "Start the server with: python start_dev.py"
            )
    except httpx.ConnectError:
        pytest.skip(
            "Cannot connect to API server at http://localhost:8000. "
            "Start the server with: python start_dev.py"
        )
    except httpx.TimeoutException:
        pytest.skip(
            "API server health check timed out. Server may still be loading models. "
            "Wait a moment and try again."
        )
    except Exception as e:
        pytest.skip(f"Error checking server health: {str(e)}")


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "video: mark test as a video processing test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically based on location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add markers based on test name
        if "api" in item.nodeid.lower():
            item.add_marker(pytest.mark.api)
        if "video" in item.nodeid.lower():
            item.add_marker(pytest.mark.video)
            item.add_marker(pytest.mark.slow)


def pytest_report_header(config):
    """Add custom header to pytest report."""
    return [
        "Wildlife Classification System - Test Suite",
        f"API Endpoint: {API_BASE_URL}",
        f"Timeout: {API_TIMEOUT}s"
    ]


# ============================================================================
# Helper Functions (can be imported by tests)
# ============================================================================

def assert_valid_prediction_response(response_data):
    """
    Validate that a prediction response has the expected structure.
    
    Args:
        response_data (dict): The API response JSON
    """
    assert "success" in response_data
    assert response_data["success"] is True
    assert "stage0" in response_data
    assert "stage1" in response_data
    
    # Stage 0 checks
    stage0 = response_data["stage0"]
    assert "is_animal" in stage0
    assert "label" in stage0
    assert "confidence" in stage0
    
    # If animal was detected, stage1 should be present
    if stage0.get("is_animal"):
        stage1 = response_data.get("stage1")
        if stage1:  # May be None if not a big cat
            assert "is_bigcat" in stage1
            assert "label" in stage1
            assert "confidence" in stage1


def assert_bigcat_prediction(response_data, expected_species):
    """
    Assert that a big cat was correctly identified.
    
    Args:
        response_data (dict): The API response JSON
        expected_species (str): Expected species name
    """
    assert_valid_prediction_response(response_data)
    
    stage1 = response_data.get("stage1")
    assert stage1 is not None, "Stage 1 should not be None for big cats"
    assert stage1.get("is_bigcat") is True, "Should be classified as big cat"
    
    final_species = response_data.get("final_species")
    assert final_species is not None, "Final species should be present"
    assert final_species.lower() == expected_species.lower(), \
        f"Expected {expected_species}, got {final_species}"


def assert_not_bigcat_prediction(response_data):
    """
    Assert that an image was correctly identified as not a big cat.
    
    Args:
        response_data (dict): The API response JSON
    """
    assert_valid_prediction_response(response_data)
    
    stage1 = response_data.get("stage1")
    # Either stage1 is None (non-animal) or is_bigcat is False
    if stage1:
        assert stage1.get("is_bigcat") is False, \
            "Should not be classified as big cat"
