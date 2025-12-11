#!/usr/bin/env python3
"""
Check what methods the relay endpoint accepts
"""

import requests

PI_IP = "192.168.1.69"
PORT = "5001"
BASE_URL = f"http://{PI_IP}:{PORT}"

print("Checking /relay endpoint methods...\n")

# Try OPTIONS request to see what methods are allowed
try:
    response = requests.options(f"{BASE_URL}/relay", timeout=5)
    print(f"OPTIONS request:")
    print(f"  Status: {response.status_code}")
    print(f"  Allowed methods: {response.headers.get('Allow', 'Not specified')}")
    print(f"  Headers: {dict(response.headers)}")
except Exception as e:
    print(f"OPTIONS failed: {e}")

print("\n" + "="*60)

# Try different methods
methods_to_test = ['GET', 'POST', 'PUT', 'DELETE']

for method in methods_to_test:
    try:
        if method == 'GET':
            response = requests.get(f"{BASE_URL}/relay", timeout=5)
        elif method == 'POST':
            response = requests.post(f"{BASE_URL}/relay", json={}, timeout=5)
        elif method == 'PUT':
            response = requests.put(f"{BASE_URL}/relay", json={}, timeout=5)
        elif method == 'DELETE':
            response = requests.delete(f"{BASE_URL}/relay", timeout=5)
        
        print(f"{method:6} /relay -> Status: {response.status_code} ({response.reason})")
        
        if response.status_code == 405:
            print(f"       Allow header: {response.headers.get('Allow', 'Not specified')}")
    except Exception as e:
        print(f"{method:6} /relay -> Error: {e}")

print("\n" + "="*60)
print("\nChecking if service is running latest code...")

# Check system status
try:
    response = requests.get(f"{BASE_URL}/status", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Service is running")
        print(f"  System: {data.get('system')}")
        print(f"  Timestamp: {data.get('timestamp')}")
        
        # Check if it's the latest version (has temperature)
        if 'temperature' in data:
            print(f"  Temperature: {data.get('temperature', {}).get('cpu_celsius')}°C")
            print("  ✓ Appears to be latest version (has temperature)")
        else:
            print("  ⚠️  May be older version (no temperature)")
except Exception as e:
    print(f"✗ Could not check status: {e}")










