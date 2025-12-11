# API Endpoints Authentication Summary

## Overview
All endpoints now support **both Token-based** and **Basic HTTP Authentication**. API key authentication has been removed.

## Authentication Methods

### 1. Token-Based Authentication
- **Header**: `Authorization: Bearer <token>`
- **How to get token**: POST to `/login` with username/password
- **Token expires**: 24 hours (configurable via `SESSION_TTL_HOURS`)

### 2. Basic HTTP Authentication
- **Header**: `Authorization: Basic <base64(username:password)>`
- **URL format**: `http://username:password@host/path`
- **Can be disabled**: Via configuration setting `basic_auth_enabled`

---

## Endpoint List

### Public Endpoints (No Authentication Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Redirects to login page |
| `/setup` | GET | Setup page (API key configuration - deprecated) |
| `/login` | GET | Login page |
| `/login` | POST | Authenticate and get token |
| `/status` | GET | System status (public) |
| `/health_check` | GET | Health check endpoint |
| `/dashboard` | GET | Dashboard page (renders HTML) |

### Protected Endpoints (Require Authentication)

#### Read-Only Endpoints (`@require_auth`)
These endpoints accept **Token OR Basic Auth**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/logout` | POST | Logout and invalidate token |
| `/get_users` | GET | Get all users |
| `/get_transactions` | GET | Get transaction history |
| `/get_today_stats` | GET | Get today's statistics |
| `/get_analytics` | GET | Get analytics data |
| `/get_user_report` | GET | Get user-specific report |
| `/get_config` | GET | Get system configuration |
| `/get_system_time` | GET | Get system time |
| `/download_transactions_csv` | GET | Download transactions as CSV |

#### Write Endpoints (`@require_both`)
These endpoints accept **Token OR Basic Auth** (API key no longer required):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/add_user` | POST | Add new user |
| `/delete_user` | POST | Delete user |
| `/block_user` | POST | Block user access |
| `/unblock_user` | POST | Unblock user access |
| `/toggle_privacy` | POST | Toggle privacy protection |
| `/relay` | POST | Control relay (door lock) |
| `/update_config` | POST | Update system configuration |
| `/update_security` | POST | Update password/API key |
| `/set_system_time` | POST | Set system time |
| `/enable_ntp` | POST | Enable/disable NTP sync |

---

## Authentication Decorators

### `@require_auth`
- **Purpose**: Read-only operations
- **Accepts**: Token OR Basic Auth
- **Returns**: 401 if not authenticated

### `@require_both`
- **Purpose**: Write operations (mutating routes)
- **Accepts**: Token OR Basic Auth
- **Note**: Despite the name, API key is NO LONGER required
- **Returns**: 401 if not authenticated

---

## Usage Examples

### Using Token Authentication

```bash
# 1. Login to get token
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response: {"status":"success","token":"..."}

# 2. Use token in subsequent requests
curl http://localhost:5001/get_users \
  -H "Authorization: Bearer <token>"
```

### Using Basic Auth

```bash
# Method 1: Using curl -u flag
curl -u admin:admin123 http://localhost:5001/get_users

# Method 2: Using Authorization header
curl http://localhost:5001/get_users \
  -H "Authorization: Basic $(echo -n 'admin:admin123' | base64)"

# Method 3: Using URL format
curl http://admin:admin123@localhost:5001/get_users
```

### Python Example

```python
from api_accesss import AccessControlAPI

# Token-based
api = AccessControlAPI("http://localhost:5001")
api.login("admin", "admin123")
users = api.get_users()

# Basic Auth (no login needed)
api = AccessControlAPI(
    "http://localhost:5001",
    use_basic_auth=True,
    username="admin",
    password="admin123"
)
users = api.get_users()
```

---

## Frontend Usage

The frontend automatically uses token-based authentication:

```javascript
// Headers sent automatically
{
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('authToken')}`
}
```

---

## Error Responses

All authentication errors return:
```json
{
  "status": "error",
  "message": "Authentication required. Please login again."
}
```

With HTTP status code: **401 Unauthorized**

---

## Configuration

### Enable/Disable Basic Auth
- **Setting**: `basic_auth_enabled` in config.json
- **Default**: `true` (enabled)
- **Change via**: Configuration page → API Authentication Settings

When disabled:
- Basic Auth requests are rejected
- Token-based auth still works
- Only Bearer tokens accepted

---

## Security Notes

1. **Token Expiration**: Tokens expire after 24 hours (configurable)
2. **Basic Auth**: Can be disabled via configuration
3. **HTTPS Recommended**: Always use HTTPS in production
4. **Password Storage**: Passwords are hashed using SHA-256
5. **Session Management**: Tokens stored in memory, cleared on server restart

---

## Migration Notes

### Removed Features
- ❌ API key authentication (`X-API-Key` header)
- ❌ API key requirement for mutating operations

### Still Supported
- ✅ Token-based authentication
- ✅ Basic HTTP authentication
- ✅ Session management
- ✅ Token expiration

---

## Testing

### Test Token Auth
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Use token
curl http://localhost:5001/get_users \
  -H "Authorization: Bearer $TOKEN"
```

### Test Basic Auth
```bash
curl -u admin:admin123 http://localhost:5001/get_users
```

### Test Both Methods
```bash
# Both should work
curl -u admin:admin123 http://localhost:5001/get_users
curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/get_users
```

---

## Summary

✅ **All endpoints support both authentication methods**
✅ **API key authentication removed**
✅ **Token-based auth works everywhere**
✅ **Basic Auth works everywhere (when enabled)**
✅ **Frontend uses token-based auth automatically**
✅ **Backend validates both methods correctly**

