#!/usr/bin/env python3
"""
Relay Control Script
Control relays: Hold open, hold closed, or pulse
"""

import requests
import sys
import time

# ============================================
# CONFIGURATION - Update these values
# ============================================
PI_IP = "192.168.1.100"  # Change to your Pi's IP address
PORT = "5001"
USERNAME = "admin"
PASSWORD = "admin123"  # Change to your actual password
API_KEY = "your-api-key-change-this"  # Change to your actual API key

BASE_URL = f"http://{PI_IP}:{PORT}"

# ============================================
# Functions
# ============================================

def login(username, password):
    """Login and get authentication token"""
    try:
        url = f"{BASE_URL}/login"
        payload = {
            "username": username,
            "password": password
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print(f"✓ Logged in successfully")
            return token
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None


def control_relay(token, relay_num, action):
    """
    Control a relay
    
    Parameters:
        token: Authentication token
        relay_num: Relay number (1, 2, or 3)
        action: 'normal' (pulse 1s), 'open_hold', or 'close_hold'
    """
    try:
        # Ensure BASE_URL doesn't have trailing slash
        base = BASE_URL.rstrip('/')
        url = f"{base}/relay"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "relay": relay_num,
            "action": action
        }
        
        print(f"🔍 Debug - URL: {url}")
        print(f"🔍 Debug - Payload: {payload}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        print(f"🔍 Debug - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Relay {relay_num}: {action} - {data.get('message', 'Success')}")
            return True
        else:
            print(f"✗ Relay control failed (Status {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"✗ Relay control error: {e}")
        return False


def hold_relay_open(token, relay_num):
    """Hold relay open (LOW state)"""
    print(f"\n🔓 Opening and holding relay {relay_num}...")
    return control_relay(token, relay_num, "open_hold")


def hold_relay_closed(token, relay_num):
    """Hold relay closed (HIGH state)"""
    print(f"\n🔒 Closing and holding relay {relay_num}...")
    return control_relay(token, relay_num, "close_hold")


def pulse_relay(token, relay_num):
    """Pulse relay for 1 second (normal operation)"""
    print(f"\n⚡ Pulsing relay {relay_num} (1 second)...")
    return control_relay(token, relay_num, "normal")


# ============================================
# Main Script
# ============================================

def main():
    print("="*50)
    print("Relay Control Script")
    print("="*50)
    
    # Login
    print(f"\n🔐 Logging in to {BASE_URL}...")
    token = login(USERNAME, PASSWORD)
    
    if not token:
        print("\n✗ Failed to login. Check your credentials and IP address.")
        sys.exit(1)
    
    # Interactive menu
    while True:
        print("\n" + "="*50)
        print("RELAY CONTROL MENU")
        print("="*50)
        print("1. Hold Relay 1 OPEN")
        print("2. Hold Relay 2 OPEN")
        print("3. Hold Relay 3 OPEN")
        print("4. Hold Relay 1 CLOSED")
        print("5. Hold Relay 2 CLOSED")
        print("6. Hold Relay 3 CLOSED")
        print("7. Pulse Relay 1 (normalize)")
        print("8. Pulse Relay 2 (normalize)")
        print("9. Pulse Relay 3 (normalize)")
        print("0. Exit")
        print("="*50)
        
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == "1":
            hold_relay_open(token, 1)
        elif choice == "2":
            hold_relay_open(token, 2)
        elif choice == "3":
            hold_relay_open(token, 3)
        elif choice == "4":
            hold_relay_closed(token, 1)
        elif choice == "5":
            hold_relay_closed(token, 2)
        elif choice == "6":
            hold_relay_closed(token, 3)
        elif choice == "7":
            pulse_relay(token, 1)
        elif choice == "8":
            pulse_relay(token, 2)
        elif choice == "9":
            pulse_relay(token, 3)
        elif choice == "0":
            print("\n👋 Exiting...")
            break
        else:
            print("\n✗ Invalid choice. Please enter 0-9.")


# ============================================
# Command Line Usage Examples
# ============================================

def command_line_examples():
    """
    Quick command-line usage without interactive menu
    Call specific functions directly
    """
    # Login
    token = login(USERNAME, PASSWORD)
    if not token:
        print("Login failed!")
        return
    
    # Example 1: Hold relay 1 open
    hold_relay_open(token, 1)
    
    # Example 2: Wait 10 seconds
    print("\n⏳ Waiting 10 seconds...")
    time.sleep(10)
    
    # Example 3: Return relay to normal (pulse)
    pulse_relay(token, 1)
    
    # Example 4: Hold relay 2 open for 30 seconds, then normalize
    hold_relay_open(token, 2)
    print("\n⏳ Relay will stay open for 30 seconds...")
    time.sleep(30)
    pulse_relay(token, 2)


# ============================================
# Run Script
# ============================================

if __name__ == "__main__":
    # Check if running with command-line arguments
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "--example":
            # Run examples
            command_line_examples()
        elif sys.argv[1] == "--help":
            print("""
Relay Control Script Usage:
===========================

Interactive Mode:
    python relay_control.py

Examples Mode:
    python relay_control.py --example

Direct Control:
    python relay_control.py hold_open <relay_num>
    python relay_control.py hold_closed <relay_num>
    python relay_control.py pulse <relay_num>

Examples:
    python relay_control.py hold_open 1      # Hold relay 1 open
    python relay_control.py hold_closed 2    # Hold relay 2 closed
    python relay_control.py pulse 3          # Pulse relay 3

Note: Edit the script to update PI_IP, PASSWORD, and API_KEY
            """)
        elif len(sys.argv) == 3:
            # Direct control mode: python relay_control.py hold_open 1
            action = sys.argv[1]
            relay_num = int(sys.argv[2])
            
            token = login(USERNAME, PASSWORD)
            if token:
                if action == "hold_open":
                    hold_relay_open(token, relay_num)
                elif action == "hold_closed":
                    hold_relay_closed(token, relay_num)
                elif action == "pulse":
                    pulse_relay(token, relay_num)
                else:
                    print(f"Unknown action: {action}")
                    print("Use: hold_open, hold_closed, or pulse")
        else:
            print("Invalid arguments. Use --help for usage.")
    else:
        # Interactive menu mode
        main()

