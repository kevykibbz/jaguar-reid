"""
Test the /jaguars endpoint to verify image data structure
"""
import requests
import json

def test_jaguars_endpoint():
    """Fetch jaguars and inspect the data structure"""
    url = "http://localhost:8000/jaguars"
    
    try:
        response = requests.get(url, timeout=60)  # Increased timeout for model loading
        
        if response.status_code == 200:
            data = response.json()
            jaguars = data.get('jaguars', [])
            
            print(f"\n{'='*70}")
            print(f"SUCCESS: Retrieved {len(jaguars)} jaguars")
            print(f"{'='*70}\n")
            
            if jaguars:
                print("First jaguar data structure:")
                print(json.dumps(jaguars[0], indent=2))
                
                print(f"\n{'='*70}")
                print("Image data for all jaguars:")
                print(f"{'='*70}\n")
                
                for jag in jaguars:
                    jaguar_name = jag.get('name', 'Unknown')
                    images = jag.get('images', [])
                    image_url = jag.get('image_url')
                    
                    print(f"\n{jaguar_name}:")
                    print(f"  - Top-level image_url: {image_url}")
                    print(f"  - Images array length: {len(images)}")
                    
                    if images:
                        for i, img in enumerate(images):
                            print(f"    [{i}] url: {img.get('url')}")
                            print(f"        path: {img.get('path')}")
                            print(f"        storage: {img.get('storage')}")
                    else:
                        print("    (No images in array)")
            else:
                print("No jaguars found in database")
                
        else:
            print(f"ERROR: Server returned {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend server")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nERROR: {str(e)}")


if __name__ == "__main__":
    test_jaguars_endpoint()
