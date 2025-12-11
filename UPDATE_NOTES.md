# 🆕 Configuration Feature - Update Notes

## What's New

A new **Configuration tab** has been added to the web dashboard, allowing you to configure Wiegand RFID reader settings through the web interface with proper API authentication.

---

## 🎯 New Features

### Configuration Tab

Located in the sidebar with a gear icon, this tab provides:

1. **Wiegand Bit Format Selection**
   - Choose 26-bit or 34-bit for each of 3 readers
   - Dropdowns with clear labels (Standard/Extended)
   - Shows current configuration for each reader

2. **Advanced Settings**
   - Scan Rate Limit (10-300 seconds)
   - Wiegand Timeout (10-100 milliseconds)

3. **Real-time Updates**
   - Changes take effect immediately
   - Readers automatically reinitialize
   - No service restart required

4. **Information & Guidance**
   - Warning about correct settings
   - Help text explaining 26-bit vs 34-bit
   - Visual feedback for current settings

### Backend Enhancements

**New API Endpoints:**
- `GET /get_config` - Retrieve current configuration (requires auth)
- `POST /update_config` - Update configuration (requires both API key + session)

**New Features:**
- Configuration stored in `config.json`
- Thread-safe config management
- Automatic Wiegand decoder reinitialization
- Validation of bit format values
- Detailed logging of configuration changes

**Files Modified:**
- `app.py` - Added config management, API endpoints, auto-reinitialization
- `templates/dashboard.html` - Added Configuration tab UI
- `static/css/style.css` - Added configuration styling
- `static/js/main.js` - Added config management functions

**New Files:**
- `CONFIGURATION_GUIDE.md` - Complete configuration documentation
- `UPDATE_NOTES.md` - This file

---

## 🔄 Changes from Previous Version

### What Changed:

**Previously:**
- Wiegand bit format only configurable in `.env` file
- Required editing files and restarting service
- No validation of settings
- No web interface for configuration

**Now:**
- Configure through secure web interface
- Real-time validation
- Immediate effect (auto-reinitialize readers)
- Persistent storage in `config.json`
- Proper authentication required

### Backward Compatibility:

✅ **Fully backward compatible!**

- If `config.json` doesn't exist, uses `.env` defaults
- Existing `.env` settings become initial configuration
- Old systems work without changes
- Configuration can still be edited manually if needed

### Migration:

**No migration needed!** The system will:
1. Read initial values from `.env` on first run
2. Create `config.json` with those values
3. Use `config.json` for subsequent runs
4. Fall back to `.env` if `config.json` is deleted

---

## 🔐 Security

The Configuration tab uses **defense-in-depth** security:

### Authentication Required:

1. **Session Token** - User must be logged in
2. **API Key** - Request must include valid X-API-Key header

This is the **highest security level** in the system, used only for:
- Adding/deleting users
- Blocking/unblocking users
- **Changing configuration** ← NEW
- Manual relay control

### Why Both?

Configuration changes can affect system operation. Requiring both credentials ensures that even if someone obtains one credential, they cannot modify critical settings without the other.

---

## 📝 Configuration File

### Location:
```
/home/pi/accessctl/config.json
```

### Format:
```json
{
  "wiegand_bits": {
    "reader_1": 26,
    "reader_2": 26,
    "reader_3": 26
  },
  "wiegand_timeout_ms": 25,
  "scan_delay_seconds": 60
}
```

### Defaults:

Values come from `.env` file:
```bash
WIEGAND_BITS_READER_1=26
WIEGAND_BITS_READER_2=26
WIEGAND_BITS_READER_3=26
WIEGAND_TIMEOUT_MS=25
SCAN_DELAY_SECONDS=60
```

---

## 🚀 How to Use

### For New Installations:

1. Install system normally (follow SETUP_GUIDE.md)
2. Login to dashboard
3. Click "Configuration" tab
4. Set appropriate Wiegand format for your cards
5. Click "Save Configuration"
6. Test card reads

### For Existing Installations:

1. Update files (copy new templates, static files, app.py)
2. Restart service: `sudo systemctl restart access-control`
3. Login to dashboard
4. New "Configuration" tab will appear
5. Current settings will be loaded from `.env`
6. Make changes as needed

---

## 🔧 Technical Details

### How Reinitialization Works:

When you click "Save Configuration":

1. **Frontend** sends POST to `/update_config` with new settings
2. **Backend validates** bit values (must be 26 or 34)
3. **Backend saves** to `config.json`
4. **Backend checks** if Wiegand settings changed
5. If changed:
   - Cancel old WiegandDecoder instances
   - Wait 100ms
   - Create new WiegandDecoder instances with new bits
   - Log reinitialization
6. **Backend responds** with success message
7. **Frontend updates** display and shows notification

### Thread Safety:

Configuration management uses a dedicated lock (`CONFIG_LOCK`) to ensure:
- No race conditions when reading/writing config
- Safe concurrent access from multiple requests
- Atomic updates to configuration file

### Error Handling:

If reinitialization fails:
- Configuration is still saved (persistent)
- User receives warning message
- Service continues running
- Manual restart can be performed if needed

---

## 📊 API Reference

### GET /get_config

**Authentication:** Session token required

**Request:**
```bash
curl -H "Authorization: Bearer <token>" \
     -H "X-API-Key: <key>" \
     http://localhost:5001/get_config
```

**Response:**
```json
{
  "status": "success",
  "config": {
    "wiegand_bits": {
      "reader_1": 26,
      "reader_2": 26,
      "reader_3": 26
    },
    "wiegand_timeout_ms": 25,
    "scan_delay_seconds": 60
  }
}
```

### POST /update_config

**Authentication:** Session token + API key required (both)

**Request:**
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "X-API-Key: <key>" \
     -H "Content-Type: application/json" \
     -d '{"config": {"wiegand_bits": {"reader_1": 34, "reader_2": 26, "reader_3": 26}, "wiegand_timeout_ms": 25, "scan_delay_seconds": 60}}' \
     http://localhost:5001/update_config
```

**Response (Success):**
```json
{
  "status": "success",
  "message": "Configuration updated and readers reinitialized"
}
```

**Response (Validation Error):**
```json
{
  "status": "error",
  "message": "Invalid bits for reader_1. Must be 26 or 34."
}
```

**Response (Reinit Warning):**
```json
{
  "status": "warning",
  "message": "Config saved but reader reinit failed: <error details>"
}
```

---

## 🧪 Testing

### Test Configuration Changes:

1. **Access Configuration Tab**
   - Login to dashboard
   - Click Configuration in sidebar
   - Verify current settings display correctly

2. **Change Single Reader**
   - Change Reader 1 from 26 to 34-bit
   - Click "Save Configuration"
   - Verify success message
   - Check current value updates to 34

3. **Test Card Read**
   - Scan a known card on Reader 1
   - Check transactions tab
   - Verify card is read (or denied if format wrong)

4. **Change Multiple Readers**
   - Change all 3 readers to different formats
   - Save configuration
   - Check logs for reinitialization message

5. **Test Advanced Settings**
   - Change scan delay to 30 seconds
   - Save configuration
   - Scan same card twice quickly
   - Verify second scan is ignored (rate limited)

6. **Test Reset Button**
   - Change settings but don't save
   - Click "Reset to Current"
   - Verify dropdowns revert to saved values

### Check Logs:

```bash
tail -f /home/pi/accessctl/access.log
```

Look for:
```
INFO Wiegand readers initialized: R1=26bit, R2=26bit, R3=26bit
INFO Wiegand readers reinitialized: R1=34bit, R2=26bit, R3=26bit
INFO Configuration updated and readers reinitialized
```

---

## ❓ FAQ

### Q: Do I need to restart the service after changing configuration?

**A:** No! The system automatically reinitializes the readers when settings change. No restart needed.

### Q: What happens if I choose the wrong bit format?

**A:** Cards won't be read. Check the logs for "Wiegand parity failed" messages. Switch to the other format and try again.

### Q: Can I still use .env file for configuration?

**A:** Yes! The `.env` file provides default values. Once you save configuration through the web interface, those values override the `.env` defaults.

### Q: What if config.json gets corrupted?

**A:** Delete it and restart the service. It will recreate with values from `.env` file.

### Q: Is there a way to reset to factory defaults?

**A:** Yes, delete `config.json` and restart the service:
```bash
rm /home/pi/accessctl/config.json
sudo systemctl restart access-control
```

### Q: Can I configure each reader to use different formats?

**A:** Yes! Each reader can independently be set to 26-bit or 34-bit. This is useful during card system transitions.

---

## 🎉 Benefits

### Before this update:
1. Edit `.env` file manually
2. Restart access-control service
3. Wait for service to come back up
4. Hope you didn't make a typo
5. Check logs to verify

### With this update:
1. Click Configuration tab
2. Select format from dropdown
3. Click Save
4. Done! ✅

**Faster, safer, easier!**

---

## 📚 Documentation

For complete information, see:
- **CONFIGURATION_GUIDE.md** - Detailed configuration guide
- **README_FRONTEND.md** - Updated with Configuration tab info
- **QUICK_START.md** - Quick reference
- **SETUP_GUIDE.md** - Installation guide

---

## 🔮 Future Enhancements

Possible future additions to Configuration tab:
- GPIO pin assignment
- Relay pulse duration
- Firebase settings
- Email/SMS notifications
- Backup/restore configuration
- Import/export settings

---

**Version:** 1.1  
**Added:** October 2025  
**Status:** Production Ready ✅

