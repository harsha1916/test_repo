# Basic HTTP Auth - Quick Reference Card

## Authentication Format
```bash
# Method 1: curl -u (Recommended)
curl -u admin:admin123 http://localhost:5001/endpoint

# Method 2: URL format
curl http://admin:admin123@localhost:5001/endpoint

# Method 3: Header
curl -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)" http://localhost:5001/endpoint
```

---

## All Endpoints (Basic Auth)

### Users Management
```bash
# Get all users
curl -u admin:admin123 http://localhost:5001/get_users

# Add user
curl -X POST http://admin:admin123@localhost:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678","id":"USR001","name":"John Doe","ref_id":"EMP123"}'

# Delete user
curl -X POST http://admin:admin123@localhost:5001/delete_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678"}'

# Block user
curl -X POST http://admin:admin123@localhost:5001/block_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678"}'

# Unblock user
curl -X POST http://admin:admin123@localhost:5001/unblock_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678"}'

# Toggle privacy
curl -X POST http://admin:admin123@localhost:5001/toggle_privacy \
  -H "Content-Type: application/json" \
  -d '{"card_number":"12345678","password":"admin123","enable":true}'
```

### Transactions & Analytics
```bash
# Get transactions
curl -u admin:admin123 "http://localhost:5001/get_transactions?limit=50"

# Get today's stats
curl -u admin:admin123 http://localhost:5001/get_today_stats

# Get analytics
curl -u admin:admin123 "http://localhost:5001/get_analytics?days=7"

# Get user report
curl -u admin:admin123 "http://localhost:5001/get_user_report?card=12345678&days=30"

# Download CSV
curl -u admin:admin123 "http://localhost:5001/download_transactions_csv?limit=500"
```

### Configuration
```bash
# Get config
curl -u admin:admin123 http://localhost:5001/get_config

# Update config
curl -X POST http://admin:admin123@localhost:5001/update_config \
  -H "Content-Type: application/json" \
  -d '{"config":{"wiegand_bits":{"reader_1":26},"scan_delay_seconds":60}}'

# Update password
curl -X POST http://admin:admin123@localhost:5001/update_security \
  -H "Content-Type: application/json" \
  -d '{"new_password":"newPassword123"}'
```

### Relay Control
```bash
# Pulse relay 1
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{"relay":1,"action":"pulse"}'

# Open relay 2
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{"relay":2,"action":"open"}'

# Close relay 3
curl -X POST http://admin:admin123@localhost:5001/relay \
  -H "Content-Type: application/json" \
  -d '{"relay":3,"action":"close"}'
```

### Time Management
```bash
# Get system time
curl -u admin:admin123 http://localhost:5001/get_system_time

# Set system time
curl -X POST http://admin:admin123@localhost:5001/set_system_time \
  -H "Content-Type: application/json" \
  -d '{"timestamp":1705312200}'

# Enable NTP
curl -X POST http://admin:admin123@localhost:5001/enable_ntp \
  -H "Content-Type: application/json" \
  -d '{"enable":true}'
```

### System Info
```bash
# System status (no auth needed)
curl http://localhost:5001/status

# Health check (no auth needed)
curl http://localhost:5001/health_check

# Logout
curl -X POST http://admin:admin123@localhost:5001/logout
```

---

## Python Quick Examples

```python
import requests
from requests.auth import HTTPBasicAuth

base = "http://localhost:5001"
auth = HTTPBasicAuth('admin', 'admin123')

# Get users
users = requests.get(f"{base}/get_users", auth=auth).json()

# Add user
requests.post(f"{base}/add_user", auth=auth, json={
    "card_number": "12345678",
    "id": "USR001",
    "name": "John Doe"
})

# Get transactions
tx = requests.get(f"{base}/get_transactions", auth=auth, params={"limit": 50}).json()
```

---

## JavaScript Quick Examples

```javascript
const auth = 'Basic ' + btoa('admin:admin123');
const base = 'http://localhost:5001';

// Get users
fetch(`${base}/get_users`, {
  headers: { 'Authorization': auth }
}).then(r => r.json()).then(console.log);

// Add user
fetch(`${base}/add_user`, {
  method: 'POST',
  headers: {
    'Authorization': auth,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    card_number: '12345678',
    id: 'USR001',
    name: 'John Doe'
  })
}).then(r => r.json()).then(console.log);
```

---

## Notes
- Replace `localhost:5001` with your server address
- Replace `admin:admin123` with your credentials
- All endpoints support Basic Auth (when enabled)
- Use HTTPS in production!

