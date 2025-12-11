# 🚀 Advanced Configuration Features

## Overview

Your access control system now includes powerful configuration features to prevent duplicate transactions, change security settings, and manage entity IDs - all through the secure web interface!

---

## 🆕 NEW FEATURES

### 1. **Tag Re-Detect Delay** (Duplicate Prevention)
### 2. **Entry/Exit Tracking** (Smart Transaction Creation)
### 3. **Entity ID Management** (Multi-Site Support)
### 4. **Password & API Key Changes** (Enhanced Security)

---

## 1. 🏷️ TAG RE-DETECT DELAY

### What It Does:
Prevents the same card from being read multiple times within a specified time period, reducing duplicate transaction records.

### Configuration:
- **Location:** Configuration tab → Duplicate Prevention & Tracking
- **Setting:** "Tag Re-Detect Delay (seconds)"
- **Range:** 1-300 seconds
- **Default:** 60 seconds

### How It Works:
```
Card 12345 scanned at 10:00:00 ✓ Transaction created
Card 12345 scanned at 10:00:30 ✗ Ignored (within 60s window)
Card 12345 scanned at 10:01:15 ✓ Transaction created (>60s elapsed)
```

### Use Cases:
- **Very short delay (1-5s):** Ultra high-traffic turnstiles, rapid entry/exit
- **Short delay (10-30s):** High-traffic areas, quick turnstiles
- **Medium delay (60s):** Standard office doors
- **Long delay (120-300s):** Parking gates, infrequent access points

### Example Configuration:
```json
{
  "scan_delay_seconds": 60
}
```

---

## 2. 🔄 ENTRY/EXIT TRACKING

### What It Does:
**Revolutionary feature** that only creates transactions when the time gap between card scans meets a minimum threshold. Perfect for preventing excessive transaction logs!

### Configuration:
- **Location:** Configuration tab → Duplicate Prevention & Tracking
- **Toggle:** "Enable Entry/Exit Tracking" checkbox
- **Setting:** "Minimum Entry/Exit Gap (seconds)"
- **Range:** 1-300 seconds (1 second to 5 minutes)
- **Default:** 300 seconds (5 minutes)

### How It Works:

#### When DISABLED (Default):
```
Every card scan creates a transaction (standard behavior)
```

#### When ENABLED:
```
First Scan:  Card 12345 at 10:00:00 → No transaction yet (entry recorded)
Second Scan: Card 12345 at 10:02:00 → No transaction (gap < 5 min)
Third Scan:  Card 12345 at 10:06:00 → Transaction created! (gap >= 5 min)
```

### Backend Logic:

```python
class EntryExitTracker:
    def should_create_transaction(self, card_int, reader_id):
        if not self.enabled:
            return True  # Always create (standard mode)
        
        if card_int not in self.last_scan:
            # First scan - record but don't create transaction
            self.last_scan[card_int] = {"timestamp": now, "reader": reader_id}
            return False
        
        gap = now - self.last_scan[card_int]["timestamp"]
        
        if gap >= self.min_gap_seconds:
            # Gap satisfied - create transaction
            self.last_scan[card_int] = {"timestamp": now, "reader": reader_id}
            return True
        else:
            # Too soon - don't create transaction
            return False
```

### Use Cases:

#### Scenario 1: Office Building
**Problem:** Employee cards trigger readers multiple times as they move around  
**Solution:** Enable with 300s (5 min) gap  
**Result:** Only log when they leave/return after meaningful absence

#### Scenario 2: Warehouse  
**Problem:** Workers stay in area all day, constant re-reads  
**Solution:** Enable with 180s (3 min) gap  
**Result:** Log only actual entries/exits, not movement within area

#### Scenario 3: Fast Turnstile
**Problem:** Rapid card scans in busy entrance  
**Solution:** Enable with 5s gap  
**Result:** Allow quick back-and-forth while preventing spam

### Example Configuration:
```json
{
  "entry_exit_tracking": {
    "enabled": true,
    "min_gap_seconds": 300
  }
}
```

### Important Notes:

⚠️ **First Scan Behavior:** When enabled, the FIRST scan of any card will NOT create a transaction. Only subsequent scans (after the gap is satisfied) create transactions.

✅ **Per-Card Tracking:** Each card is tracked independently. Card A entering doesn't affect Card B's tracking.

🔄 **Relay Still Works:** Even when a transaction isn't created, the relay STILL operates if the user is authorized. Access is granted, just not logged every time.

---

## 3. 🌐 ENTITY ID MANAGEMENT

### What It Does:
Configure the Firebase entity ID through the web interface, allowing easy multi-site management.

### Configuration:
- **Location:** Configuration tab → Entity Configuration
- **Field:** "Entity ID (Firebase)"
- **Default:** "default_entity"
- **Format:** Alphanumeric string

### How It Works:
The entity ID determines which Firebase collection stores your transactions:
```
Firebase Structure:
  entities/
    ├── entity1/
    │   └── transactions/
    ├── entity2/
    │   └── transactions/
    └── site_branch_A/
        └── transactions/
```

### Use Cases:

#### Single Site:
```
entity_id: "main_office"
```

#### Multiple Buildings:
```
Building 1: entity_id: "building_1"
Building 2: entity_id: "building_2"
Building 3: entity_id: "building_3"
```

#### Multi-Organization:
```
Company A: entity_id: "company_a"
Company B: entity_id: "company_b"
```

### Example Configuration:
```json
{
  "entity_id": "main_office_building_A"
}
```

### Important Notes:
- Entity ID changes take effect immediately
- Existing transactions remain under old entity ID
- New transactions use the new entity ID
- Can be reverted at any time

---

## 4. 🔒 SECURITY SETTINGS

### What It Does:
Change admin password and API key through the web interface with proper authentication.

### Configuration:
- **Location:** Configuration tab → Security Settings
- **Endpoint:** `/update_security`
- **Authentication:** Requires BOTH session token + current API key

### Features:

#### A. Change Admin Password
- **Field:** "New Admin Password"
- **Requirement:** Minimum 8 characters
- **Confirmation:** Must match confirm password
- **Hashing:** SHA-256 (configurable)

#### B. Change API Key
- **Field:** "New API Key"
- **Requirement:** Minimum 16 characters
- **Important:** Must update localStorage after change!

### How To Use:

#### Step 1: Access Security Settings
```
Configuration tab → Scroll to "Security Settings" section
```

#### Step 2: Change Password (Optional)
```
1. Enter new password (min 8 chars)
2. Confirm password
3. Leave API key blank if not changing
4. Click "Update Security Settings"
```

#### Step 3: Change API Key (Optional)
```
1. Enter new API key (min 16 chars)
2. Leave passwords blank if not changing
3. Click "Update Security Settings"
```

#### Step 4: Update Browser After API Key Change
```
Method 1: Use alert prompt that appears
Method 2: Press F12 → Console → Run:
  setApiKey('your-new-api-key')
Method 3: Visit /setup page and enter new key
```

### Security Features:

✅ **Dual Authentication Required**
- Current valid session token
- Current valid API key
- Both must be present and correct

✅ **Validation**
- Password minimum 8 characters
- API key minimum 16 characters
- Passwords must match

✅ **Audit Logging**
- All security changes logged
- Includes username of who made change
- Timestamped entries

✅ **Confirmation Required**
- JavaScript confirm dialog before submit
- Prevents accidental changes

### Example API Call:
```javascript
// Change password only
{
  "new_password": "NewSecurePass123"
}

// Change API key only
{
  "new_api_key": "new-super-secret-key-12345678"
}

// Change both
{
  "new_password": "NewSecurePass123",
  "new_api_key": "new-super-secret-key-12345678"
}
```

### Example Configuration:
```json
{
  "new_password": "MyNewPassword123",
  "new_api_key": "my-new-secure-api-key-2025"
}
```

### Important Warnings:

⚠️ **After Changing API Key:**
1. Current browser localStorage will be outdated
2. You MUST update it: `setApiKey('new-key')`
3. All API requests will fail with 401 until updated
4. An alert will remind you to update it

⚠️ **After Changing Password:**
1. Current session remains valid
2. Next login requires new password
3. Update password manager / documentation

⚠️ **Lost Credentials:**
- If you lose API key: Edit `.env` file and restart service
- If you lose password: Edit `.env` file and restart service
- Keep backups of credentials!

---

## 📊 COMPLETE CONFIGURATION STRUCTURE

Here's the complete `config.json` with all new features:

```json
{
  "wiegand_bits": {
    "reader_1": 26,
    "reader_2": 26,
    "reader_3": 34
  },
  "wiegand_timeout_ms": 25,
  "scan_delay_seconds": 60,
  "entry_exit_tracking": {
    "enabled": true,
    "min_gap_seconds": 300
  },
  "entity_id": "main_office"
}
```

---

## 🎯 COMMON CONFIGURATION SCENARIOS

### Scenario 1: Standard Office
```json
{
  "scan_delay_seconds": 60,
  "entry_exit_tracking": {
    "enabled": false
  },
  "entity_id": "office_main"
}
```

### Scenario 2: High-Traffic Area (Prevent Spam)
```json
{
  "scan_delay_seconds": 30,
  "entry_exit_tracking": {
    "enabled": true,
    "min_gap_seconds": 300
  },
  "entity_id": "cafeteria"
}
```

### Scenario 3: Fast Turnstile Area
```json
{
  "scan_delay_seconds": 5,
  "entry_exit_tracking": {
    "enabled": true,
    "min_gap_seconds": 10
  },
  "entity_id": "main_turnstile"
}
```

### Scenario 4: Multi-Site Deployment
```json
// Site A
{
  "entity_id": "site_A",
  "entry_exit_tracking": {"enabled": false}
}

// Site B  
{
  "entity_id": "site_B",
  "entry_exit_tracking": {"enabled": false}
}
```

---

## 🔧 TROUBLESHOOTING

### Issue: Too Many Duplicate Transactions

**Solution 1:** Increase Tag Re-Detect Delay
```
Change scan_delay_seconds from 60 to 120 or higher
```

**Solution 2:** Enable Entry/Exit Tracking
```
Enable entry_exit_tracking with 300s gap
```

### Issue: Not Enough Transactions Logged

**Solution:** Check Entry/Exit Tracking
```
If enabled, only transactions after gap are logged
Consider disabling or reducing min_gap_seconds
```

### Issue: Can't Login After Password Change

**Solution:**
```bash
# Edit .env file
nano /home/pi/accessctl/.env

# Update ADMIN_PASSWORD_HASH with new hash
python3 -c "import hashlib; print(hashlib.sha256('your-password'.encode()).hexdigest())"

# Restart service
sudo systemctl restart access-control
```

### Issue: 401 Errors After API Key Change

**Solution:**
```javascript
// Update localStorage
setApiKey('your-new-api-key')

// Or visit setup page
window.location.href = '/setup'
```

### Issue: Wrong Entity ID Used

**Solution:**
```
1. Go to Configuration tab
2. Update Entity ID field
3. Save configuration
4. New transactions use correct entity ID
```

---

## 📈 MONITORING & LOGGING

All configuration changes are logged:

```bash
# View configuration logs
tail -f /home/pi/accessctl/access.log | grep -i config

# Example log entries:
[2025-10-07 14:30:15] INFO Configuration updated and readers reinitialized
[2025-10-07 14:30:15] INFO Entry/Exit tracking: enabled, gap=300s
[2025-10-07 14:30:15] INFO Entity ID updated to: main_office
[2025-10-07 14:32:00] WARNING Admin password changed by admin
[2025-10-07 14:33:00] WARNING API key changed by admin
[2025-10-07 14:35:00] INFO Entry/Exit tracking: Skipped transaction for card 12345 (gap not satisfied)
```

---

## ✅ TESTING CHECKLIST

After configuration changes:

### Tag Re-Detect Delay:
- [ ] Scan same card twice quickly
- [ ] Verify second scan ignored
- [ ] Wait for delay period
- [ ] Verify next scan creates transaction

### Entry/Exit Tracking:
- [ ] Enable feature with 180s gap
- [ ] Scan card first time (no transaction)
- [ ] Scan again within 180s (no transaction)
- [ ] Scan after 180s (transaction created)
- [ ] Check logs for "Skipped transaction" messages

### Entity ID:
- [ ] Change entity ID in config
- [ ] Create test transaction
- [ ] Check Firebase for new entity collection
- [ ] Verify old transactions under old entity
- [ ] Verify new transactions under new entity

### Security Settings:
- [ ] Change password
- [ ] Logout and login with new password
- [ ] Change API key
- [ ] Update localStorage with new key
- [ ] Verify API calls work

---

## 🎓 BEST PRACTICES

### For Tag Re-Detect Delay:
1. Start with 60s (default)
2. Monitor transaction logs
3. Adjust based on your access patterns
4. Higher values for parking/gates
5. Lower values for turnstiles

### For Entry/Exit Tracking:
1. Only enable if you have duplicate transaction issues
2. Set gap based on typical stay duration
3. Test thoroughly before production use
4. Document the behavior for operators
5. Consider disabling for critical access points

### For Entity ID:
1. Use descriptive names (building_A, site_main)
2. Document your entity structure
3. Keep consistent naming scheme
4. Don't change frequently (breaks continuity)
5. Use same ID for all readers in same location

### For Security Settings:
1. Change defaults immediately in production
2. Use strong passwords (12+ chars)
3. Use long random API keys (32+ chars)
4. Document credential changes
5. Test after each change
6. Keep secure backup of credentials

---

## 🔮 ADVANCED USAGE

### Programmatic Configuration Update:

```python
import requests

# Update configuration via API
config = {
    "wiegand_bits": {"reader_1": 34, "reader_2": 26, "reader_3": 26},
    "scan_delay_seconds": 90,
    "entry_exit_tracking": {"enabled": True, "min_gap_seconds": 600},
    "entity_id": "warehouse_sector_B"
}

response = requests.post(
    'http://192.168.1.100:5001/update_config',
    headers={
        'X-API-Key': 'your-api-key',
        'Authorization': 'Bearer your-session-token',
        'Content-Type': 'application/json'
    },
    json={'config': config}
)

print(response.json())
```

### Batch Security Update:

```python
import requests

# Change both password and API key
security_data = {
    "new_password": "NewSecurePassword2025",
    "new_api_key": "new-secure-api-key-with-high-entropy-12345678"
}

response = requests.post(
    'http://192.168.1.100:5001/update_security',
    headers={
        'X-API-Key': 'current-api-key',
        'Authorization': 'Bearer your-session-token',
        'Content-Type': 'application/json'
    },
    json=security_data
)

print(response.json())
```

---

## 📚 RELATED DOCUMENTATION

- **CONFIGURATION_GUIDE.md** - Wiegand format configuration
- **README_FRONTEND.md** - Frontend features overview
- **SETUP_GUIDE.md** - Initial system setup
- **UPDATE_NOTES.md** - Technical implementation details

---

**All features production-ready and fully tested!** 🎉

Version: 1.2  
Last Updated: October 2025  
Status: ✅ Complete and Deployed

