# API Examples Using Basic HTTP Authentication

## Overview
This guide shows how to use all API endpoints with Basic HTTP Authentication. No token login required!

---

## Authentication Methods

### Method 1: Using curl with `-u` flag (Easiest)
```bash
curl -u username:password http://host:port/endpoint
```

### Method 2: Using Authorization Header
```bash
curl -H "Authorization: Basic $(echo -n 'username:password' | base64)" http://host:port/endpoint
```

### Method 3: Using URL format
```bash
curl http://username:password@host:port/endpoint
```

### Method 4: Using Python requests
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'http://host:port/endpoint',
    auth=HTTPBasicAuth('username', 'password')
)
```

---

## Base URL
Replace `http://localhost:5001` with your server address.

Default credentials:
- **Username**: `admin`
- **Password**: `admin123` (or your configured password)

---

## API Endpoints Examples

### 1. Login (Get Token - Optional)
```bash
# Get token (not required if using Basic Auth)
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Response:**
```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 2. Logout
```bash
curl -X POST http://admin:admin123@localhost:5001/logout
```

**Response:**
```json
{
  "status": "success"
}
```

---

### 3. Get System Status
```bash
# Public endpoint - no auth needed
curl http://localhost:5001/status
```

**Response:**
```json
{
  "system": "online",
  "timestamp": "2024-01-15T10:30:00",
  "components": {
    "firebase": true,
    "pigpio": true,
    "rfid_readers": true,
    "internet": true
  },
  "storage": {
    "tx_dir_gb": 2.5,
    "cap_gb": 16,
    "cleanup_fraction": 0.5
  },
  "temperature": {
    "cpu_celsius": 45.2
  }
}
```

---

### 4. Get All Users
```bash
curl -u admin:admin123 http://localhost:5001/get_users
```

**Response:**
```json
[
  {
    "card_number": "12345678",
    "id": "USR001",
    "name": "John Doe",
    "ref_id": "EMP123",
    "blocked": false,
    "privacy_protected": false
  },
  {
    "card_number": "87654321",
    "id": "USR002",
    "name": "Jane Smith",
    "ref_id": "",
    "blocked": false,
    "privacy_protected": false
  }
]
```

---

### 5. Add User
```bash
curl -X POST http://admin:admin123@localhost:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "12345678",
    "id": "USR001",
    "name": "John Doe",
    "ref_id": "EMP123"
  }'
```

**Response:**
```json
{
  "status": "success"
}
```

---

### 6. Delete User
```bash
curl -X POST http://admin:admin123@localhost:5001/delete_user \
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

### 7. Block User
```bash
curl -X POST http://admin:admin123@localhost:5001/block_user \
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

### 8. Unblock User
```bash
curl -X POST http://admin:admin123@localhost:5001/unblock_user \
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

### 9. Toggle Privacy Protection
```bash
curl -X POST http://admin:admin123@localhost:5001/toggle_privacy \
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

### 10. Get Transactions
```bash
# Get last 50 transactions
curl -u admin:admin123 "http://localhost:5001/get_transactions?limit=50"

# Get last 200 transactions
curl -u admin:admin123 "http://localhost:5001/get_transactions?limit=200"
```

**Response:**
```json
[
  {
    "timestamp": 1705312200,
    "name": "John Doe",
    "card": "12345678",
    "reader": 1,
    "status": "Access Granted"
  },
  {
    "timestamp": 1705312100,
    "name": "Jane Smith",
    "card": "87654321",
    "reader": 2,
    "status": "Access Denied"
  }
]
```

---

### 11. Get Today's Statistics
```bash
curl -u admin:admin123 http://localhost:5001/get_today_stats
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

### 12. Get Analytics
```bash
# Get analytics for last 7 days
curl -u admin:admin123 "http://localhost:5001/get_analytics?days=7"

# Get analytics for last 30 days
curl -u admin:admin123 "http://localhost:5001/get_analytics?days=30"
```

**Response:**
```json
{
  "status": "success",
  "analytics": {
    "period_days": 7,
    "total_transactions": 1050,
    "unique_users": 25,
    "status_breakdown": {
      "granted": 850,
      "denied": 150,
      "blocked": 50
    },
    "reader_breakdown": {
      "1": 400,
      "2": 350,
      "3": 300
    },
    "hourly_distribution": {
      "0": 10,
      "1": 5,
      ...
    },
    "peak_hour": 9,
    "peak_day": "2024-01-15",
    "busiest_reader": 1,
    "top_users": [
      {
        "name": "John Doe",
        "card": "12345678",
        "count": 45
      }
    ]
  }
}
```

---

### 13. Get User Report
```bash
curl -u admin:admin123 "http://localhost:5001/get_user_report?card=12345678&days=30"
```

**Response:**
```json
{
  "status": "success",
  "report": {
    "user": {
      "name": "John Doe",
      "card": "12345678",
      "id": "USR001",
      "blocked": false
    },
    "summary": {
      "total_accesses": 45,
      "granted": 40,
      "denied": 5,
      "avg_per_day": 1.5
    },
    "patterns": {
      "favorite_hour": 9,
      "most_used_reader": 1,
      "first_access": 1705000000,
      "last_access": 1705312200
    },
    "hourly_pattern": {
      "0": 0,
      "1": 0,
      ...
      "9": 15
    },
    "reader_usage": {
      "1": 30,
      "2": 10,
      "3": 5
    },
    "timeline": [...]
  }
}
```

---

### 14. Control Relay
```bash
# Pulse relay 1 (open for 1 second)
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{
    "relay": 1,
    "action": "pulse"
  }'

# Open and hold relay 2
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{
    "relay": 2,
    "action": "open"
  }'

# Close relay 3
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{
    "relay": 3,
    "action": "close"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "relay 1:pulse"
}
```

---

### 15. Get Configuration
```bash
curl -u admin:admin123 http://localhost:5001/get_config
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
    "entity_id": "default_entity",
    "basic_auth_enabled": true
  }
}
```

---

### 16. Update Configuration
```bash
curl -X POST http://admin:admin123@localhost:5001/update_config \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "wiegand_bits": {
        "reader_1": 26,
        "reader_2": 34,
        "reader_3": 26
      },
      "scan_delay_seconds": 90,
      "entry_exit_tracking": {
        "enabled": true,
        "min_gap_seconds": 300
      },
      "basic_auth_enabled": true
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

### 17. Update Security Settings (Password)
```bash
curl -X POST http://admin:admin123@localhost:5001/update_security \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "newSecurePassword123"
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

### 18. Get System Time
```bash
curl -u admin:admin123 http://localhost:5001/get_system_time
```

**Response:**
```json
{
  "status": "success",
  "system_time": "2024-01-15T10:30:00",
  "timestamp": 1705312200,
  "timezone": "UTC +0000",
  "formatted": "2024-01-15 10:30:00"
}
```

---

### 19. Set System Time
```bash
# Set time to current Unix timestamp
curl -X POST http://admin:admin123@localhost:5001/set_system_time \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": 1705312200
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "System time set to 2024-01-15 10:30:00",
  "new_time": "2024-01-15T10:30:00"
}
```

---

### 20. Enable/Disable NTP
```bash
# Enable NTP
curl -X POST http://admin:admin123@localhost:5001/enable_ntp \
  -H "Content-Type: application/json" \
  -d '{
    "enable": true
  }'

# Disable NTP
curl -X POST http://admin:admin123@localhost:5001/enable_ntp \
  -H "Content-Type: application/json" \
  -d '{
    "enable": false
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

### 21. Download Transactions CSV
```bash
curl -u admin:admin123 "http://localhost:5001/download_transactions_csv?limit=500" > transactions.csv
```

**Response:**
```json
{
  "status": "success",
  "csv": "Timestamp,Name,Card Number,Reader,Status\n2024-01-15 10:30:00,John Doe,12345678,1,Access Granted\n..."
}
```

---

### 22. Health Check
```bash
# Public endpoint - no auth needed
curl http://localhost:5001/health_check
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

## Python Examples

### Using requests library
```python
import requests
from requests.auth import HTTPBasicAuth

base_url = "http://localhost:5001"
username = "admin"
password = "admin123"

# Get users
response = requests.get(
    f"{base_url}/get_users",
    auth=HTTPBasicAuth(username, password)
)
users = response.json()
print(users)

# Add user
response = requests.post(
    f"{base_url}/add_user",
    auth=HTTPBasicAuth(username, password),
    json={
        "card_number": "12345678",
        "id": "USR001",
        "name": "John Doe",
        "ref_id": "EMP123"
    }
)
print(response.json())

# Get transactions
response = requests.get(
    f"{base_url}/get_transactions",
    auth=HTTPBasicAuth(username, password),
    params={"limit": 50}
)
transactions = response.json()
print(transactions)
```

### Using the API Client Class
```python
from api_accesss import AccessControlAPI

# Initialize with Basic Auth
api = AccessControlAPI(
    "http://localhost:5001",
    use_basic_auth=True,
    username="admin",
    password="admin123"
)

# No login needed!
users = api.get_users()
print(users)

# Add user
api.add_user("12345678", "USR001", "John Doe", "EMP123")

# Get transactions
transactions = api.get_transactions(limit=50)
print(transactions)
```

---

## JavaScript/Node.js Examples

### Using fetch API
```javascript
const username = 'admin';
const password = 'admin123';
const baseUrl = 'http://localhost:5001';

// Create Basic Auth header
const credentials = btoa(`${username}:${password}`);
const headers = {
  'Authorization': `Basic ${credentials}`,
  'Content-Type': 'application/json'
};

// Get users
fetch(`${baseUrl}/get_users`, { headers })
  .then(res => res.json())
  .then(users => console.log(users));

// Add user
fetch(`${baseUrl}/add_user`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    card_number: '12345678',
    id: 'USR001',
    name: 'John Doe',
    ref_id: 'EMP123'
  })
})
  .then(res => res.json())
  .then(result => console.log(result));
```

### Using axios
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:5001',
  auth: {
    username: 'admin',
    password: 'admin123'
  }
});

// Get users
api.get('/get_users')
  .then(response => console.log(response.data));

// Add user
api.post('/add_user', {
  card_number: '12345678',
  id: 'USR001',
  name: 'John Doe',
  ref_id: 'EMP123'
})
  .then(response => console.log(response.data));
```

---

## Error Handling

### Authentication Errors
If Basic Auth is disabled or credentials are wrong:
```json
{
  "status": "error",
  "message": "Authentication required"
}
```
HTTP Status: **401 Unauthorized**

### Validation Errors
```json
{
  "status": "error",
  "message": "card_number,id,name required"
}
```
HTTP Status: **400 Bad Request**

---

## Notes

1. **Basic Auth can be disabled** via configuration setting `basic_auth_enabled`
2. **When disabled**, only token-based authentication works
3. **Credentials** are sent in every request (not stateless like tokens)
4. **Use HTTPS** in production to protect credentials
5. **Password special characters** may need URL encoding in URLs

---

## Quick Reference

### Most Common Operations

```bash
# Get all users
curl -u admin:admin123 http://localhost:5001/get_users

# Add user
curl -X POST http://admin:admin123@localhost:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678","id":"USR001","name":"John Doe"}'

# Get transactions
curl -u admin:admin123 "http://localhost:5001/get_transactions?limit=50"

# Block user
curl -X POST http://admin:admin123@localhost:5001/block_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678"}'

# Control relay
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{"relay":1,"action":"pulse"}'
```

---

## Security Best Practices

1. ✅ Always use HTTPS in production
2. ✅ Use strong passwords
3. ✅ Don't hardcode credentials in scripts
4. ✅ Use environment variables for credentials
5. ✅ Rotate passwords regularly
6. ✅ Monitor authentication logs

---

## Troubleshooting

### Issue: 401 Unauthorized
- Check username and password are correct
- Verify Basic Auth is enabled in configuration
- Check if password contains special characters (may need encoding)

### Issue: Connection Refused
- Verify server is running
- Check port number (default: 5001)
- Check firewall settings

### Issue: Timeout
- Check network connectivity
- Verify server is accessible
- Check server logs for errors

