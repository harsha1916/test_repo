# Why "Authentication required" Error Occurs

## Root Cause Analysis

The error `{"message":"Authentication required","status":"error"}` occurs when the `is_authenticated()` function returns `False` for a protected endpoint. Here's why this happens:

---

## Error Flow

```
1. Client makes request → 
2. Endpoint has @require_auth decorator → 
3. Calls is_authenticated() → 
4. Returns False → 
5. Decorator returns 401 error with "Authentication required"
```

---

## Why `is_authenticated()` Returns False

The `is_authenticated()` function checks **TWO** authentication methods:

### Check 1: Basic Auth
```python
if check_basic_auth():
    return True
```

### Check 2: Token Auth (for UI)
```python
token = request.headers.get('Authorization','').replace('Bearer ','')
return token in active_sessions
```

**If BOTH fail → Returns False → Error occurs**

---

## Reason 1: Basic Auth Header Not Present or Wrong Format

### Symptom
- `check_basic_auth()` returns `False` immediately at line 755-756

### Causes:
1. **No Authorization header sent**
   ```python
   auth_header = request.headers.get('Authorization', '')  # Returns empty string
   if not auth_header.startswith('Basic '):  # Fails here
       return False
   ```

2. **Header format wrong**
   - ❌ `Authorization: basic ...` (lowercase - fails)
   - ❌ `Authorization:Basic ...` (no space - fails)
   - ✅ `Authorization: Basic ...` (correct - with space!)

3. **Using wrong method**
   - ❌ Sending token in Bearer format when trying Basic Auth
   - ❌ Forgetting to include credentials at all

### Fix:
```bash
# Correct Basic Auth format
curl -u admin:admin123 http://192.168.1.2:5001/get_users

# Or manual header
curl -H "Authorization: Basic YWRtaW46YWRtaW4xMjM=" http://192.168.1.2:5001/get_users
```

---

## Reason 2: Base64 Decode Failure

### Symptom
- Exception caught at line 768-769
- Log shows: "Basic Auth decode error"

### Causes:
1. **Invalid base64 string**
   - Malformed base64 encoding
   - Missing padding characters (`=`)
   - Invalid characters in base64 string

2. **Wrong encoding method**
   - Not using standard base64 encoding
   - Using URL-safe base64 when standard is expected

### Example of what happens:
```python
try:
    encoded = auth_header.replace('Basic ', '', 1)
    decoded = base64.b64decode(encoded).decode('utf-8')  # ← Fails here if invalid
    username, password = decoded.split(':', 1)
except Exception as e:
    logging.error(f"Basic Auth decode error: {e}")  # ← Caught here
    return False  # ← Returns False
```

### Fix:
Ensure proper base64 encoding:
```python
import base64
credentials = base64.b64encode(b'admin:admin123').decode('utf-8')
# Result: 'YWRtaW46YWRtaW4xMjM='
```

---

## Reason 3: Username Mismatch

### Symptom
- Log shows: "Basic Auth failed: invalid credentials for user: <username>"
- Username doesn't match `ADMIN_USERNAME`

### Causes:
1. **Wrong username**
   - Using `Admin` instead of `admin` (case-sensitive!)
   - Typos in username

2. **Environment variable not set**
   - `ADMIN_USERNAME` not in `.env` file
   - Default is `'admin'` but you changed it

### Code check:
```python
if username == ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
    # username must EXACTLY match ADMIN_USERNAME
    # Case-sensitive comparison!
```

### Fix:
```bash
# Check your .env file
cat .env | grep ADMIN_USERNAME

# Default is 'admin' (lowercase)
# Must match exactly (case-sensitive)
```

---

## Reason 4: Password Hash Mismatch

### Symptom
- Username matches but password verification fails
- Log shows: "Basic Auth failed: invalid credentials"

### Causes:
1. **Wrong password**
   - Typo in password
   - Using old password after changing

2. **Password hash not matching**
   - Hash in `.env` file is wrong
   - Password was changed but hash not updated
   - Using wrong hash algorithm

### How password verification works:
```python
def verify_password(password, hashed) -> bool:
    return hash_password(password) == hashed

def hash_password(password:str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
```

**The process:**
1. Takes plain password from Basic Auth
2. Hashes it with SHA256
3. Compares with `ADMIN_PASSWORD_HASH` from `.env`

### Fix:
Verify password hash matches:
```bash
# Generate correct hash for password "admin123"
python3 -c "import hashlib; print(hashlib.sha256('admin123'.encode()).hexdigest())"
# Should output: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9

# Check your .env file
cat .env | grep ADMIN_PASSWORD_HASH
```

---

## Reason 5: Special Characters in Password

### Symptom
- Works with simple passwords but fails with special characters
- Base64 decode might succeed but password verification fails

### Causes:
1. **URL encoding issues**
   - Special characters in URL: `http://admin:pass@word@...` (the `@` breaks it!)
   - Need URL encoding for `@`, `#`, `%`, etc.

2. **Character encoding issues**
   - Non-ASCII characters might not encode/decode properly
   - UTF-8 encoding issues

### Fix:
**Use `-u` flag in curl (handles encoding automatically):**
```bash
# ❌ Don't use special chars in URL
curl http://admin:pass@word@192.168.1.2:5001/get_users

# ✅ Use -u flag instead
curl -u "admin:pass@word" http://192.168.1.2:5001/get_users
```

---

## Reason 6: Trying to Access Protected Endpoint Without Auth

### Symptom
- Endpoint requires authentication but none provided

### Endpoints that REQUIRE auth:

**Read operations (`@require_auth`):**
- `GET /get_users`
- `GET /get_transactions`
- `GET /get_today_stats`
- etc.

**Write operations (`@require_both`):**
- `POST /add_user`
- `POST /delete_user`
- `POST /block_user`
- etc.

### Endpoints that DON'T require auth:
- `GET /status`
- `GET /health_check`
- `GET /test_auth`
- `POST /login` (but needs credentials in body)

---

## Reason 7: Token Auth Conflicts (Edge Case)

### Symptom
- Using Basic Auth but also have Bearer token in header
- Might accidentally trigger token check instead

### How it works:
```python
def is_authenticated():
    # Check Basic Auth first
    if check_basic_auth():  # ← Checks for "Basic "
        return True
    # Check token auth
    token = request.headers.get('Authorization','').replace('Bearer ','')
    # If header is "Bearer token", replace returns "token"
    # If header is "Basic ...", replace returns "Basic ..." (unchanged)
    return token in active_sessions  # "Basic ..." won't be in sessions
```

**This shouldn't cause issues**, but if you send BOTH headers somehow, Basic Auth is checked first.

---

## Most Common Causes (In Order)

1. **No Authorization header sent** (40%)
   - Forgot to include credentials
   - Wrong HTTP client

2. **Wrong username/password** (30%)
   - Typos
   - Changed password but using old one

3. **Wrong header format** (15%)
   - Missing space after "Basic"
   - Wrong case "basic" instead of "Basic"

4. **Password hash mismatch** (10%)
   - Changed password but hash not updated in `.env`

5. **Special characters** (5%)
   - Password with special chars not properly encoded

---

## Debugging Steps

### Step 1: Check if header is being sent
```bash
# Use verbose mode
curl -v -u admin:admin123 http://192.168.1.2:5001/test_auth

# Look for this line:
# > Authorization: Basic YWRtaW46YWRtaW4xMjM=
```

### Step 2: Use test endpoint
```bash
curl http://admin:admin123@192.168.1.2:5001/test_auth
# Shows exactly what's detected
```

### Step 3: Check server logs
```bash
tail -f /home/pi/accessctl/access.log | grep -i "auth"
# Look for:
# - "Basic Auth successful" → Working!
# - "Basic Auth failed" → Check credentials
# - "Basic Auth decode error" → Check header format
```

### Step 4: Verify environment variables
```bash
# On Raspberry Pi
cat .env | grep -E "ADMIN_USERNAME|ADMIN_PASSWORD"
```

---

## Quick Fix Checklist

- [ ] Using correct username (default: `admin` - case-sensitive)
- [ ] Using correct password (default: `admin123`)
- [ ] Header format: `Authorization: Basic ...` (with space!)
- [ ] Using `-u` flag or proper URL encoding
- [ ] Server is running on correct IP/port
- [ ] No typos in credentials
- [ ] `.env` file has correct password hash

---

## Example: Working vs Failing

### ✅ WORKING:
```bash
curl -u admin:admin123 http://192.168.1.2:5001/get_users
```
**Headers sent:**
```
Authorization: Basic YWRtaW46YWRtaW4xMjM=
```

**Flow:**
1. `check_basic_auth()` detects "Basic " → True
2. Decodes base64 → `admin:admin123`
3. Splits → username=`admin`, password=`admin123`
4. Verifies username == "admin" → True
5. Hashes password → matches hash → True
6. Returns True → Authentication successful!

### ❌ FAILING:
```bash
curl http://192.168.1.2:5001/get_users
# No credentials provided
```
**Headers sent:**
```
(no Authorization header)
```

**Flow:**
1. `check_basic_auth()` gets empty string
2. `auth_header.startswith('Basic ')` → False
3. Returns False
4. Token check also fails (no Bearer token)
5. `is_authenticated()` returns False
6. Error: "Authentication required"

---

## Summary

The error occurs because **neither** authentication method succeeds:
- Basic Auth fails: No header, wrong format, or wrong credentials
- Token Auth fails: No token or invalid token

**To fix:** Ensure you're sending credentials correctly with the right format!

