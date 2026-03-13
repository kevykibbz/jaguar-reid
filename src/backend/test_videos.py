#!/usr/bin/env python3
"""Test video classification"""
import requests
import os
import json

def test_video(video_path, description=""):
    """Test video classification endpoint"""
    url = "http://localhost:8000/classify"
    
    print("\n" + "="*60)
    print(f"Video: {os.path.basename(video_path)}")
    if description:
        print(f"Description: {description}")
    print("="*60)
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
            response = requests.post(url, files=files, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            # Print stage results
            stage2 = result.get('stage2', {})
            stage3 = result.get('stage3', {})
            
            if stage2:
                species = stage2.get('species', 'unknown')
                confidence = stage2.get('confidence', 0) * 100
                print(f"Species: {species} ({confidence:.1f}% confidence)")
                
                if species == 'jaguar' and stage3:
                    if stage3.get('match'):
                        jaguar_name = stage3.get('jaguar_name', 'unknown')
                        jaguar_id = stage3.get('jaguar_id', 'unknown')
                        similarity = stage3.get('similarity', 0) * 100
                        print(f"Individual: {jaguar_name} ({jaguar_id})")
                        print(f"Similarity: {similarity:.1f}%")
                        print(f"Status: {stage3.get('status', 'unknown')}")
                    else:
                        print("Individual: NEW JAGUAR (auto-registered)")
                elif species != 'jaguar':
                    print("Stage 3: Not a jaguar, skipped re-identification")
            
            # Print frame count if available
            if 'frames_analyzed' in result:
                print(f"\nFrames analyzed: {result['frames_analyzed']}")
                print(f"Duration: {result.get('video_duration_seconds', 0):.1f}s")
            
            return result
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return None

if __name__ == "__main__":
    base_path = r"c:\Users\user\techzone\patterns-ai-wildlife\src\backend\assets\videos"
    
    videos = [
        ("cheetah.mp4", "Cheetah video"),
        ("elephant.mp4", "Elephant video (non-bigcat)"),
        ("gazelle.mp4", "Gazelle video (prey animal)"),
        ("leopard.mp4", "Leopard video"),
        ("lion.mp4", "Lion video"),
    ]
    
    print("="*60)
    print("TESTING ALL VIDEOS")
    print("="*60)
    
    results = []
    for video_name, description in videos:
        video_path = os.path.join(base_path, video_name)
        if os.path.exists(video_path):
            result = test_video(video_path, description)
            results.append((video_name, result))
        else:
            print(f"\n✗ Video not found: {video_name}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total videos tested: {len([r for r in results if r[1] is not None])}")
