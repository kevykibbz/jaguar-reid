"""
Download pre-trained models from Azure Storage.
Run this script before building Docker images or running locally.
"""
import os
import sys
import requests
from pathlib import Path

# Azure Storage URLs (you'll update these after uploading)
MODEL_URLS = {
    "convnext_arcface_jaguar_final.pth": "https://jaguarreidmodels.blob.core.windows.net/models/convnext_arcface_jaguar_final.pth",
    "sam_vit_b_01ec64.pth": "https://jaguarreidmodels.blob.core.windows.net/models/sam_vit_b_01ec64.pth",
    "yolov8n.pt": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
}

# Destination paths
BACKEND_DIR = Path(__file__).parent / "src" / "backend"
MODELS_DIR = BACKEND_DIR / "models"

DESTINATIONS = {
    "convnext_arcface_jaguar_final.pth": MODELS_DIR / "convnext_arcface_jaguar_final.pth",
    "sam_vit_b_01ec64.pth": BACKEND_DIR / "sam_vit_b_01ec64.pth",
    "yolov8n.pt": BACKEND_DIR / "yolov8n.pt"
}

def download_file(url, dest_path):
    """Download file with progress indicator."""
    print(f"Downloading {dest_path.name}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f}MB / {total_size / 1024 / 1024:.1f}MB)", end='')
        
        print(f"\nDownloaded {dest_path.name}")
        return True
        
    except Exception as e:
        print(f"\nFailed to download {dest_path.name}: {e}")
        return False

def check_existing_models():
    """Check which models already exist."""
    existing = []
    missing = []
    
    for name, path in DESTINATIONS.items():
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            existing.append(f"  ✓ {name} ({size_mb:.1f}MB)")
        else:
            missing.append(name)
    
    return existing, missing

def main():
    print("=" * 60)
    print("Jaguar Re-ID Model Downloader")
    print("=" * 60)
    
    # Check existing models
    existing, missing = check_existing_models()
    
    if existing:
        print("\nAlready downloaded:")
        for item in existing:
            print(item)
    
    if not missing:
        print("\nAll models are already downloaded!")
        return 0
    
    print(f"\nNeed to download {len(missing)} model(s):")
    for name in missing:
        print(f"  - {name}")
    
    print("\n" + "=" * 60)
    
    # Download missing models
    failed = []
    for name in missing:
        url = MODEL_URLS[name]
        dest = DESTINATIONS[name]
        
        if not download_file(url, dest):
            failed.append(name)
    
    print("\n" + "=" * 60)
    
    if failed:
        print(f"Failed to download {len(failed)} model(s):")
        for name in failed:
            print(f"  - {name}")
        print("\nPlease check your internet connection and the URLs in download_models.py")
        return 1
    else:
        print("All models downloaded successfully!")
        print("\nYou can now:")
        print("  1. Run locally: docker-compose up")
        print("  2. Build for Azure: docker build ./src/backend")
        return 0

if __name__ == "__main__":
    sys.exit(main())
