"""
Test video paths for wildlife classification
Organized by category for easy testing
"""

from pathlib import Path

# Base paths
BACKEND_DIR = Path(__file__).parent.parent.parent
ASSETS_DIR = BACKEND_DIR / "assets" / "videos"

# Big Cat Videos
BIGCAT_VIDEOS = {
    "cheetah": {
        "path": ASSETS_DIR / "cheetah.mp4",
        "expected_species": "cheetah",
        "description": "Cheetah video"
    },
    "leopard": {
        "path": ASSETS_DIR / "leopard.mp4",
        "expected_species": "leopard",
        "description": "Leopard video"
    },
    "lion": {
        "path": ASSETS_DIR / "lion.mp4",
        "expected_species": "lion",
        "description": "Lion video"
    }
}

# Other Animals
OTHER_ANIMAL_VIDEOS = {
    "elephant": {
        "path": ASSETS_DIR / "elephant.mp4",
        "expected_stage1": "NotBigCat",
        "description": "Elephant video"
    },
    "gazelle": {
        "path": ASSETS_DIR / "gazelle.mp4",
        "expected_stage1": "NotBigCat",
        "description": "Gazelle video"
    }
}

# All test videos combined
ALL_TEST_VIDEOS = {**BIGCAT_VIDEOS, **OTHER_ANIMAL_VIDEOS}

# Check which videos exist
def get_available_videos():
    """Returns only videos that exist on disk"""
    available = {}
    for name, info in ALL_TEST_VIDEOS.items():
        if info["path"].exists():
            available[name] = info
    return available
