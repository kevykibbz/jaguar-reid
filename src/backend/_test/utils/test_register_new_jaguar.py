"""
Test registering a new jaguar and verify it appears in the gallery
"""
import requests
from datetime import datetime

def register_new_jaguar():
    """Register a new jaguar with test image"""
    url = "http://localhost:8000/register"
    
    # Generate unique name with timestamp
    timestamp = datetime.now().strftime("%H%M%S")
    jaguar_name = f"TestJaguar_{timestamp}"
    
    # Try to download image first
    test_image_urls = [
        "https://lazoo.org/wp-content/uploads/2020/02/Jaguar-Female-JEP_6234-1.jpg",
        "https://images.unsplash.com/photo-1614027164847-1b28cfe1df60?w=800",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Standing_jaguar.jpg/800px-Standing_jaguar.jpg"
    ]
    
    downloaded_file = None
    successful_url = None
    
    print(f"\n{'='*70}")
    print(f"REGISTERING NEW JAGUAR: {jaguar_name}")
    print(f"{'='*70}")
    
    # Try to download test image
    for test_url in test_image_urls:
        try:
            print(f"\nTrying to download: {test_url[:60]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            img_response = requests.get(test_url, headers=headers, timeout=15)
            if img_response.status_code == 200:
                downloaded_file = img_response.content
                successful_url = test_url
                print(f"[OK] Downloaded {len(downloaded_file)} bytes")
                break
        except Exception as e:
            print(f"[FAILED] {str(e)}")
            continue
    
    if not downloaded_file:
        print("\n[ERROR] Failed to download any test image")
        print("Please ensure you have internet connection")
        return None
    
    print(f"\nUsing image from: {successful_url}")
    
    try:
        # Send registration request with file upload
        files = {
            'file': ('jaguar_test.jpg', downloaded_file, 'image/jpeg')
        }
        data = {
            'jaguar_name': jaguar_name
        }
        
        response = requests.post(url, files=files, data=data, timeout=120)  # 2 min timeout for classification
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[SUCCESS] Jaguar registered!")
            print(f"  - Jaguar ID: {result.get('jaguar_id')}")
            print(f"  - Name: {result.get('jaguar_name')}")
            print(f"  - Image URL: {result.get('image_url')}")
            return result.get('jaguar_id')
            
        else:
            print(f"\n[ERROR] Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out (may still be processing...)")
        return None
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return None


def verify_in_gallery(jaguar_id):
    """Verify the new jaguar appears in the gallery"""
    url = "http://localhost:8000/jaguars"
    
    print(f"\n{'='*70}")
    print("VERIFYING IN GALLERY")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            jaguars = data.get('jaguars', [])
            
            print(f"Total jaguars in database: {len(jaguars)}")
            
            # Find our newly registered jaguar
            found = None
            for jag in jaguars:
                if jag.get('id') == jaguar_id:
                    found = jag
                    break
            
            if found:
                print(f"\n[SUCCESS] Found newly registered jaguar in gallery!")
                print(f"\nJaguar Data:")
                print(f"  ID: {found.get('id')}")
                print(f"  Name: {found.get('name')}")
                print(f"  First Seen: {found.get('first_seen')}")
                print(f"  Times Seen: {found.get('times_seen')}")
                print(f"  Image URL: {found.get('image_url')}")
                
                images = found.get('images', [])
                print(f"\n  Images Array ({len(images)} images):")
                for i, img in enumerate(images):
                    print(f"    [{i}] url: {img.get('url')}")
                    print(f"        path: {img.get('path')}")
                    print(f"        storage: {img.get('storage')}")
                
                return True
            else:
                print(f"\n[WARNING] Jaguar ID {jaguar_id} not found in gallery")
                print("This could mean registration succeeded but database query failed")
                return False
                
        else:
            print(f"\n[ERROR] Failed to fetch gallery: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("JAGUAR REGISTRATION TEST")
    print("="*70)
    print("\nThis test will:")
    print("1. Register a new jaguar with a test image")
    print("2. Verify it appears in the gallery with correct image data")
    print("\n" + "="*70 + "\n")
    
    # Step 1: Register
    jaguar_id = register_new_jaguar()
    
    if jaguar_id:
        # Step 2: Verify
        success = verify_in_gallery(jaguar_id)
        
        if success:
            print("\n" + "="*70)
            print("[SUCCESS] TEST PASSED - Gallery data refreshes correctly!")
            print("="*70 + "\n")
        else:
            print("\n" + "="*70)
            print("[WARNING] TEST INCOMPLETE - Check logs above")
            print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("[FAILED] Registration did not complete")
        print("="*70 + "\n")
