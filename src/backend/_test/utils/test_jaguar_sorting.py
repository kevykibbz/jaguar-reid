"""
Test that jaguars are sorted by creation date (newest first)
"""
import requests
from datetime import datetime

def test_jaguar_sorting():
    """Verify jaguars are sorted newest first"""
    url = "http://localhost:8000/jaguars"
    
    print(f"\n{'='*70}")
    print("TESTING JAGUAR SORTING (Newest First)")
    print(f"{'='*70}\n")
    
    try:
        response = requests.get(url, timeout=120)  # Increased timeout for model loading
        
        if response.status_code == 200:
            data = response.json()
            jaguars = data.get('jaguars', [])
            
            print(f"Total jaguars: {len(jaguars)}")
            print(f"\nFirst 10 jaguars (should be newest first):\n")
            
            prev_date = None
            is_sorted = True
            
            for i, jag in enumerate(jaguars[:10]):
                name = jag.get('name', 'Unknown')
                first_seen = jag.get('first_seen', 'No date')
                
                # Parse date for comparison
                try:
                    current_date = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                    
                    # Check if sorted correctly (newer dates should come first)
                    if prev_date and current_date > prev_date:
                        is_sorted = False
                        print(f"  [{i+1}] {name[:30]:30} | {first_seen} [ERROR: Out of order!]")
                    else:
                        print(f"  [{i+1}] {name[:30]:30} | {first_seen}")
                    
                    prev_date = current_date
                except:
                    print(f"  [{i+1}] {name[:30]:30} | {first_seen}")
            
            print(f"\n{'='*70}")
            if is_sorted:
                print("[SUCCESS] Jaguars are correctly sorted (newest first)")
            else:
                print("[ERROR] Jaguars are NOT sorted correctly")
            print(f"{'='*70}\n")
            
            return is_sorted
        else:
            print(f"[ERROR] Failed to fetch jaguars: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    test_jaguar_sorting()
