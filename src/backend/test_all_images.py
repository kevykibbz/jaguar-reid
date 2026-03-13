#!/usr/bin/env python3
"""Test all available jaguar images"""
import requests
import os
from pathlib import Path

def test_image(image_path, description=""):
    url = "http://localhost:8000/classify"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            stage2 = result.get('stage2', {})
            stage3 = result.get('stage3', {})
            
            print(f"\n{'='*60}")
            print(f"Image: {os.path.basename(image_path)}")
            if description:
                print(f"Description: {description}")
            print(f"{'='*60}")
            
            # Stage 2 species
            species = stage2.get('species', 'unknown')
            confidence = stage2.get('confidence', 0)
            print(f"Species: {species} ({confidence*100:.1f}% confidence)")
            
            # Stage 3 individual ID
            if stage3:
                if stage3.get('match'):
                    print(f"Individual: {stage3['jaguar_name']} ({stage3['jaguar_id']})")
                    print(f"Similarity: {stage3['similarity']*100:.1f}%")
                    print(f"Status: {stage3['status']}")
                else:
                    print(f"Individual: NEW JAGUAR (auto-registered)")
                    if 'jaguar_id' in stage3:
                        print(f"  ID: {stage3['jaguar_id']}")
                        print(f"  Name: {stage3['jaguar_name']}")
            else:
                print("Stage 3: Not a jaguar, skipped re-identification")
            
            return result
        else:
            print(f"\n✗ Error for {os.path.basename(image_path)}: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"\n✗ Exception for {os.path.basename(image_path)}: {e}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("TESTING ALL JAGUAR IMAGES")
    print("="*60)
    
    # Test images from src/images
    image_dir = r"c:\Users\user\techzone\patterns-ai-wildlife\src\images"
    images = [
        ("jaguar_01.jpg", "Test jaguar image 1"),
        ("jaguar_02.jpg", "Test jaguar image 2"),
        ("final.jpg", "Final test image"),
    ]
    
    results = []
    for img_file, desc in images:
        img_path = os.path.join(image_dir, img_file)
        if os.path.exists(img_path):
            result = test_image(img_path, desc)
            results.append((img_file, result))
        else:
            print(f"\n✗ File not found: {img_path}")
    
    # Test database images
    print("\n" + "="*60)
    print("TESTING DATABASE JAGUAR IMAGES")
    print("="*60)
    
    db_image_dir = r"c:\Users\user\techzone\patterns-ai-wildlife\src\backend\database\images"
    if os.path.exists(db_image_dir):
        db_images = [f for f in os.listdir(db_image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        for img_file in db_images[:3]:  # Test first 3
            img_path = os.path.join(db_image_dir, img_file)
            result = test_image(img_path, "Database jaguar")
            results.append((img_file, result))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    jaguars_found = 0
    new_jaguars = 0
    known_jaguars = 0
    
    for img_file, result in results:
        if result and result.get('stage2', {}).get('species') == 'jaguar':
            jaguars_found += 1
            stage3 = result.get('stage3', {})
            if stage3.get('match'):
                known_jaguars += 1
            elif stage3:
                new_jaguars += 1
    
    print(f"Total images tested: {len(results)}")
    print(f"Jaguars identified: {jaguars_found}")
    print(f"  - Known jaguars: {known_jaguars}")
    print(f"  - New jaguars (auto-registered): {new_jaguars}")
