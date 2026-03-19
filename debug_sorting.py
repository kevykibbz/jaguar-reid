"""
Debug script to check jaguar sorting in the database
"""
import sqlite3
from datetime import datetime

# Connect to the database
db_path = r"c:\Users\user\techzone\patterns-ai-wildlife\src\backend\database\jaguars.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("JAGUAR DATABASE SORTING DEBUG")
print("=" * 80)

# Check all jaguars ordered by created_at DESC (newest first)
print("\n1. ALL JAGUARS (ordered by created_at DESC - newest first):")
print("-" * 80)
cursor.execute("""
    SELECT id, name, created_at, first_seen, last_seen, times_seen
    FROM jaguars
    ORDER BY created_at DESC
""")

jaguars = cursor.fetchall()
print(f"Total jaguars: {len(jaguars)}\n")

for idx, row in enumerate(jaguars, 1):
    print(f"{idx}. ID: {row['id']}")
    print(f"   Name: {row['name']}")
    print(f"   Created: {row['created_at']}")
    print(f"   First seen: {row['first_seen']}")
    print(f"   Last seen: {row['last_seen']}")
    print(f"   Times seen: {row['times_seen']}")
    print()

# Check the query used by list_jaguars()
print("\n2. QUERY USED BY list_jaguars() API:")
print("-" * 80)
cursor.execute("""
    SELECT 
        j.id, j.name, j.first_seen, j.last_seen, j.times_seen, j.created_at,
        i.image_url, i.local_path, i.storage_type, i.file_name
    FROM jaguars j
    LEFT JOIN images i ON j.id = i.jaguar_id
    ORDER BY j.created_at DESC
""")

print("First 10 results:")
for idx, row in enumerate(cursor.fetchall()[:10], 1):
    print(f"{idx}. {row['name']} (created: {row['created_at']})")

# Check if created_at values exist
print("\n3. CHECK FOR NULL created_at VALUES:")
print("-" * 80)
cursor.execute("""
    SELECT COUNT(*) as count
    FROM jaguars
    WHERE created_at IS NULL
""")
null_count = cursor.fetchone()['count']
print(f"Jaguars with NULL created_at: {null_count}")

# Check the most recent jaguar
print("\n4. MOST RECENT JAGUAR:")
print("-" * 80)
cursor.execute("""
    SELECT id, name, created_at, first_seen
    FROM jaguars
    ORDER BY created_at DESC
    LIMIT 1
""")
recent = cursor.fetchone()
if recent:
    print(f"ID: {recent['id']}")
    print(f"Name: {recent['name']}")
    print(f"Created: {recent['created_at']}")
    print(f"First seen: {recent['first_seen']}")

# Check if there are timestamp issues (string vs datetime)
print("\n5. CREATED_AT DATA TYPES:")
print("-" * 80)
cursor.execute("""
    SELECT id, name, created_at, typeof(created_at) as type
    FROM jaguars
    ORDER BY created_at DESC
    LIMIT 5
""")
print("Sample of recent jaguars with their created_at types:")
for row in cursor.fetchall():
    print(f"  {row['name']}: {row['created_at']} (type: {row['type']})")

conn.close()
print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
