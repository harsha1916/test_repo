# ⏰ System Time Configuration Setup Guide

## Overview

The access control system now includes time configuration functionality that allows you to:
- View system time vs. PC/browser time in real-time
- Sync system time with your PC's time
- Enable automatic NTP time synchronization
- Manually set a specific date and time

This is especially important for Raspberry Pi Zero 2W devices that don't have a real-time clock (RTC) and lose time when powered off.

---

## Features

### 1. **Time Display**
- **System Time**: Current time on the Raspberry Pi (updates every second)
- **PC Time**: Your computer's current time (updates every second)
- **Time Difference Alert**: Automatically warns if system time differs by more than 10 seconds

### 2. **Sync with PC Time**
- One-click synchronization with your computer's time
- Useful for initial setup or after power loss
- Requires sudo permissions

### 3. **Enable NTP Sync**
- Automatic internet time synchronization
- Keeps time accurate when internet is available
- Requires sudo permissions and internet connection

### 4. **Manual Time Setting**
- Set any specific date and time manually
- Useful for offline scenarios or specific requirements
- Uses datetime-local HTML5 input for easy selection

---

## Required Sudo Permissions Setup

For time configuration to work, the application needs passwordless sudo access to specific commands.

### Step 1: Create Sudoers Configuration File

```bash
sudo visudo -f /etc/sudoers.d/access-control-time
```

### Step 2: Add the Following Lines

Replace `pi` with the username running the access control service:

```bash
# Allow access control service to set system time without password
pi ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-time *
pi ALL=(ALL) NOPASSWD: /usr/bin/timedatectl set-ntp *
pi ALL=(ALL) NOPASSWD: /usr/bin/date -s *
```

### Step 3: Set Proper Permissions

```bash
sudo chmod 0440 /etc/sudoers.d/access-control-time
```

### Step 4: Verify Configuration

```bash
sudo visudo -c
```

You should see: `parsed OK`

### Step 5: Test Sudo Access

```bash
# Test timedatectl (should not ask for password)
sudo timedatectl set-time "2025-10-10 12:00:00"

# Test NTP (should not ask for password)
sudo timedatectl set-ntp true
```

---

## API Endpoints

### GET `/get_system_time`
**Authentication Required**: Yes

**Response**:
```json
{
  "status": "success",
  "system_time": "2025-10-10T15:30:45.123456",
  "timestamp": 1728574245,
  "timezone": "UTC +0000",
  "formatted": "2025-10-10 15:30:45"
}
```

### POST `/set_system_time`
**Authentication Required**: Yes (API Key + Session)

**Request Body**:
```json
{
  "timestamp": 1728574245
}
```

**Response**:
```json
{
  "status": "success",
  "message": "System time set to 2025-10-10 15:30:45",
  "new_time": "2025-10-10T15:30:45"
}
```

### POST `/enable_ntp`
**Authentication Required**: Yes (API Key + Session)

**Request Body**:
```json
{
  "enable": true
}
```

**Response**:
```json
{
  "status": "success",
  "message": "NTP time synchronization enabled"
}
```

---

## Usage Instructions

### From the Web Dashboard

1. **Navigate to Configuration Tab**
   - Click on "Configuration" in the left sidebar
   - Scroll down to "🕐 System Time Configuration" section

2. **View Time Status**
   - System time is displayed in blue on the left
   - Your PC time is displayed in green on the right
   - If times differ by more than 10 seconds, a warning alert appears

3. **Sync with PC Time**
   - Click "Sync with PC Time" button
   - Confirm the action
   - System time will be set to match your PC's current time

4. **Enable NTP Synchronization**
   - Click "Enable NTP Sync" button
   - Confirm the action
   - System will automatically sync with internet time servers
   - Requires active internet connection

5. **Set Manual Time**
   - Click on the date/time input field
   - Select desired date and time
   - Click "Set Time" button
   - Confirm the action

6. **Refresh**
   - Click "Refresh" button to reload system time
   - Useful after making changes or to verify synchronization

---

## Troubleshooting

### Error: "Failed to set system time: Ensure sudo permissions are configured"

**Solution**:
1. Verify sudoers configuration (see setup steps above)
2. Check that the user running the service has proper permissions
3. Test sudo commands manually as shown in Step 5

### Error: "Failed to configure NTP"

**Possible Causes**:
- No internet connection
- NTP service not installed
- Sudo permissions not configured

**Solution**:
```bash
# Install NTP service
sudo apt-get install systemd-timesyncd

# Enable the service
sudo systemctl enable systemd-timesyncd
sudo systemctl start systemd-timesyncd
```

### Time Difference Still Shows After Sync

**Solution**:
1. Click "Refresh" button to reload system time
2. If problem persists, reload the web page
3. Check if NTP is overriding your manual setting

### NTP Sync Not Working

**Check NTP Status**:
```bash
timedatectl status
```

**Expected Output**:
```
System clock synchronized: yes
NTP service: active
```

**If not synchronized**:
```bash
sudo systemctl restart systemd-timesyncd
sudo timedatectl set-ntp true
```

---

## Best Practices

### 1. **Initial Setup**
- When first setting up the Pi Zero 2W, use "Sync with PC Time"
- Then enable NTP sync for automatic time maintenance
- This ensures accurate time immediately and ongoing

### 2. **Offline Installations**
- If Pi will be offline permanently, sync with PC on each startup
- Consider adding a script to sync time on boot if possible
- Manual setting is also available but requires more precision

### 3. **Power Loss Recovery**
- After power loss, Pi Zero 2W will lose time
- Log in via dashboard and sync with PC time
- Or enable NTP and wait for automatic synchronization

### 4. **Transaction Accuracy**
- Keep system time accurate for reliable transaction timestamps
- Check time occasionally, especially after power outages
- Enable NTP for best automatic accuracy

---

## Security Considerations

### Sudo Permissions
- Only specific time-related commands have passwordless sudo
- Commands are limited to timedatectl and date with specific parameters
- No other system commands can be run through these permissions

### Audit Logging
- All time changes are logged in the application log
- Log entries include: timestamp, username, and new time value
- Check `/home/pi/accessctl/access.log` for time change audit trail

### Access Control
- Time configuration requires both API key AND active session
- Only authenticated admin users can change system time
- All actions are logged for security audit

---

## Systemd Service Configuration

If using systemd, ensure the service runs as the correct user:

```bash
sudo nano /etc/systemd/system/access-control.service
```

Verify the `User` line matches your sudoers configuration:

```ini
[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/access-control
ExecStart=/usr/bin/python3 /home/pi/access-control/app.py
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart access-control
```

---

## Testing the Feature

### Manual Test Steps

1. **Check Current System Time**:
   ```bash
   date
   ```

2. **Access Dashboard**:
   - Login to web interface
   - Go to Configuration tab
   - Scroll to Time Configuration section

3. **Test Time Sync**:
   - Note the current system time shown
   - Click "Sync with PC Time"
   - Verify system time updates to match PC time

4. **Test Manual Setting**:
   - Select a specific time (e.g., 1 hour in the future)
   - Click "Set Time"
   - Verify system time changes

5. **Verify from Terminal**:
   ```bash
   date
   ```
   Should show the time you just set

6. **Test NTP (if internet available)**:
   - Click "Enable NTP Sync"
   - Wait 10-30 seconds
   - Click "Refresh"
   - Time should sync with internet time servers

---

## Integration with Existing System

The time configuration feature integrates seamlessly with:
- **Transaction Logging**: All transactions use system time for timestamps
- **Daily Stats**: Statistics are grouped by date based on system time
- **Analytics**: Reports use system time for date ranges
- **Session Management**: Session expiry uses system time

After setting time, you may want to:
1. Reload the page to see updated timestamps
2. Check transaction logs for accurate time entries
3. Verify daily stats are using correct date

---

## Quick Reference

| Action | Button | Requires Internet | Sudo Required |
|--------|--------|------------------|---------------|
| View Time | Auto-loaded | No | No |
| Sync with PC | Blue Button | No | Yes |
| Enable NTP | Green Button | Yes | Yes |
| Manual Set | Yellow Button | No | Yes |
| Refresh | Gray Button | No | No |

---

## Notes

- Time is displayed in 24-hour format (HH:MM:SS)
- Timezone information is shown below each clock
- Both clocks update every second for real-time comparison
- Warning appears if difference exceeds 10 seconds
- All time operations are logged for audit purposes
- Changes take effect immediately but may require page reload for full synchronization

---

For additional support or questions, check the application logs:
```bash
tail -f /home/pi/accessctl/access.log
```

