# HTTP Basic Authentication Usage

## Overview
The API now supports **HTTP Basic Authentication** in addition to the existing token-based authentication. This allows you to use credentials directly in the URL or headers without needing to get a login token first.

## Authentication Methods

### Method 1: Basic Auth (Username:Password in URL)
```bash
# Using curl
curl http://admin:admin123@192.168.1.2:5001/get_users

# Using Python requests
import requests
response = requests.get('http://admin:admin123@192.168.1.2:5001/get_users')

# Using wget
wget --user=admin --password=admin123 http://192.168.1.2:5001/get_users
```

### Method 2: Basic Auth (Authorization Header)
```bash
# Using curl with base64 encoded credentials
curl -u admin:admin123 http://192.168.1.2:5001/get_users

# Or manually set the header
curl -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)" \
     http://192.168.1.2:5001/get_users
```

### Method 3: Token Authentication (Original - Still Works)
```bash
# Step 1: Login to get token
TOKEN=$(curl -X POST http://192.168.1.2:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

# Step 2: Use token in requests
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-API-Key: your-api-key-change-this" \
     http://192.168.1.2:5001/get_users
```

## API Endpoint Authentication Requirements

### Endpoints Requiring Basic Auth OR Token (Read Operations)
These endpoints accept either Basic Auth or Token authentication:

- `GET /get_users` - Get all users
- `GET /get_transactions` - Get transactions
- `GET /get_today_stats` - Get today's statistics
- `GET /get_analytics` - Get analytics
- `GET /get_user_report` - Get user report
- `GET /get_system_time` - Get system time
- `GET /get_config` - Get configuration
- `GET /download_transactions_csv` - Download CSV

**Example:**
```bash
# Using Basic Auth (no token needed!)
curl http://admin:admin123@192.168.1.2:5001/get_users
```

### Endpoints Requiring Basic Auth OR (Token + API Key) (Write Operations)
These endpoints accept either:
- Basic Auth alone (username:password), OR
- Token + API Key combination (for UI compatibility)

- `POST /add_user` - Add new user
- `POST /delete_user` - Delete user
- `POST /block_user` - Block user
- `POST /unblock_user` - Unblock user
- `POST /toggle_privacy` - Toggle privacy protection
- `POST /relay` - Control relays
- `POST /set_system_time` - Set system time
- `POST /enable_ntp` - Enable/disable NTP
- `POST /update_config` - Update configuration
- `POST /update_security` - Update security settings

**Example with Basic Auth:**
```bash
# Using Basic Auth - simple and easy!
curl -X POST http://admin:admin123@192.168.1.2:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "123456",
    "id": "user1",
    "name": "John Doe"
  }'
```

**Example with Token + API Key (for UI):**
```bash
# Still works for UI compatibility
curl -X POST http://192.168.1.2:5001/add_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: your-api-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"card_number": "123456", "id": "user1", "name": "John Doe"}'
```

## Complete Examples

### Example 1: Get Users with Basic Auth
```bash
curl http://admin:admin123@192.168.1.2:5001/get_users
```

### Example 2: Add User with Basic Auth
```bash
curl -X POST http://admin:admin123@192.168.1.2:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "789012",
    "id": "user2",
    "name": "Jane Smith",
    "ref_id": "ref123"
  }'
```

### Example 3: Get Transactions with Basic Auth
```bash
curl "http://admin:admin123@192.168.1.2:5001/get_transactions?limit=100"
```

### Example 4: Block User with Basic Auth
```bash
curl -X POST http://admin:admin123@192.168.1.2:5001/block_user \
  -H "Content-Type: application/json" \
  -d '{"card_number": "123456"}'
```

### Example 5: Control Relay with Basic Auth
```bash
curl -X POST http://admin:admin123@192.168.1.2:5001/relay \
  -H "Content-Type: application/json" \
  -d '{
    "action": "normal",
    "relay": 1
  }'
```

## Python Examples

### Using requests library
```python
import requests
from requests.auth import HTTPBasicAuth

# Basic Auth method 1: URL
response = requests.get('http://admin:admin123@192.168.1.2:5001/get_users')

# Basic Auth method 2: auth parameter (recommended)
response = requests.get(
    'http://192.168.1.2:5001/get_users',
    auth=HTTPBasicAuth('admin', 'admin123')
)

# POST request with Basic Auth
response = requests.post(
    'http://192.168.1.2:5001/add_user',
    auth=HTTPBasicAuth('admin', 'admin123'),
    json={
        'card_number': '123456',
        'id': 'user1',
        'name': 'John Doe'
    }
)
```

## JavaScript/Node.js Examples

### Using fetch API
```javascript
// Basic Auth with fetch
const username = 'admin';
const password = 'admin123';
const credentials = btoa(`${username}:${password}`);

fetch('http://192.168.1.2:5001/get_users', {
    headers: {
        'Authorization': `Basic ${credentials}`
    }
})
.then(response => response.json())
.then(data => console.log(data));

// POST request
fetch('http://192.168.1.2:5001/add_user', {
    method: 'POST',
    headers: {
        'Authorization': `Basic ${credentials}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        card_number: '123456',
        id: 'user1',
        name: 'John Doe'
    })
});
```

## Security Notes

1. **HTTPS Recommended**: Basic Auth sends credentials in base64 encoding (not encryption). Use HTTPS in production!

2. **Credential Storage**: Never hardcode credentials in scripts. Use environment variables:
   ```bash
   export API_USER="admin"
   export API_PASS="admin123"
   curl -u "$API_USER:$API_PASS" http://192.168.1.2:5001/get_users
   ```

3. **Token Auth Still Available**: The web UI continues to use token-based authentication, which remains more secure for interactive sessions.

4. **Both Methods Work**: You can use either Basic Auth OR Token auth - choose based on your use case.

## Migration from Token Auth to Basic Auth

**Before (Token Auth):**
```bash
# Step 1: Login
TOKEN=$(curl -X POST http://192.168.1.2:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Step 2: Use token
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-API-Key: your-api-key-change-this" \
     http://192.168.1.2:5001/get_users
```

**After (Basic Auth):**
```bash
# One step - credentials in URL
curl http://admin:admin123@192.168.1.2:5001/get_users
```

## Troubleshooting

### 401 Unauthorized
- Check username and password are correct
- Verify credentials match `ADMIN_USERNAME` and password hash in `.env`
- For Basic Auth in URL, ensure format is correct: `http://username:password@host:port/path`

### Still Need Token Auth?
Token-based authentication still works! The UI continues to use it. Basic Auth is an additional option, not a replacement.

