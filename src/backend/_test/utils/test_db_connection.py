"""Quick database connection test"""
from database.database_manager import get_database

try:
    db = get_database()
    print("✓ Database connected successfully!")
    
    jaguars = db.list_jaguars()
    print(f"✓ Found {len(jaguars)} registered jaguars")
    
    if jaguars:
        print("\nJaguars in database:")
        for j in jaguars[:10]:
            # First jaguar - print all keys to understand structure
            if jaguars.index(j) == 0:
                print(f"  DEBUG - Available keys: {list(j.keys())}")
                if j.get('images'):
                    print(f"  DEBUG - Image structure: {j['images'][0]}")
            
            jaguar_id = j.get('jaguar_id', j.get('id', 'N/A'))
            name = j.get('name', 'Unknown')
            num_images = len(j.get("images", []))
            print(f"  - {name} (ID: {jaguar_id}): {num_images} images")
            if num_images > 0:
                for img in j.get("images", [])[:3]:
                    # Changed from image_url to url!
                    print(f"    • Image URL: {img.get('url', 'N/A')}")
    else:
        print("  (No jaguars registered yet)")
        
    # Check statistics
    stats = db.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total jaguars: {stats.get('total_jaguars', 0)}")
    print(f"  Total images: {stats.get('total_images', 0)}")
    print(f"  Total sightings: {stats.get('total_sightings', 0)}")
    
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    import traceback
    traceback.print_exc()
