# Bug Fixes & New Features Summary

## Date: October 10, 2025

### Fixed Issues

#### 1. Blocked Users Still Getting Access ✅
**Problem:** When a user was blocked, they were still allowed access and the relay was being activated.

**Root Cause:** The code was checking if a user was allowed and operating the relay BEFORE checking if the user was blocked.

**Fix:** Modified the `handle_access()` function in `app.py` (lines 513-527) to:
- Check blocked status FIRST before checking allowed status
- Only operate the relay if the user is allowed AND not blocked
- Blocked users now cannot access even if they're in the allowed set

**Code Changes:**
```python
# Check blocked status FIRST - blocked users cannot access even if they're in allowed set
if is_blocked:
    status = "Blocked"; name = "Blocked"
    privacy_protected = False
elif is_allowed:
    # ... grant access and operate relay
else:
    status = "Access Denied"; name = "Unknown"
```

---

#### 2. CPU Temperature Monitoring Added ✅
**Problem:** No way to monitor the Pi Zero 2W temperature from the dashboard.

**Solution:** Added comprehensive temperature monitoring:

**Backend Changes (`app.py`):**
- Added `get_cpu_temperature()` function (lines 106-114) that reads from `/sys/class/thermal/thermal_zone0/temp`
- Updated `/status` endpoint to include temperature data (lines 720-722)
- Temperature is read in Celsius with 1 decimal precision

**Frontend Changes:**
- Added new temperature stat card in `dashboard.html` (lines 149-159)
- Updated `loadSystemStatus()` in `main.js` (lines 102-118) to display temperature
- Color coding implemented:
  - **Green:** < 60°C (Normal)
  - **Yellow:** 60-75°C (Warm)
  - **Red:** > 75°C (Hot)
- Temperature auto-refreshes every 30 seconds with other system stats

---

#### 3. "Open and Hold" Button Issue Fixed ✅
**Problem:** When "Open & Hold" button was pressed, showing a valid RFID card would return the relay to normal state instead of maintaining the hold state until "Pulse" button was pressed.

**Root Cause:** RFID card scans always triggered relay operations without checking if the relay was in manual override mode.

**Fix:** Implemented relay state tracking in `app.py`:

**New State Management (lines 466-487):**
- Added `relay_hold_states` dictionary to track each relay's manual override state
- Added `RELAY_HOLD_LOCK` for thread-safe state management
- Modified `operate_relay()` function to:
  - Set hold state when "open_hold" or "close_hold" is activated
  - Ignore RFID-triggered relay operations when in hold mode
  - Clear hold state only when "normal" (pulse) is explicitly requested via button

**Behavior:**
- **Open & Hold:** Relay stays LOW until Pulse button is pressed
- **Close & Hold:** Relay stays HIGH until Pulse button is pressed
- **RFID cards:** Do NOT affect relay when in hold mode
- **Pulse button:** Returns relay to normal operation and clears hold state

---

## New Features Added

#### 4. System Time Configuration ✅
**Feature:** Added comprehensive time management to the Configuration tab.

**Capabilities:**
- **Real-time Display:** Shows both system time and PC/browser time side-by-side with live updates every second
- **Time Difference Detection:** Automatically warns if system time differs from PC time by more than 10 seconds
- **Sync with PC:** One-click synchronization to set system time to match PC time
- **NTP Synchronization:** Enable automatic internet time sync for ongoing accuracy
- **Manual Time Setting:** Set any specific date and time using a datetime picker
- **Timezone Display:** Shows timezone information for both system and PC

**Why This is Important:**
- Pi Zero 2W lacks a real-time clock (RTC)
- Time resets to default on power loss
- Accurate timestamps are critical for transaction logging
- Prevents confusion with mismatched transaction times

**Implementation Details:**

**Backend (app.py):**
- Added `/get_system_time` endpoint (lines 1138-1153) - Returns current system time with timezone
- Added `/set_system_time` endpoint (lines 1155-1223) - Sets system time via timedatectl or date command
- Added `/enable_ntp` endpoint (lines 1225-1256) - Enables/disables NTP time synchronization
- All endpoints require authentication and log time changes for audit

**Frontend (dashboard.html):**
- Added Time Configuration section in Configuration tab (lines 707-787)
- Real-time clock display for both system and PC time
- Visual time difference alert with color coding
- Three quick action buttons plus manual time input
- Comprehensive help text and warnings

**JavaScript (main.js):**
- `loadSystemTime()` - Fetches and displays system time (lines 1323-1339)
- `startBrowserTimeClock()` - Updates PC time every second (lines 1341-1361)
- `syncWithPcTime()` - Syncs system time with browser timestamp (lines 1413-1440)
- `enableNtpSync()` - Enables NTP synchronization (lines 1442-1466)
- `setManualTime()` - Sets manual time from datetime picker (lines 1468-1505)
- `checkTimeDifference()` - Calculates and displays time difference warning (lines 1384-1411)

**Security Features:**
- Requires sudo permissions (passwordless for specific commands)
- All time changes logged with username and timestamp
- Both API key and session authentication required
- Audit trail in access.log

**Sudo Permissions Setup:**
```bash
# Create sudoers file
sudo visudo -f /etc/sudoers.d/access-control-time

# Add these lines (replace 'pi' with actual username)
pi ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-time *
pi ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-ntp *
pi ALL=(ALL) NOPASSWD: /usr/bin/date -s *

# Set permissions
sudo chmod 0440 /etc/sudoers.d/access-control-time
```

See `TIME_CONFIGURATION_SETUP.md` for complete setup guide and troubleshooting.

---

## Testing Recommendations

### 1. Blocked User Test
1. Add a user to the system
2. Block the user from the Users tab
3. Scan their card - should see "Blocked" status
4. Verify relay does NOT activate
5. Check transaction log shows "Blocked" status

### 2. Temperature Monitoring Test
1. Navigate to Dashboard
2. Verify CPU temperature is displayed with °C unit
3. Check color coding based on temperature
4. Verify temperature updates every 30 seconds
5. On a real Pi Zero 2W, temperature should be 40-65°C typically

### 3. Open & Hold Test
1. Go to Relay Control tab
2. Press "Open & Hold" on any relay
3. Scan a valid RFID card
4. Verify relay stays in open state (does not pulse)
5. Press "Pulse (1s)" button
6. Verify relay returns to normal operation
7. Scan valid card again - should pulse normally

### 4. Time Configuration Test
**Prerequisites:** Complete sudo permissions setup (see TIME_CONFIGURATION_SETUP.md)

1. **View Time Display:**
   - Navigate to Configuration tab
   - Scroll to "System Time Configuration" section
   - Verify system time and PC time are both displayed
   - Both clocks should update every second
   - If times differ by >10 seconds, warning should appear

2. **Test Sync with PC:**
   - If times are different, click "Sync with PC Time"
   - Confirm the action
   - Verify system time updates to match PC time
   - Warning should disappear if it was showing
   - Check from terminal: `date` should show synced time

3. **Test Manual Time Setting:**
   - Click on datetime-local input
   - Select a time (e.g., 2 hours in the future)
   - Click "Set Time" button
   - Confirm the action
   - Verify system time updates to selected time
   - Check from terminal to confirm

4. **Test NTP Sync (if internet available):**
   - Click "Enable NTP Sync" button
   - Confirm the action
   - Wait 10-30 seconds
   - Click "Refresh" button
   - System time should sync with internet time servers
   - Check with: `timedatectl status` (should show NTP: active)

5. **Verify Permissions:**
   - All commands should work without password prompts
   - Check logs for time change entries: `tail -f ~/accessctl/access.log`
   - Each change should be logged with username

---

## Files Modified

1. **app.py** (Main backend)
   - Lines 106-114: Added `get_cpu_temperature()` function
   - Lines 466-487: Added relay hold state management
   - Lines 513-527: Fixed blocked user access control
   - Lines 720-722: Added temperature to status endpoint
   - Lines 1138-1153: Added `get_system_time()` endpoint
   - Lines 1155-1223: Added `set_system_time()` endpoint
   - Lines 1225-1256: Added `enable_ntp()` endpoint

2. **templates/dashboard.html** (Dashboard UI)
   - Lines 149-159: Added CPU temperature stat card
   - Lines 707-787: Added System Time Configuration section

3. **static/js/main.js** (Dashboard JavaScript)
   - Lines 82-119: Updated `loadSystemStatus()` to display temperature with color coding
   - Lines 913-971: Updated `initConfiguration()` to include time handlers
   - Lines 1317-1505: Added complete time management functionality

4. **TIME_CONFIGURATION_SETUP.md** (New documentation)
   - Complete setup guide for time configuration
   - Sudo permissions configuration
   - API documentation
   - Troubleshooting guide

5. **BUG_FIXES_SUMMARY.md** (Updated)
   - Added time configuration feature documentation

---

## Notes

- All changes are backward compatible
- No database migrations required
- Temperature reading is Pi-specific; will return `null` on non-Pi systems
- Relay hold states are stored in memory and reset on service restart
- Changes are thread-safe using appropriate locks

---

## Deployment

To apply these fixes and new features:

1. **Stop the access control service:**
   ```bash
   sudo systemctl stop access-control
   ```

2. **Pull the updated files:**
   - app.py
   - templates/dashboard.html
   - static/js/main.js
   - TIME_CONFIGURATION_SETUP.md
   - BUG_FIXES_SUMMARY.md

3. **Configure sudo permissions for time management:**
   ```bash
   # Create sudoers file
   sudo visudo -f /etc/sudoers.d/access-control-time
   
   # Add these lines (replace 'pi' with your username):
   pi ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-time *
   pi ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-ntp *
   pi ALL=(ALL) NOPASSWD: /usr/bin/date -s *
   
   # Save and exit (Ctrl+X, then Y, then Enter)
   
   # Set proper permissions
   sudo chmod 0440 /etc/sudoers.d/access-control-time
   
   # Verify configuration
   sudo visudo -c
   ```

4. **Restart the service:**
   ```bash
   sudo systemctl start access-control
   ```

5. **Monitor logs for any issues:**
   ```bash
   sudo journalctl -u access-control -f
   ```

6. **Test all fixes and features:**
   - Blocked user access (should be denied)
   - Temperature display (should show CPU temp)
   - Relay open/hold (should ignore RFID when held)
   - Time configuration (should sync/set time)

