"""Test the /jaguars API endpoint"""
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("Testing GET /jaguars endpoint...")
print("="*70)

response = client.get("/jaguars")
data = response.json()

print(f"Status Code: {response.status_code}")
print(f"Success: {data.get('success')}")
print(f"Count: {data.get('count')}")
print("\nFirst jaguar structure:")

if data.get('jaguars'):
    first_jaguar = data['jaguars'][0]
    import json
    print(json.dumps(first_jaguar, indent=2))
    
    print(f"\nHas 'images' key: {'images' in first_jaguar}")
    print(f"Has 'image_url' key: {'image_url' in first_jaguar}")
    
    if 'images' in first_jaguar and first_jaguar['images']:
        print(f"\nFirst image in images array:")
        print(json.dumps(first_jaguar['images'][0], indent=2))
else:
    print("No jaguars returned")
