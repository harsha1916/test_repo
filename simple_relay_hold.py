#!/usr/bin/env python3
"""
Simple Relay Hold Script
Quick script to hold a relay open or closed
"""

import requests

# Configuration
PI_IP = "192.168.1.100"          # Change to your Pi's IP
PASSWORD = "admin123"             # Change to your password
API_KEY = "your-api-key-change-this"  # Change to your API key
BASE_URL = f"http://{PI_IP}:5001"

def hold_relay_open(relay_num):
    """Hold relay open indefinitely"""
    # Login
    response = requests.post(f"{BASE_URL}/login", json={
        "username": "admin",
        "password": PASSWORD
    })
    token = response.json()["token"]
    
    # Hold relay open
    response = requests.post(f"{BASE_URL}/relay", 
        headers={
            "Authorization": f"Bearer {token}",
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "relay": relay_num,
            "action": "open_hold"
        }
    )
    
    print(f"✓ Relay {relay_num} is now OPEN and HELD")
    print(f"Response: {response.json()}")

def pulse_relay_to_normalize(relay_num):
    """Pulse relay to return to normal operation"""
    # Login
    response = requests.post(f"{BASE_URL}/login", json={
        "username": "admin",
        "password": PASSWORD
    })
    token = response.json()["token"]
    
    # Pulse relay (normalizes it)
    response = requests.post(f"{BASE_URL}/relay", 
        headers={
            "Authorization": f"Bearer {token}",
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "relay": relay_num,
            "action": "normal"
        }
    )
    
    print(f"✓ Relay {relay_num} pulsed and normalized")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    # Hold relay 1 open
    hold_relay_open(1)
    
    # To normalize it later, uncomment this:
    # import time
    # time.sleep(30)  # Wait 30 seconds
    # pulse_relay_to_normalize(1)










