#!/usr/bin/env python3
"""
Quick Relay Test Script
Debug and test relay control
"""

import requests
import json

# ============================================
# CONFIGURATION - Update these!
# ============================================
PI_IP = "192.168.1.100"     # Change to your Pi's IP
PORT = "5001"
USERNAME = "admin"
PASSWORD = "admin123"        # Change to your password
API_KEY = "your-api-key-change-this"  # Change to your API key

BASE_URL = f"http://{PI_IP}:{PORT}"

# ============================================
# Test Functions
# ============================================

def test_connection():
    """Test if we can reach the server"""
    print("\n1️⃣  Testing connection...")
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        print(f"   ✓ Server is reachable (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"   ✗ Cannot reach server: {e}")
        print(f"   Check: Is {BASE_URL} correct?")
        return False


def test_login():
    """Test login"""
    print("\n2️⃣  Testing login...")
    try:
        url = f"{BASE_URL}/login"
        payload = {"username": USERNAME, "password": PASSWORD}
        
        print(f"   URL: {url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print(f"   ✓ Login successful")
            print(f"   Token: {token[:30]}..." if token else "   ✗ No token received")
            return token
        else:
            print(f"   ✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"   ✗ Login error: {e}")
        return None


def test_relay_control(token, relay_num=1):
    """Test relay control"""
    print(f"\n3️⃣  Testing relay {relay_num} control...")
    try:
        # Remove trailing slash if present
        base = BASE_URL.rstrip('/')
        url = f"{base}/relay"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "relay": relay_num,
            "action": "open_hold"
        }
        
        print(f"   URL: {url}")
        print(f"   Headers: {json.dumps({k: v[:30] + '...' if len(v) > 30 else v for k, v in headers.items()}, indent=2)}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print(f"   ✓ Relay control successful!")
            return True
        else:
            print(f"   ✗ Relay control failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Relay control error: {e}")
        return False


def test_all_endpoints():
    """Check all available endpoints"""
    print("\n4️⃣  Checking available endpoints...")
    
    endpoints_to_test = [
        ("GET", "/status"),
        ("POST", "/login"),
        ("POST", "/relay"),
        ("GET", "/health_check"),
    ]
    
    for method, path in endpoints_to_test:
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            print(f"   {method:4} {path:20} - Status: {response.status_code}")
        except Exception as e:
            print(f"   {method:4} {path:20} - Error: {str(e)[:30]}")


# ============================================
# Main Test
# ============================================

def main():
    print("="*60)
    print("RELAY CONTROL DIAGNOSTIC TEST")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Username: {USERNAME}")
    print(f"  API Key: {API_KEY[:20]}..." if len(API_KEY) > 20 else f"  API Key: {API_KEY}")
    
    # Test 1: Connection
    if not test_connection():
        print("\n❌ Cannot reach server. Check your PI_IP and PORT.")
        return
    
    # Test 2: Login
    token = test_login()
    if not token:
        print("\n❌ Login failed. Check your USERNAME and PASSWORD.")
        return
    
    # Test 3: Relay Control
    if not test_relay_control(token, relay_num=1):
        print("\n❌ Relay control failed. Check your API_KEY.")
        print("\nTroubleshooting:")
        print("  1. Verify API_KEY matches the one in .env or default")
        print("  2. Check that relay endpoint exists: POST /relay")
        print("  3. Try accessing dashboard to verify service is running")
        return
    
    # Test 4: List endpoints
    test_all_endpoints()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYou can now use relay_control.py safely.")


if __name__ == "__main__":
    main()










