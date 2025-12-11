# Authentication Troubleshooting Guide

## Error: `{"message":"Authentication required","status":"error"}`

This error means your request failed authentication. Here's how to fix it:

---

## Quick Test

**Step 1: Test the authentication endpoint**
```bash
# Test Basic Auth
curl http://admin:admin123@192.168.1.2:5001/test_auth

# Should return something like:
{
  "status": "info",
  "basic_auth_detected": true,
  "basic_auth_works": true,
  ...
}
```

---

## Common Issues & Solutions

### Issue 1: Wrong Username or Password

**Symptom:** `basic_auth_works: false` in test response

**Solution:**
1. Check your `.env` file for `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH`
2. Default username: `admin`
3. Default password: `admin123`
4. Verify password hash matches:
   ```bash
   python3 -c "import hashlib; print(hashlib.sha256('admin123'.encode()).hexdigest())"
   ```

**Test:**
```bash
curl -u admin:admin123 http://192.168.1.2:5001/test_auth
```

---

### Issue 2: Basic Auth Header Not Being Sent

**Symptom:** `basic_auth_detected: false` in test response

**Common Causes:**
- URL format incorrect
- Using wrong method to send credentials

**Solutions:**

**Option A: Use curl with `-u` flag (Recommended)**
```bash
curl -u admin:admin123 http://192.168.1.2:5001/get_users
```

**Option B: Use credentials in URL**
```bash
curl http://admin:admin123@192.168.1.2:5001/get_users
```

**Option C: Manual header (for debugging)**
```bash
# Generate base64 encoded credentials
echo -n "admin:admin123" | base64
# Returns: YWRtaW46YWRtaW4xMjM=

curl -H "Authorization: Basic YWRtaW46YWRtaW4xMjM=" \
     http://192.168.1.2:5001/get_users
```

---

### Issue 3: Accessing Endpoint Requiring `@require_both`

**Symptom:** Getting 401 even with correct Basic Auth

**Solution:** 
For endpoints with `@require_both` decorator, Basic Auth alone should work. But verify you're using the correct endpoint.

**Endpoints that require `@require_both` (write operations):**
- `POST /add_user`
- `POST /delete_user`
- `POST /block_user`
- `POST /unblock_user`
- `POST /relay`
- etc.

**Test:**
```bash
# This should work with Basic Auth
curl -X POST -u admin:admin123 \
  http://192.168.1.2:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"123","id":"test","name":"Test User"}'
```

---

### Issue 4: Port or IP Address Wrong

**Symptom:** Connection refused or can't reach server

**Check:**
```bash
# Test if server is running
curl http://192.168.1.2:5001/status

# Default port is 5001
# Default host is 0.0.0.0 (all interfaces)
```

---

### Issue 5: Special Characters in Password

**Symptom:** Auth fails with special characters in password

**Solution:**
URL-encode special characters or use `-u` flag which handles this automatically:

```bash
# If password has special characters, use -u flag
curl -u "admin:pass@word#123" http://192.168.1.2:5001/get_users

# NOT: curl http://admin:pass@word#123@192.168.1.2:5001/get_users
```

---

## Step-by-Step Debugging

### Step 1: Verify Server is Running
```bash
curl http://192.168.1.2:5001/status
# Should return system status (no auth needed)
```

### Step 2: Test Authentication
```bash
curl http://admin:admin123@192.168.1.2:5001/test_auth
# Should show authentication details
```

### Step 3: Check Logs
```bash
# On the Raspberry Pi, check logs
tail -f /home/pi/accessctl/access.log

# Look for:
# - "Basic Auth successful" (good)
# - "Basic Auth failed" (check credentials)
# - "Basic Auth decode error" (check header format)
```

### Step 4: Test with Different Methods

**Method 1: curl with -u**
```bash
curl -u admin:admin123 http://192.168.1.2:5001/get_users
```

**Method 2: URL credentials**
```bash
curl http://admin:admin123@192.168.1.2:5001/get_users
```

**Method 3: Python requests**
```python
import requests
response = requests.get(
    'http://192.168.1.2:5001/get_users',
    auth=('admin', 'admin123')
)
print(response.json())
```

---

## Verification Checklist

- [ ] Server is running and accessible (`/status` endpoint works)
- [ ] Username matches `ADMIN_USERNAME` in `.env` file (default: `admin`)
- [ ] Password hash matches `ADMIN_PASSWORD_HASH` in `.env` file
- [ ] Using correct port (default: `5001`)
- [ ] Using correct IP address
- [ ] Authorization header is being sent (check with `/test_auth`)
- [ ] No typos in username or password
- [ ] Special characters in password are properly encoded

---

## Example Working Commands

```bash
# Test authentication (no auth required - returns info)
curl http://192.168.1.2:5001/test_auth

# Get users (requires auth)
curl -u admin:admin123 http://192.168.1.2:5001/get_users

# Add user (requires auth)
curl -X POST -u admin:admin123 \
  http://192.168.1.2:5001/add_user \
  -H "Content-Type: application/json" \
  -d '{"card_number":"123456","id":"user1","name":"John Doe"}'

# Get transactions (requires auth)
curl -u admin:admin123 "http://192.168.1.2:5001/get_transactions?limit=10"
```

---

## Still Not Working?

1. **Check the test endpoint response:**
   ```bash
   curl http://admin:admin123@192.168.1.2:5001/test_auth
   ```
   This will tell you exactly what's happening.

2. **Check server logs:**
   ```bash
   tail -f /home/pi/accessctl/access.log | grep -i "auth"
   ```

3. **Verify environment variables:**
   ```bash
   # On Raspberry Pi
   cat .env | grep -E "ADMIN_USERNAME|ADMIN_PASSWORD"
   ```

4. **Try with verbose curl:**
   ```bash
   curl -v -u admin:admin123 http://192.168.1.2:5001/get_users
   ```
   This shows the actual HTTP headers being sent.

---

## Quick Reference

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**Basic Auth Format:**
- Header: `Authorization: Basic <base64(username:password)>`
- URL: `http://username:password@host:port/path`
- curl: `curl -u username:password http://host:port/path`

**Test Endpoint:**
- `GET /test_auth` - No auth required, shows auth status

**Public Endpoints (no auth):**
- `GET /status`
- `GET /health_check`
- `GET /test_auth`
- `GET /login` (but needs POST with credentials)
- `POST /login` (but needs POST body with credentials)

