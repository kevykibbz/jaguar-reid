"""
Debug script to test the /jaguars API endpoint
"""
import sys
sys.path.insert(0, r'c:\Users\user\techzone\patterns-ai-wildlife\src\backend')

from database.database_manager import JaguarDatabase

# Initialize database
db = JaguarDatabase(r"c:\Users\user\techzone\patterns-ai-wildlife\src\backend\database\jaguars.db")

print("=" * 80)
print("API /jaguars ENDPOINT DEBUG")
print("=" * 80)

# Get all jaguars using the same method the API uses
all_jaguars = db.list_jaguars()

print(f"\nTotal jaguars from list_jaguars(): {len(all_jaguars)}\n")

# Show the order they come back in
print("Order of jaguars:")
print("-" * 80)
for idx, jaguar in enumerate(all_jaguars, 1):
    print(f"{idx}. {jaguar['name']} (ID: {jaguar['id']})")
    print(f"   Times seen: {jaguar.get('times_seen', 0)}")
    print(f"   First seen: {jaguar.get('first_seen', 'N/A')}")
    if 'created_at' in jaguar:
        print(f"   Created at: {jaguar['created_at']}")
    print()

# Simulate pagination (page 1, limit 12)
print("\n" + "=" * 80)
print("SIMULATING API CALL: /jaguars?page=1&limit=12")
print("=" * 80)
page = 1
limit = 12
start_idx = (page - 1) * limit
end_idx = start_idx + limit
paginated = all_jaguars[start_idx:end_idx]

print(f"\nReturning jaguars {start_idx + 1} to {min(end_idx, len(all_jaguars))}:\n")
for idx, jaguar in enumerate(paginated, 1):
    print(f"{idx}. {jaguar['name']}")

print("\n" + "=" * 80)
