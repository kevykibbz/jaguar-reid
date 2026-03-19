"""Check images table in database"""
from database.database_manager import get_database
import sqlite3

try:
    db = get_database()
    
    # Direct SQL query to see raw image data
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM images LIMIT 20")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} image records in database:")
    print("\n" + "="*100)
    
    for row in rows:
        row_dict = dict(row)
        print(f"Image ID: {row_dict['id']}")
        print(f"  Jaguar ID: {row_dict['jaguar_id']}")
        print(f"  Image URL: {row_dict['image_url']}")
        print(f"  Local Path: {row_dict['local_path']}")
        print(f"  Storage Type: {row_dict['storage_type']}")
        print(f"  File Name: {row_dict['file_name']}")
        print(f"  Created: {row_dict['created_at']}")
        print("-"*100)
    
    # Also check jaguars table
    cursor.execute("SELECT id, name FROM jaguars")
    jaguars = cursor.fetchall()
    print(f"\nJaguars in database:")
    for jag in jaguars:
        print(f"  {jag['id']}: {jag['name']}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
