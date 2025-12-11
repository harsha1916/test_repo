# 🚀 Access Control System - API Examples

## Base URL
```
http://YOUR_PI_IP:5001
```

Replace `YOUR_PI_IP` with your Raspberry Pi's IP address (e.g., `192.168.1.100`)

---

## Authentication Flow

### 1. Login (Get Auth Token)

**Endpoint:** `POST /login`

**Request:**
```bash
curl -X POST http://192.168.1.100:5001/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Save the token** - you'll need it for all authenticated requests!

---

## 🔐 Using Authentication

All authenticated endpoints require:
- **Header:** `Authorization: Bearer YOUR_TOKEN`
- **Header:** `X-API-Key: your-api-key-change-this`

**Example with curl:**
```bash
TOKEN="your_token_here"
API_KEY="your-api-key-change-this"

curl -X GET http://192.168.1.100:5001/get_users \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

---

## 📋 API Endpoints by Category

### System Status

#### Get System Status
```bash
# Public endpoint (no auth required)
curl http://192.168.1.100:5001/status
```

**Response:**
```json
{
  "system": "online",
  "timestamp": "2025-10-10T15:30:45.123456",
  "components": {
    "firebase": true,
    "pigpio": true,
    "rfid_readers": true,
    "internet": true
  },
  "storage": {
    "tx_dir_gb": 0.156,
    "cap_gb": 16.0,
    "cleanup_fraction": 0.5
  },
  "files": {
    "users": true,
    "blocked": true,
    "daily_stats": true
  },
  "temperature": {
    "cpu_celsius": 45.2
  }
}
```

---

#### Health Check
```bash
# Public endpoint
curl http://192.168.1.100:5001/health_check
```

**Response:**
```json
{
  "internet": true,
  "firebase": true,
  "pigpio": true
}
```

---

### 👥 User Management

#### Get All Users
```bash
curl -X GET http://192.168.1.100:5001/get_users \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
[
  {
    "card_number": "12345678",
    "id": "EMP001",
    "name": "John Doe",
    "ref_id": "REF123",
    "blocked": false,
    "privacy_protected": false
  },
  {
    "card_number": "87654321",
    "id": "EMP002",
    "name": "Jane Smith",
    "ref_id": "REF456",
    "blocked": true,
    "privacy_protected": false
  }
]
```

---

#### Add New User
```bash
curl -X POST http://192.168.1.100:5001/add_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "99887766",
    "id": "EMP003",
    "name": "Bob Wilson",
    "ref_id": "REF789"
  }'
```

**Response:**
```json
{
  "status": "success"
}
```

---

#### Delete User
```bash
curl -X POST http://192.168.1.100:5001/delete_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "99887766"
  }'
```

**Response:**
```json
{
  "status": "success"
}
```

---

#### Block User
```bash
curl -X POST http://192.168.1.100:5001/block_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "12345678"
  }'
```

**Response:**
```json
{
  "status": "success"
}
```

---

#### Unblock User
```bash
curl -X POST http://192.168.1.100:5001/unblock_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "12345678"
  }'
```

**Response:**
```json
{
  "status": "success"
}
```

---

#### Toggle Privacy Protection
```bash
curl -X POST http://192.168.1.100:5001/toggle_privacy \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "12345678",
    "password": "admin123",
    "enable": true
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Privacy protection enabled for John Doe"
}
```

---

### 📊 Transactions & Statistics

#### Get Transactions
```bash
# Get last 50 transactions (default)
curl -X GET "http://192.168.1.100:5001/get_transactions?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
[
  {
    "name": "John Doe",
    "card": "12345678",
    "reader": 1,
    "status": "Access Granted",
    "timestamp": 1728574245
  },
  {
    "name": "Jane Smith",
    "card": "87654321",
    "reader": 2,
    "status": "Access Denied",
    "timestamp": 1728574250
  }
]
```

**Get more transactions:**
```bash
# Get last 200 transactions
curl -X GET "http://192.168.1.100:5001/get_transactions?limit=200" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

---

#### Get Today's Statistics
```bash
curl -X GET http://192.168.1.100:5001/get_today_stats \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "total": 150,
  "granted": 120,
  "denied": 25,
  "blocked": 5
}
```

---

#### Download Transactions CSV
```bash
curl -X GET "http://192.168.1.100:5001/download_transactions_csv?limit=500" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "status": "success",
  "csv": "Timestamp,Name,Card Number,Reader,Status\n2025-10-10 15:30:45,John Doe,12345678,1,Access Granted\n..."
}
```

**Save to file:**
```bash
curl -X GET "http://192.168.1.100:5001/download_transactions_csv?limit=500" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  | jq -r '.csv' > transactions.csv
```

---

### 📈 Analytics

#### Get System Analytics
```bash
# Last 7 days analytics
curl -X GET "http://192.168.1.100:5001/get_analytics?days=7" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "status": "success",
  "analytics": {
    "period_days": 7,
    "total_transactions": 850,
    "status_breakdown": {
      "granted": 720,
      "denied": 100,
      "blocked": 30
    },
    "reader_breakdown": {
      "1": 400,
      "2": 350,
      "3": 100
    },
    "hourly_distribution": {
      "0": 5, "1": 2, "2": 0, "3": 0,
      "8": 120, "9": 150, "10": 100,
      "17": 140, "18": 100, "19": 50
    },
    "daily_distribution": {
      "2025-10-04": 100,
      "2025-10-05": 120,
      "2025-10-06": 110
    },
    "top_users": [
      {"name": "John Doe", "card": "12345678", "count": 45},
      {"name": "Jane Smith", "card": "87654321", "count": 38}
    ],
    "peak_hour": 9,
    "peak_day": "2025-10-05",
    "busiest_reader": 1,
    "unique_users": 25
  }
}
```

**Different periods:**
```bash
# Last 30 days
curl -X GET "http://192.168.1.100:5001/get_analytics?days=30" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"

# Last 90 days
curl -X GET "http://192.168.1.100:5001/get_analytics?days=90" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

---

#### Get User Report
```bash
# Get report for specific user
curl -X GET "http://192.168.1.100:5001/get_user_report?card=12345678&days=30" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "status": "success",
  "report": {
    "user": {
      "name": "John Doe",
      "card": "12345678",
      "id": "EMP001",
      "ref_id": "REF123",
      "blocked": false
    },
    "period_days": 30,
    "summary": {
      "total_accesses": 120,
      "granted": 118,
      "denied": 2,
      "blocked": 0,
      "avg_per_day": 4.0
    },
    "patterns": {
      "most_used_reader": 1,
      "favorite_hour": 9,
      "first_access": 1726574245,
      "last_access": 1728574245
    },
    "timeline": [
      {"timestamp": 1728574245, "reader": 1, "status": "Access Granted"},
      {"timestamp": 1728560000, "reader": 1, "status": "Access Granted"}
    ],
    "hourly_pattern": {
      "8": 15, "9": 35, "10": 20, "17": 30, "18": 20
    },
    "reader_usage": {
      "1": 90, "2": 25, "3": 5
    }
  }
}
```

---

### 🎛️ Relay Control

#### Pulse Relay (Normal Operation)
```bash
# Pulse relay 1 for 1 second
curl -X POST http://192.168.1.100:5001/relay \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "relay": 1,
    "action": "normal"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "relay 1:normal"
}
```

---

#### Open and Hold
```bash
# Open relay 2 and hold it open
curl -X POST http://192.168.1.100:5001/relay \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "relay": 2,
    "action": "open_hold"
  }'
```

---

#### Close and Hold
```bash
# Close relay 3 and hold it closed
curl -X POST http://192.168.1.100:5001/relay \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "relay": 3,
    "action": "close_hold"
  }'
```

**Relay Actions:**
- `normal` - Pulse for 1 second (default relay operation)
- `open_hold` - Open and hold indefinitely
- `close_hold` - Close and hold indefinitely

**Relays:**
- `1` - Relay 1 (Main entrance)
- `2` - Relay 2 (Secondary door)
- `3` - Relay 3 (Auxiliary)

---

### ⏰ Time Management

#### Get System Time
```bash
curl -X GET http://192.168.1.100:5001/get_system_time \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "status": "success",
  "system_time": "2025-10-10T15:30:45.123456",
  "timestamp": 1728574245,
  "timezone": "UTC +0000",
  "formatted": "2025-10-10 15:30:45"
}
```

---

#### Set System Time (Sync with PC)
```bash
# Set to current time (Unix timestamp)
CURRENT_TIME=$(date +%s)

curl -X POST http://192.168.1.100:5001/set_system_time \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"timestamp\": $CURRENT_TIME
  }"
```

**Response:**
```json
{
  "status": "success",
  "message": "System time set to 2025-10-10 15:30:45",
  "new_time": "2025-10-10T15:30:45"
}
```

---

#### Enable NTP Time Sync
```bash
curl -X POST http://192.168.1.100:5001/enable_ntp \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enable": true
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "NTP time synchronization enabled"
}
```

---

### ⚙️ Configuration

#### Get Configuration
```bash
curl -X GET http://192.168.1.100:5001/get_config \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "status": "success",
  "config": {
    "wiegand_bits": {
      "reader_1": 26,
      "reader_2": 26,
      "reader_3": 26
    },
    "wiegand_timeout_ms": 25,
    "scan_delay_seconds": 60,
    "entry_exit_tracking": {
      "enabled": false,
      "min_gap_seconds": 300
    },
    "entity_id": "default_entity"
  }
}
```

---

#### Update Configuration
```bash
curl -X POST http://192.168.1.100:5001/update_config \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "wiegand_bits": {
        "reader_1": 26,
        "reader_2": 34,
        "reader_3": 26
      },
      "wiegand_timeout_ms": 25,
      "scan_delay_seconds": 60,
      "entry_exit_tracking": {
        "enabled": true,
        "min_gap_seconds": 300
      },
      "entity_id": "building_a"
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated and readers reinitialized"
}
```

---

#### Update Security Settings
```bash
# Change admin password and/or API key
curl -X POST http://192.168.1.100:5001/update_security \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "NewSecurePassword123!",
    "new_api_key": "new-super-secret-api-key-xyz"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Security settings updated. Please update your saved credentials!"
}
```

---

### 🚪 Logout

```bash
curl -X POST http://192.168.1.100:5001/logout \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY"
```

**Response:**
```json
{
  "status": "success"
}
```

---

## 🐍 Python Examples

### Setup
```python
import requests
import json
from datetime import datetime

BASE_URL = "http://192.168.1.100:5001"
API_KEY = "your-api-key-change-this"
```

### Login and Get Token
```python
def login(username, password):
    url = f"{BASE_URL}/login"
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    else:
        print(f"Login failed: {response.text}")
        return None

# Get auth token
token = login("admin", "admin123")
print(f"Token: {token}")
```

### Get All Users
```python
def get_users(token):
    url = f"{BASE_URL}/get_users"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

# Usage
users = get_users(token)
for user in users:
    print(f"Name: {user['name']}, Card: {user['card_number']}, Blocked: {user['blocked']}")
```

### Add New User
```python
def add_user(token, card_number, user_id, name, ref_id=""):
    url = f"{BASE_URL}/add_user"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "card_number": card_number,
        "id": user_id,
        "name": name,
        "ref_id": ref_id
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Usage
result = add_user(token, "99887766", "EMP003", "Bob Wilson", "REF789")
print(result)
```

### Get Transactions
```python
def get_transactions(token, limit=50):
    url = f"{BASE_URL}/get_transactions"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": API_KEY
    }
    params = {"limit": limit}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Usage
transactions = get_transactions(token, limit=100)
for tx in transactions[:10]:  # Show first 10
    timestamp = datetime.fromtimestamp(tx['timestamp'])
    print(f"{timestamp} - {tx['name']} ({tx['card']}) - {tx['status']}")
```

### Control Relay
```python
def control_relay(token, relay_num, action):
    """
    relay_num: 1, 2, or 3
    action: 'normal', 'open_hold', 'close_hold'
    """
    url = f"{BASE_URL}/relay"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "relay": relay_num,
        "action": action
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Usage
# Pulse relay 1
result = control_relay(token, 1, "normal")
print(result)

# Open and hold relay 2
result = control_relay(token, 2, "open_hold")
print(result)
```

### Get Analytics
```python
def get_analytics(token, days=7):
    url = f"{BASE_URL}/get_analytics"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": API_KEY
    }
    params = {"days": days}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Usage
analytics = get_analytics(token, days=30)
if analytics and analytics['status'] == 'success':
    data = analytics['analytics']
    print(f"Total Transactions: {data['total_transactions']}")
    print(f"Success Rate: {(data['status_breakdown']['granted'] / data['total_transactions'] * 100):.1f}%")
    print(f"Peak Hour: {data['peak_hour']}:00")
    print(f"Busiest Reader: {data['busiest_reader']}")
```

### Sync Time with PC
```python
import time

def sync_time_with_pc(token):
    url = f"{BASE_URL}/set_system_time"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    current_time = int(time.time())
    payload = {"timestamp": current_time}
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# Usage
result = sync_time_with_pc(token)
print(result)
```

---

## 📱 JavaScript (Browser) Examples

### Setup
```javascript
const BASE_URL = 'http://192.168.1.100:5001';
const API_KEY = 'your-api-key-change-this';
let authToken = localStorage.getItem('authToken');
```

### Login
```javascript
async function login(username, password) {
    const response = await fetch(`${BASE_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        authToken = data.token;
        localStorage.setItem('authToken', authToken);
        return authToken;
    }
    throw new Error('Login failed');
}

// Usage
login('admin', 'admin123')
    .then(token => console.log('Logged in:', token))
    .catch(err => console.error(err));
```

### Get Users
```javascript
async function getUsers() {
    const response = await fetch(`${BASE_URL}/get_users`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'X-API-Key': API_KEY
        }
    });
    
    if (response.ok) {
        return await response.json();
    }
    throw new Error('Failed to get users');
}

// Usage
getUsers()
    .then(users => {
        users.forEach(user => {
            console.log(`${user.name} - ${user.card_number} - Blocked: ${user.blocked}`);
        });
    })
    .catch(err => console.error(err));
```

### Add User
```javascript
async function addUser(cardNumber, userId, name, refId = '') {
    const response = await fetch(`${BASE_URL}/add_user`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            card_number: cardNumber,
            id: userId,
            name: name,
            ref_id: refId
        })
    });
    
    return await response.json();
}

// Usage
addUser('99887766', 'EMP003', 'Bob Wilson', 'REF789')
    .then(result => console.log('User added:', result))
    .catch(err => console.error(err));
```

### Get Transactions
```javascript
async function getTransactions(limit = 50) {
    const response = await fetch(`${BASE_URL}/get_transactions?limit=${limit}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'X-API-Key': API_KEY
        }
    });
    
    if (response.ok) {
        return await response.json();
    }
    throw new Error('Failed to get transactions');
}

// Usage
getTransactions(100)
    .then(transactions => {
        transactions.forEach(tx => {
            const date = new Date(tx.timestamp * 1000);
            console.log(`${date.toLocaleString()} - ${tx.name} - ${tx.status}`);
        });
    })
    .catch(err => console.error(err));
```

### Control Relay
```javascript
async function controlRelay(relayNum, action) {
    const response = await fetch(`${BASE_URL}/relay`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            relay: relayNum,
            action: action
        })
    });
    
    return await response.json();
}

// Usage
controlRelay(1, 'normal')
    .then(result => console.log('Relay controlled:', result))
    .catch(err => console.error(err));
```

### Get System Status
```javascript
async function getSystemStatus() {
    const response = await fetch(`${BASE_URL}/status`);
    if (response.ok) {
        return await response.json();
    }
    throw new Error('Failed to get status');
}

// Usage
getSystemStatus()
    .then(status => {
        console.log('System:', status.system);
        console.log('Temperature:', status.temperature.cpu_celsius + '°C');
        console.log('Internet:', status.components.internet);
        console.log('Storage:', status.storage.tx_dir_gb + ' GB');
    })
    .catch(err => console.error(err));
```

---

## 🔧 Complete Python Script Example

```python
#!/usr/bin/env python3
"""
Access Control API Client Example
Complete script showing all major operations
"""

import requests
import json
import time
from datetime import datetime

class AccessControlClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.token = None
    
    def _headers(self):
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, username, password):
        """Login and get auth token"""
        url = f"{self.base_url}/login"
        payload = {"username": username, "password": password}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            return True
        return False
    
    def get_users(self):
        """Get all users"""
        url = f"{self.base_url}/get_users"
        response = requests.get(url, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        return []
    
    def add_user(self, card_number, user_id, name, ref_id=""):
        """Add new user"""
        url = f"{self.base_url}/add_user"
        payload = {
            "card_number": card_number,
            "id": user_id,
            "name": name,
            "ref_id": ref_id
        }
        response = requests.post(url, headers=self._headers(), json=payload)
        return response.json()
    
    def block_user(self, card_number):
        """Block a user"""
        url = f"{self.base_url}/block_user"
        payload = {"card_number": card_number}
        response = requests.post(url, headers=self._headers(), json=payload)
        return response.json()
    
    def get_transactions(self, limit=50):
        """Get recent transactions"""
        url = f"{self.base_url}/get_transactions"
        params = {"limit": limit}
        response = requests.get(url, headers=self._headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_today_stats(self):
        """Get today's statistics"""
        url = f"{self.base_url}/get_today_stats"
        response = requests.get(url, headers=self._headers())
        if response.status_code == 200:
            return response.json()
        return {}
    
    def control_relay(self, relay_num, action):
        """Control relay (1-3, action: normal/open_hold/close_hold)"""
        url = f"{self.base_url}/relay"
        payload = {"relay": relay_num, "action": action}
        response = requests.post(url, headers=self._headers(), json=payload)
        return response.json()
    
    def get_system_status(self):
        """Get system status (no auth required)"""
        url = f"{self.base_url}/status"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return {}

# Usage example
if __name__ == "__main__":
    # Initialize client
    client = AccessControlClient(
        base_url="http://192.168.1.100:5001",
        api_key="your-api-key-change-this"
    )
    
    # Login
    if client.login("admin", "admin123"):
        print("✓ Logged in successfully")
        
        # Get system status
        status = client.get_system_status()
        print(f"\n📊 System Status:")
        print(f"  Temperature: {status['temperature']['cpu_celsius']}°C")
        print(f"  Internet: {status['components']['internet']}")
        print(f"  Storage: {status['storage']['tx_dir_gb']} GB")
        
        # Get today's stats
        stats = client.get_today_stats()
        print(f"\n📈 Today's Stats:")
        print(f"  Total: {stats['total']}")
        print(f"  Granted: {stats['granted']}")
        print(f"  Denied: {stats['denied']}")
        print(f"  Blocked: {stats['blocked']}")
        
        # Get users
        users = client.get_users()
        print(f"\n👥 Users ({len(users)}):")
        for user in users[:5]:  # Show first 5
            status_icon = "🚫" if user['blocked'] else "✅"
            print(f"  {status_icon} {user['name']} - Card: {user['card_number']}")
        
        # Get recent transactions
        transactions = client.get_transactions(limit=10)
        print(f"\n📋 Recent Transactions:")
        for tx in transactions[:5]:  # Show first 5
            timestamp = datetime.fromtimestamp(tx['timestamp'])
            status_icon = "✅" if tx['status'] == "Access Granted" else "❌"
            print(f"  {status_icon} {timestamp.strftime('%H:%M:%S')} - {tx['name']} - {tx['status']}")
        
    else:
        print("✗ Login failed")
```

---

## 🎯 Common Use Cases

### 1. Monitor System (Every 30 seconds)
```python
while True:
    status = client.get_system_status()
    temp = status['temperature']['cpu_celsius']
    print(f"Temperature: {temp}°C at {datetime.now()}")
    
    if temp > 70:
        print("⚠️  WARNING: High temperature!")
    
    time.sleep(30)
```

### 2. Export Today's Transactions
```bash
# Get CSV and save to file
curl -X GET "http://192.168.1.100:5001/download_transactions_csv?limit=1000" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  | jq -r '.csv' > "transactions_$(date +%Y%m%d).csv"
```

### 3. Automated Relay Schedule
```python
import schedule

def open_door():
    client.control_relay(1, "open_hold")
    print("Door opened at", datetime.now())

def close_door():
    client.control_relay(1, "close_hold")
    print("Door closed at", datetime.now())

# Open at 8 AM, close at 6 PM
schedule.every().day.at("08:00").do(open_door)
schedule.every().day.at("18:00").do(close_door)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 4. Alert on Blocked User Attempts
```python
def monitor_blocked_attempts():
    last_check = time.time()
    
    while True:
        time.sleep(10)  # Check every 10 seconds
        transactions = client.get_transactions(limit=100)
        
        for tx in transactions:
            if tx['timestamp'] > last_check and tx['status'] == 'Blocked':
                print(f"🚨 ALERT: Blocked user attempted access!")
                print(f"   Card: {tx['card']} at {datetime.fromtimestamp(tx['timestamp'])}")
                # Send email, SMS, or webhook here
        
        last_check = time.time()
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
```bash
# Store credentials securely
export ACCESS_CONTROL_HOST="192.168.1.100:5001"
export ACCESS_CONTROL_API_KEY="your-api-key-here"
export ACCESS_CONTROL_PASSWORD="your-password-here"
```

```python
import os

BASE_URL = f"http://{os.environ['ACCESS_CONTROL_HOST']}"
API_KEY = os.environ['ACCESS_CONTROL_API_KEY']
PASSWORD = os.environ['ACCESS_CONTROL_PASSWORD']
```

### 2. Token Refresh
```python
def ensure_authenticated(client):
    """Check if token is still valid, re-login if needed"""
    try:
        # Try to get users (authenticated endpoint)
        client.get_users()
        return True
    except:
        # Token expired or invalid, re-login
        return client.login("admin", PASSWORD)
```

### 3. Error Handling
```python
def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with error handling"""
    try:
        return func(*args, **kwargs)
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the service running?")
    except requests.exceptions.Timeout:
        print("❌ Request timeout - slow network?")
    except Exception as e:
        print(f"❌ Error: {e}")
    return None
```

---

## 📚 Additional Resources

- **Dashboard URL**: `http://192.168.1.100:5001/dashboard`
- **Login Page**: `http://192.168.1.100:5001/login`
- **Setup Page**: `http://192.168.1.100:5001/setup`

---

## ⚡ Quick Test

Test if API is working:
```bash
# Simple health check (no auth)
curl http://192.168.1.100:5001/health_check

# Should return:
# {"internet":true,"firebase":true,"pigpio":true}
```

---

**Happy Coding! 🚀**

Need more examples? Check the dashboard's network tab in browser DevTools to see live API calls!










