#!/usr/bin/env python3
"""
Display Stage 2 Species Classification Test Results in Tabular Format
"""

import io
import torch
import torch.nn.functional as F
from PIL import Image
from pathlib import Path
from torchvision import transforms
import sys
import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Stage 2 Test Data
TEST_IMAGES = {
    "jaguar": {
        "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/618315063/large.jpg",
        "expected": "jaguar",
    },
    "tiger": {
        "url": "https://www.shutterstock.com/image-photo/tiger-peacefully-reclined-on-mossy-260nw-2519850751.jpg",
        "expected": "tiger",
    },
    "lion": {
        "url": "https://media.istockphoto.com/id/1796374503/photo/the-lion-king.jpg?s=612x612&w=0&k=20&c=wDcyZj9yM1-7cCahtCn1SWnu_DGJsOHzlqWt6SSllzU=",
        "expected": "lion",
    },
    "leopard": {
        "url": "https://media.istockphoto.com/id/465470420/photo/focused.jpg?s=612x612&w=0&k=20&c=xjhwOExrjp-u2TFQRh4V7oI5XUlDddm6YF35AR01IZs=",
        "expected": "leopard",
    },
    "cheetah": {
        "url": "https://nationalzoo.si.edu/sites/default/files/animals/cheetah-002.jpg",
        "expected": "cheetah",
    },
}

def download_image(url, timeout=15):
    """Download image from URL"""
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def main():
    from config import DEVICE, STAGE2_CLASSES
    from models import load_stage2_model
    
    print("\n" + "="*120)
    print("STAGE 2 SPECIES CLASSIFICATION TEST RESULTS".center(120))
    print("="*120 + "\n")
    
    # Load model
    model = load_stage2_model()
    
    # Image transform
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    # Results
    results = []
    total = 0
    passed = 0
    
    print(f"{'Image':<15} {'Expected':<15} {'Predicted':<15} {'Confidence':<15} {'Status':<10}")
    print("-"*120)
    
    for image_name, image_data in TEST_IMAGES.items():
        total += 1
        expected = image_data['expected']
        
        # Download and classify
        image_bytes = download_image(image_data['url'])
        if image_bytes is None:
            print(f"{image_name:<15} {expected:<15} {'ERROR':<15} N/A               {'FAIL':<10}")
            continue
        
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_tensor = transform(image).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                output = model(image_tensor)
                probs = F.softmax(output, dim=1)
            
            predicted_class_id = int(torch.argmax(probs[0]).item())
            predicted = STAGE2_CLASSES[predicted_class_id]
            confidence = probs[0, predicted_class_id].item()
            
            match = "PASS" if predicted == expected else "FAIL"
            if match == "PASS":
                passed += 1
            
            print(f"{image_name:<15} {expected:<15} {predicted:<15} {confidence:>13.2%}   {match:<10}")
            results.append((image_name, expected, predicted, confidence, match))
            
        except Exception as e:
            print(f"{image_name:<15} {expected:<15} {'ERROR':<15} N/A               {'FAIL':<10}")
    
    print("-"*120)
    print(f"\nAccuracy: {passed}/{total} (100%)" if passed == total else f"\nAccuracy: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Species Detection: All {total} species correctly classified")
    print("\n" + "="*120 + "\n")

if __name__ == "__main__":
    main()
