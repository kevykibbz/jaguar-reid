#!/usr/bin/env python3
"""Quick test script for jaguar classification"""
import requests
import sys

def test_classify(image_path):
    url = "http://localhost:8000/classify"
    
    with open(image_path, 'rb') as f:
        files = {'file': (image_path.split('\\')[-1], f, 'image/jpeg')}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("✓ Classification successful!")
        print(f"Stage 0: {result.get('stage0', {})}")
        print(f"Stage 1: {result.get('stage1', {})}")
        print(f"Stage 2: {result.get('stage2', {})}")
        print(f"Stage 3: {result.get('stage3', {})}")
        print(f"\nImage ID: {result.get('image_id')}")
        return result
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        return None

def test_gallery():
    url = "http://localhost:8000/jaguars"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        jaguars = response.json()
        print(f"\n✓ Gallery contains {len(jaguars)} jaguars:")
        for j in jaguars[:5]:
            print(f"  - {j['jaguar_id']}: {j['name']} ({j['image_count']} images)")
        return jaguars
    else:
        print(f"✗ Error: {response.status_code}")
        return None

if __name__ == "__main__":
    print("=== Test 1: Classify known jaguar ===")
    image = r"c:\Users\user\techzone\patterns-ai-wildlife\src\backend\database\images\JAG_0001.jpg"
    result = test_classify(image)
    
    print("\n=== Test 2: Check gallery ===")
    test_gallery()
