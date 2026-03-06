"""
Simple API test script to verify video classification
"""
import requests
import json
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/classify"
VIDEO_PATH = Path(__file__).parent.parent / "assets" / "videos" / "leopard.mp4"

def test_video_classification(video_path):
    """Test video classification via API"""
    print(f"\n{'='*70}")
    print(f"Testing Video Classification API")
    print(f"{'='*70}")
    print(f"Video: {video_path.name}")
    print(f"Path: {video_path}")
    print(f"API Endpoint: {API_URL}")
    print(f"{'='*70}\n")
    
    # Check if file exists
    if not video_path.exists():
        print(f"❌ ERROR: Video file not found at {video_path}")
        return
    
    # Get file size
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size_mb:.2f} MB")
    
    # Open and send video file
    try:
        with open(video_path, 'rb') as video_file:
            files = {'file': (video_path.name, video_file, 'video/mp4')}
            
            print(f"🚀 Sending request to API...")
            response = requests.post(API_URL, files=files, timeout=120)
            
            print(f"\n📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Classification Successful!\n")
                print(json.dumps(result, indent=2))
                
                # Print key results
                if result.get('success'):
                    print(f"\n{'='*70}")
                    print(f"🎯 CLASSIFICATION RESULTS:")
                    print(f"{'='*70}")
                    
                    if 'final_species' in result:
                        print(f"Species: {result['final_species'].upper()}")
                        print(f"Confidence: {result['final_confidence']:.2%}")
                    
                    if 'video_info' in result:
                        info = result['video_info']
                        print(f"\nVideo Info:")
                        print(f"  Duration: {info.get('duration', 0):.1f}s")
                        print(f"  FPS: {info.get('fps', 0):.1f}")
                        print(f"  Frames processed: {info.get('extracted_frames', 0)}")
                    
                    if 'stage2' in result and result['stage2']:
                        print(f"\nSpecies Voting:")
                        votes = result['stage2'].get('frame_votes', {})
                        for species, count in sorted(votes.items(), key=lambda x: x[1], reverse=True):
                            print(f"  {species}: {count} frames")
                    
                    print(f"{'='*70}\n")
                else:
                    print(f"\n⚠️ Classification unsuccessful: {result.get('error', 'Unknown error')}")
            else:
                print(f"\n❌ API Error: {response.status_code}")
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to API at {API_URL}")
        print("Make sure the backend server is running!")
    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Request timed out (video processing took too long)")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_video_classification(VIDEO_PATH)
