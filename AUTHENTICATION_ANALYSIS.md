# Authentication System Analysis

## Overview
This access control system uses a **dual-layer authentication mechanism**:
1. **Session Token Authentication** - For web interface/user sessions
2. **API Key Authentication** - For REST API requests
3. **Combined Authentication** - Both token + API key required for sensitive operations

---

## 🔐 Authentication Methods

### 1. **Session Token Authentication** (Primary Method)

#### Token Generation
- **Function**: `generate_session_token()` (line 742-743)
- **Method**: Uses Python's `secrets.token_urlsafe(32)` 
- **Token Format**: URL-safe base64 encoded string (43 characters)
- **Security**: Cryptographically secure random token

```python
def generate_session_token():
    return secrets.token_urlsafe(32)
```

#### Login Process (Token Generation)
**Endpoint**: `POST /login` (lines 796-814)

**Flow**:
1. Client sends username and password via POST request
2. Server verifies credentials:
   - Username must match `ADMIN_USERNAME`
   - Password is hashed using SHA256 and compared with `ADMIN_PASSWORD_HASH`
3. If valid, server:
   - Generates a new session token using `generate_session_token()`
   - Stores token in `active_sessions` dictionary with:
     - `username`: The authenticated user
     - `login_time`: Timestamp of login
     - `expires`: Expiration time (default: 24 hours from login)
   - Returns token to client in JSON response

**Example Request**:
```json
POST /login
{
  "username": "admin",
  "password": "admin123"
}
```

**Example Response**:
```json
{
  "status": "success",
  "token": "xK9jP2mN8qR5vT3wY7zA1bC4dE6fG9hI0jK2lM4nO6pQ8rS0tU2vW4xY6zA8b"
}
```

#### Token Storage (Server-Side)
- **Location**: In-memory dictionary `active_sessions` (line 739)
- **Thread Safety**: Protected by `SESS_LOCK` (threading.RLock) (line 740)
- **Structure**:
```python
active_sessions = {
    "token_string": {
        "username": "admin",
        "login_time": datetime.now(),
        "expires": datetime.now() + timedelta(hours=24)
    }
}
```

#### Token Validation
**Function**: `is_authenticated()` (lines 752-755)

**Process**:
1. Extracts token from HTTP header: `Authorization: Bearer <token>`
2. Checks if token exists in `active_sessions` dictionary
3. Returns `True` if token is found, `False` otherwise

```python
def is_authenticated():
    token = request.headers.get('Authorization','').replace('Bearer ','')
    with SESS_LOCK:
        return token in active_sessions
```

**Note**: The current implementation does NOT check token expiration during validation. Expired tokens are cleaned up by a background worker.

#### Token Usage (Client-Side)

**Web Frontend (JavaScript)**:
- Token is stored in browser's `localStorage` with key `authToken`
- Token is automatically included in all API requests via `getHeaders()` function
- **Storage Location**: `localStorage.getItem('authToken')`
- **Header Injection**: Automatically added to every request as `Authorization: Bearer <token>`

**Frontend Implementation** (`static/js/main.js` and `templates/login.html`):
```javascript
// After successful login (login.html line 74)
localStorage.setItem('authToken', data.token);
localStorage.setItem('username', username);

// In all API calls (main.js lines 6-12)
function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
    };
}

// Automatic redirect on 401 (main.js lines 65-68)
if (response.status === 401) {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
    return null;
}
```

**REST API (curl/HTTP)**:
**Header Format**: `Authorization: Bearer <token>`

**Example**:
```bash
curl -X GET http://192.168.1.100:5001/get_users \
  -H "Authorization: Bearer xK9jP2mN8qR5vT3wY7zA1bC4dE6fG9hI0jK2lM4nO6pQ8rS0tU2vW4xY6zA8b"
```

#### Token Expiration & Cleanup
- **Default TTL**: 24 hours (configurable via `SESSION_TTL_HOURS` environment variable)
- **Cleanup Function**: `cleanup_expired_sessions()` (lines 745-750)
- **Worker**: `housekeeping_worker()` runs every 5 minutes (line 732)
- **Process**: Removes expired sessions from `active_sessions` dictionary

#### Logout
**Endpoint**: `POST /logout` (lines 816-822)

**Process**:
1. Validates token using `@require_auth` decorator
2. Removes token from `active_sessions` dictionary
3. Token becomes invalid immediately

---

### 2. **API Key Authentication** (Secondary Method)

#### API Key Configuration
- **Source**: Environment variable `API_KEY` (line 59)
- **Default**: `'your-api-key-change-this'` (⚠️ **MUST be changed in production**)
- **Validation**: Simple string comparison

#### API Key Validation
**Function**: `require_api_key()` decorator (lines 765-771)

**Process**:
1. Reads API key from HTTP header: `X-API-Key: <api_key>`
2. Compares with server's `API_KEY` value
3. Returns 401 if mismatch

```python
def require_api_key(f):
    @wraps(f)
    def _w(*a,**k):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"status":"error","message":"Invalid API key"}), 401
        return f(*a,**k)
    return _w
```

#### API Key Usage (Client-Side)
**Header Format**: `X-API-Key: <api_key>`

**Example**:
```bash
curl -X POST http://192.168.1.100:5001/add_user \
  -H "X-API-Key: your-api-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"card_number": "123456", "id": "user1", "name": "John Doe"}'
```

---

### 3. **Combined Authentication** (Most Secure)

#### Dual Protection
**Function**: `require_both()` decorator (lines 773-782)

**Process**:
1. First checks API key validation
2. Then checks session token authentication
3. Both must pass for request to proceed

```python
def require_both(f):
    """Defense-in-depth for mutating routes (API key + session)."""
    @wraps(f)
    def _w(*a,**k):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"status":"error","message":"Invalid API key"}), 401
        if not is_authenticated():
            return jsonify({"status":"error","message":"Authentication required"}), 401
        return f(*a,**k)
    return _w
```

#### Usage on Endpoints
Applied to **sensitive/mutating operations**:
- `POST /add_user` (line 876)
- `POST /delete_user` (line 893)
- `POST /block_user` (line 909)
- `POST /unblock_user` (line 919)
- `POST /toggle_privacy` (line 930)
- `POST /relay` (line 1248)
- `POST /set_system_time` (line 1289)
- `POST /enable_ntp` (line 1359)
- `POST /update_config` (line 1407)
- `POST /update_security` (line 1492)

#### Combined Usage Example
```bash
TOKEN="xK9jP2mN8qR5vT3wY7zA1bC4dE6fG9hI0jK2lM4nO6pQ8rS0tU2vW4xY6zA8b"
API_KEY="your-api-key-change-this"

curl -X POST http://192.168.1.100:5001/add_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"card_number": "123456", "id": "user1", "name": "John Doe"}'
```

---

## 📋 Authentication Decorators Summary

### `@require_auth` (Token Only)
- **Used for**: Read-only operations requiring user login
- **Endpoints**: 
  - `GET /get_users` (line 860)
  - `GET /get_transactions` (line 999)
  - `GET /get_today_stats` (line 1008)
  - `GET /get_analytics` (line 1026)
  - `GET /get_user_report` (line 1128)
  - `GET /get_system_time` (line 1272)
  - `GET /get_config` (line 1393)
  - `GET /download_transactions_csv` (line 1538)
  - `POST /logout` (line 817)

### `@require_api_key` (API Key Only)
- **Used for**: API-only operations (if any)
- **Note**: Not currently used in the codebase, but available

### `@require_both` (Token + API Key)
- **Used for**: Write/modify/delete operations (defense-in-depth)
- **Endpoints**: All mutating operations (see list above)

---

## 🔍 Security Features

### ✅ Strengths
1. **Cryptographically Secure Tokens**: Uses `secrets.token_urlsafe()` for token generation
2. **Thread-Safe Session Storage**: Protected by RLock
3. **Token Expiration**: Automatic cleanup of expired sessions
4. **Dual Authentication**: Sensitive operations require both token and API key
5. **Password Hashing**: SHA256 hashing (though not salted - see weaknesses)

### ⚠️ Weaknesses & Recommendations
1. **No Token Expiration Check**: `is_authenticated()` doesn't verify expiration time
   - **Recommendation**: Add expiration check in `is_authenticated()`:
   ```python
   def is_authenticated():
       token = request.headers.get('Authorization','').replace('Bearer ','')
       with SESS_LOCK:
           if token not in active_sessions:
               return False
           session = active_sessions[token]
           if datetime.now() > session['expires']:
               active_sessions.pop(token, None)
               return False
           return True
   ```

2. **Password Hashing**: Uses SHA256 without salt
   - **Current**: Simple SHA256 hash
   - **Recommendation**: Use `bcrypt` or `argon2` for password hashing

3. **In-Memory Session Storage**: Sessions lost on server restart
   - **Impact**: Users must re-login after restart
   - **Recommendation**: Consider persistent storage (Redis, database) for production

4. **API Key Storage**: Stored in plain text in environment variable
   - **Current**: Readable from environment
   - **Recommendation**: Consider key management system for production

5. **No Rate Limiting**: Login endpoint could be brute-forced
   - **Recommendation**: Add rate limiting to `/login` endpoint

6. **No HTTPS Enforcement**: Tokens sent over HTTP are visible
   - **Recommendation**: Use HTTPS in production

---

## 📊 Authentication Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. POST /login (username, password)
       ▼
┌──────────────────┐
│  Server Verifies │
│  Credentials     │
└──────┬───────────┘
       │
       ├─ Invalid → Return 401
       │
       └─ Valid → Generate Token
                  │
                  ▼
       ┌──────────────────────┐
       │ Store in active_     │
       │ sessions dictionary  │
       └──────┬───────────────┘
              │
              │ 2. Return token to client
              ▼
┌─────────────────────────┐
│ Client Stores Token     │
└──────┬──────────────────┘
       │
       │ 3. Subsequent requests with:
       │    - Authorization: Bearer <token>
       │    - X-API-Key: <api_key> (for sensitive ops)
       ▼
┌─────────────────────────┐
│ Server Validates Token  │
│ (and API key if needed) │
└──────┬──────────────────┘
       │
       ├─ Invalid → Return 401
       │
       └─ Valid → Process Request
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<sha256_hash>  # Generate with: python3 -c "import hashlib; print(hashlib.sha256('password'.encode()).hexdigest())"

# API Key
API_KEY=your-api-key-change-this  # Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"

# Session settings
SESSION_TTL_HOURS=24  # Token expiration time in hours
SESSION_SECRET=<random_secret>  # Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📝 Summary

**Authentication Method**: Token-based authentication with optional API key

**Token Generation**: 
- Uses `secrets.token_urlsafe(32)` to generate secure random tokens
- Tokens are 43-character URL-safe base64 strings

**Token Storage (Client-Side)**:
- **Web Frontend**: Stored in browser `localStorage` as `authToken`
- **REST API**: Client must store token and send with each request
- Token persists across browser sessions until manually cleared or expires

**Token Usage**:
- Client sends token in `Authorization: Bearer <token>` header
- Server validates token against in-memory `active_sessions` dictionary
- Tokens expire after 24 hours (configurable)
- Frontend automatically redirects to login on 401 (unauthorized) responses

**Security Levels**:
1. **Public**: No authentication (e.g., `/status`, `/health_check`)
2. **Token Only**: Read operations (e.g., `GET /get_users`)
3. **Token + API Key**: Write operations (e.g., `POST /add_user`)

**Complete Flow**:
1. User submits credentials via web form or API
2. Server validates credentials and generates token
3. Token returned to client in JSON response
4. Client stores token (localStorage for web, variable for API)
5. Client sends token in `Authorization` header with all requests
6. Server validates token on each request
7. Token expires after 24 hours (or as configured)
8. Expired tokens cleaned up by background worker every 5 minutes

**Key Points**:
- ✅ Token-based authentication implemented
- ✅ Session management with expiration
- ✅ Dual authentication for sensitive operations
- ✅ Client-side automatic token injection and error handling
- ⚠️ Token expiration not checked during validation (relies on cleanup worker)
- ⚠️ Sessions stored in memory (lost on restart)
- ⚠️ Token stored in localStorage (vulnerable to XSS attacks - use HTTPS)

