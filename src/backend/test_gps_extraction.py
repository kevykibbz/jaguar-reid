#!/usr/bin/env python3
"""Test GPS extraction from registration endpoint"""

import requests
import json

url = 'http://localhost:8000/register'
files = {'file': open('assets/images/ssssssssssssssssssStanding_jaguar.jpg', 'rb')}
data = {'jaguar_name': 'test_gps_jaguar_v2'}

try:
    print("Sending registration request...")
    response = requests.post(url, files=files, data=data, timeout=120)
    print(f'Status: {response.status_code}\n')
    
    result = response.json()
    print('=== Full Response ===')
    print(json.dumps(result, indent=2))
    
    # Show GPS specifically
    if result.get('gps'):
        print('\n=== GPS INFORMATION ===')
        print(f'Has GPS: {result["gps"].get("has_gps")}')
        if result['gps'].get('latitude'):
            print(f'Latitude:  {result["gps"]["latitude"]:.4f}°')
        if result['gps'].get('longitude'):
            print(f'Longitude: {result["gps"]["longitude"]:.4f}°')
            
        # Google Maps link
        if result['gps'].get('latitude') and result['gps'].get('longitude'):
            lat, lon = result['gps']['latitude'], result['gps']['longitude']
            print(f'\nGoogle Maps: https://maps.google.com/?q={lat},{lon}')
except Exception as e:
    print(f'Error: {e}')
