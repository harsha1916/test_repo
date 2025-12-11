# 🔧 Wiegand Configuration Guide

## Overview

The Configuration tab allows you to change RFID reader settings through the web interface without editing files or restarting the system manually. All changes are authenticated and take effect immediately!

---

## 🎯 Features

### What You Can Configure:

✅ **Wiegand Bit Format** (26-bit or 34-bit) for each of 3 readers  
✅ **Scan Rate Limit** - Prevent duplicate card scans  
✅ **Wiegand Timeout** - Timing for bit detection  
✅ **Live Reinitialization** - Readers restart automatically when settings change  
✅ **Persistent Storage** - Settings saved to `config.json`  
✅ **API Authentication** - Requires both API key AND session token  

---

## 🔐 Access Requirements

The Configuration tab requires:
1. **Valid Login Session** (authenticated user)
2. **Valid API Key** (X-API-Key header)

This dual authentication ensures only authorized administrators can change critical RFID settings.

---

## 📱 How to Use

### Step 1: Access Configuration Tab

1. Login to the dashboard
2. Click **"Configuration"** in the sidebar (gear icon)
3. You'll see the RFID Reader Configuration section

### Step 2: Select Wiegand Format

For each reader (1, 2, and 3):

**26-bit (Standard):**
- Most common format
- Used by standard 125kHz proximity cards
- Format: 8-bit facility code + 16-bit card number + parity bits

**34-bit (Extended):**
- Extended format for larger installations
- Format: 16-bit facility code + 16-bit card number + parity bits
- Less common, check with card manufacturer

### Step 3: Advanced Settings (Optional)

**Scan Rate Limit:**
- Default: 60 seconds
- Range: 10-300 seconds
- Prevents the same card from being read multiple times in quick succession

**Wiegand Timeout:**
- Default: 25 milliseconds
- Range: 10-100 milliseconds
- Maximum time between individual bits before read is reset
- ⚠️ Advanced users only - incorrect values may prevent card reads

### Step 4: Save Configuration

1. Click **"Save Configuration"** button
2. System will:
   - Validate your settings
   - Save to `config.json`
   - Automatically reinitialize affected readers
   - Show success message

The readers will immediately start using the new settings!

---

## 🔍 How to Determine Your Card Format

### Method 1: Check Card Manufacturer Specs

Look at your RFID card documentation or manufacturer website. Most will specify:
- "26-bit Wiegand"
- "34-bit Wiegand"
- "H10301" (26-bit)
- "H10302" (34-bit)

### Method 2: Test Both Formats

1. Start with **26-bit** (most common)
2. Try scanning a card
3. Check the transaction logs
4. If no read detected, switch to **34-bit**
5. Try scanning again

### Method 3: Check Application Logs

When a card is scanned, check `/home/pi/accessctl/access.log`:

```bash
tail -f /home/pi/accessctl/access.log
```

Look for messages about:
- Successful reads (card detected)
- Parity errors (wrong format)
- Wiegand initialization messages

---

## 📊 Configuration File

Settings are stored in: `/home/pi/accessctl/config.json`

Example:
```json
{
  "wiegand_bits": {
    "reader_1": 26,
    "reader_2": 26,
    "reader_3": 34
  },
  "wiegand_timeout_ms": 25,
  "scan_delay_seconds": 60
}
```

### Backup Configuration

Before making changes, backup your config:

```bash
cp /home/pi/accessctl/config.json /home/pi/accessctl/config.json.backup
```

### Manual Configuration (if needed)

If the web interface is unavailable, you can edit the file directly:

```bash
nano /home/pi/accessctl/config.json
```

Then restart the service:

```bash
sudo systemctl restart access-control
```

---

## ⚡ Live Reinitialization

When you change Wiegand settings:

1. **Backend validates** - Ensures bits are 26 or 34
2. **Saves config** - Writes to `config.json`
3. **Cancels old decoders** - Stops current Wiegand readers
4. **Reinitializes readers** - Creates new decoders with updated settings
5. **Logs change** - Records in application log

**No service restart required!** The system continues running with new settings.

### What Gets Reinitialized:

- ✅ Wiegand bit format changes → Readers restart
- ✅ Timeout changes → Readers restart
- ❌ Scan delay changes → Only rate limiter updates (no restart)

---

## 🚨 Troubleshooting

### Cards Not Reading After Configuration Change

**Problem:** Changed format but cards still don't work

**Solutions:**
1. Try the other format (26 ↔ 34)
2. Check application logs for errors
3. Verify GPIO connections
4. Test with "Reset to Current" button
5. Manually restart service if needed

### "Configuration saved but reader reinit failed"

**Problem:** Settings saved but readers didn't restart

**Possible Causes:**
- pigpio daemon not running
- GPIO already in use
- Hardware connection issue

**Solution:**
```bash
# Check pigpio daemon
sudo systemctl status pigpiod

# Restart access control service
sudo systemctl restart access-control

# Check logs
tail -f /home/pi/accessctl/access.log
```

### Can't Access Configuration Tab

**Problem:** 401 Unauthorized error

**Solution:**
1. Ensure you're logged in
2. Verify API key is configured
3. Check browser console for errors
4. Try logging out and back in

### Changes Don't Persist After Reboot

**Problem:** Config reverts to defaults

**Solution:**
1. Check file permissions:
   ```bash
   ls -la /home/pi/accessctl/config.json
   ```
2. Ensure file exists and is writable
3. Check for errors in system log

---

## 📚 Common Scenarios

### Scenario 1: Mixed Card Types

**Situation:** You have some 26-bit and some 34-bit cards

**Solution:**
- Most systems use **one format** for all cards
- If you truly have mixed formats, you'll need separate readers
- Configure Reader 1 for 26-bit, Reader 2 for 34-bit
- Users must use correct reader for their card type

### Scenario 2: Upgrading Card System

**Situation:** Transitioning from 26-bit to 34-bit cards

**Solution:**
1. Keep Reader 1 at 26-bit for old cards
2. Set Reader 2 to 34-bit for new cards
3. Gradually transition users
4. Once all users migrated, reconfigure all readers to 34-bit

### Scenario 3: Testing New Readers

**Situation:** Adding new RFID reader hardware

**Solution:**
1. Connect reader to appropriate GPIO pins
2. Go to Configuration tab
3. Set expected bit format
4. Test with known card
5. Check logs for successful reads
6. Adjust format if needed

---

## 🔒 Security Notes

### Who Can Change Configuration?

Configuration changes require **TWO levels of authentication**:

1. **Session Token** - Must be logged in as admin
2. **API Key** - Must match the key in `.env` file

This prevents unauthorized changes even if someone has only one credential.

### Audit Trail

All configuration changes are logged to `/home/pi/accessctl/access.log`:

```
2025-10-07 14:32:15 INFO Wiegand readers reinitialized: R1=26bit, R2=26bit, R3=34bit
2025-10-07 14:32:15 INFO Configuration updated and readers reinitialized
```

Review logs periodically to track changes.

---

## 💡 Best Practices

### ✅ DO:

1. **Test changes during low-traffic periods** - Avoid peak access times
2. **Document your settings** - Keep notes on which format works
3. **Backup config file** - Before making changes
4. **Test immediately** - Scan a card right after changing settings
5. **Check logs** - Verify readers reinitialized successfully

### ❌ DON'T:

1. **Change randomly** - Know what your cards require first
2. **Modify timeout unless necessary** - Default (25ms) works for most
3. **Set scan delay too low** - Can cause duplicate transaction records
4. **Skip testing** - Always verify cards still work after changes

---

## 📞 Support

### Configuration Not Working?

1. **Check Application Log:**
   ```bash
   tail -n 50 /home/pi/accessctl/access.log
   ```

2. **Verify pigpio Running:**
   ```bash
   sudo systemctl status pigpiod
   ```

3. **Test Reader Manually:**
   - Go to Relay Control tab
   - Click "Pulse" on a relay
   - Confirms GPIO is working

4. **Reset to Defaults:**
   - Delete config file:
     ```bash
     rm /home/pi/accessctl/config.json
     ```
   - Restart service - will recreate with defaults from `.env`

---

## 🎓 Understanding Wiegand Formats

### What is Wiegand?

Wiegand is a communication protocol for RFID readers:
- Uses 2 wires (D0 and D1) plus power and ground
- Sends binary data as pulse trains
- Reader pulls D0 low for '0' bit, D1 low for '1' bit
- Cards transmit data in 26 or 34 pulses (bits)

### 26-bit Format Structure:

```
[P][FFFFFFFF][NNNNNNNNNNNNNNNN][P]
 1    8 bits      16 bits        1

P = Parity bit (error checking)
F = Facility code (building/site ID)
N = Card number (unique ID within facility)
```

### 34-bit Format Structure:

```
[P][FFFFFFFFFFFFFFFF][NNNNNNNNNNNNNNNN][P]
 1      16 bits            16 bits        1

P = Parity bit
F = Facility code (larger range)
N = Card number
```

### Why Parity Matters:

Parity bits verify data integrity. The system checks:
- **Even parity** on first half of data bits
- **Odd parity** on second half of data bits

If parity check fails, the read is rejected (logged as "Wiegand parity failed").

---

## ✅ Configuration Checklist

Before deploying to production:

- [ ] Identified correct Wiegand format for your cards
- [ ] Tested configuration with known cards
- [ ] Verified all 3 readers work correctly
- [ ] Documented which readers use which format
- [ ] Backed up `config.json` file
- [ ] Set appropriate scan delay for your use case
- [ ] Tested card reads after configuration
- [ ] Checked application logs for errors
- [ ] Verified users can access doors
- [ ] Updated system documentation

---

## 📖 Related Documentation

- **SETUP_GUIDE.md** - Initial system setup
- **README_FRONTEND.md** - Frontend features
- **QUICK_START.md** - Getting started guide
- **app.py** - Backend implementation details

---

**Configuration made easy!** 🎉

No more editing files manually or restarting services. Change your RFID reader settings with confidence through the secure web interface!

