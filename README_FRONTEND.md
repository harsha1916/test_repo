# Access Control System - Frontend Documentation

## 🚀 Quick Start

### 1. Setup API Key

The frontend needs to communicate with the Flask backend using your API key. Before accessing the dashboard, you need to configure it:

**Method 1: Browser Console (Recommended)**
1. Open the login page in your browser
2. Press `F12` to open Developer Tools
3. Go to the Console tab
4. Run this command (replace with your actual API key from `.env`):
   ```javascript
   setApiKey('your-api-key-change-this')
   ```
5. Refresh the page

**Method 2: Manually in localStorage**
```javascript
localStorage.setItem('apiKey', 'your-api-key-change-this');
```

### 2. Login

- **Default credentials:**
  - Username: `admin`
  - Password: `admin123`

⚠️ **Important:** Change these defaults in your `.env` file for production!

---

## 📱 Features

### Dashboard Tab
- **Real-time System Health Monitoring:**
  - Internet connectivity status
  - Firebase connection status
  - RFID readers status
  - Storage usage
  
- **Today's Statistics:**
  - Total scans
  - Access granted count
  - Access denied count
  - Blocked attempts

- **Live Transactions:**
  - Auto-updates every 5 seconds
  - Shows last 10 transactions
  - Real-time status indicators

### Transactions Tab
- View complete transaction history
- Search by name or card number
- Adjustable record limit (50-500)
- **CSV Export:** Download transactions for external analysis

### Users Tab
- View all registered users
- Search functionality
- Add new users
- Block/Unblock users
- Delete users
- Status indicators (Active/Blocked)

### Analytics Tab
- Search for specific users by name or card number
- View detailed user information
- Recent activity history (last 50 transactions)
- User-specific statistics

### Relay Control Tab
- Manual relay control
- Three relay outputs:
  - Pulse (1 second)
  - Open & Hold
  - Close & Hold

---

## 🔧 Configuration

### Environment Variables (`.env`)

Make sure these are set in your `.env` file:

```bash
# Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<sha256-hash-of-password>
API_KEY=your-api-key-change-this  # Match this in browser!

# Flask Settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
```

### Generate Password Hash

To change the admin password:

```python
import hashlib
password = "your-new-password"
hash_value = hashlib.sha256(password.encode()).hexdigest()
print(hash_value)
```

Add the hash to your `.env` file as `ADMIN_PASSWORD_HASH`.

---

## 🖥️ Raspberry Pi Zero 2W Optimization

The frontend is optimized for low-resource environments:

### Performance Features:
- **Lightweight CSS:** No heavy frameworks, pure CSS
- **Vanilla JavaScript:** No jQuery or large libraries
- **Efficient polling:** Smart intervals (5s for transactions, 30s for system status)
- **Debounced searches:** Reduces API calls
- **Lazy loading:** Only active tab data is refreshed
- **Visibility API:** Pauses updates when browser tab is hidden

### Resource Usage:
- HTML: ~15KB
- CSS: ~12KB
- JavaScript: ~15KB
- **Total:** <50KB (uncompressed)

---

## 🔒 Authentication Flow

1. User enters credentials on login page
2. Backend validates and returns session token
3. Token stored in `localStorage`
4. All API requests include:
   - `Authorization: Bearer <token>` header
   - `X-API-Key: <api-key>` header
5. 401 errors automatically redirect to login

**Session Duration:** 24 hours (configurable via `SESSION_TTL_HOURS`)

---

## 📊 API Endpoints Used

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/login` | POST | None | User authentication |
| `/logout` | POST | Session | End session |
| `/status` | GET | None | System status |
| `/get_users` | GET | Session | List all users |
| `/add_user` | POST | Both | Add new user |
| `/delete_user` | POST | Both | Remove user |
| `/block_user` | POST | Both | Block user |
| `/unblock_user` | POST | Both | Unblock user |
| `/get_transactions` | GET | Session | Get transactions |
| `/download_transactions_csv` | GET | Session | Export CSV |
| `/get_today_stats` | GET | Session | Today's stats |
| `/relay` | POST | Both | Control relays |
| `/dashboard` | GET | None | Dashboard page |

**Auth Types:**
- **Session:** Requires valid session token
- **Both:** Requires both session token AND API key

---

## 🐛 Troubleshooting

### 401 Unauthorized Errors

**Cause:** API key mismatch or expired session

**Solution:**
1. Check console for API key warnings
2. Verify API key matches `.env` file:
   ```javascript
   console.log(localStorage.getItem('apiKey'));
   ```
3. Update if needed:
   ```javascript
   setApiKey('correct-api-key-from-env-file')
   ```
4. Clear session and re-login if needed:
   ```javascript
   localStorage.clear();
   ```

### Page Not Loading

**Check:**
1. Flask server is running: `ps aux | grep app.py`
2. Port 5001 is accessible
3. Browser console for errors (F12)
4. Network tab shows successful requests

### Live Updates Not Working

**Check:**
1. Browser tab is visible (updates pause when hidden)
2. Network connectivity
3. Console for API errors
4. Try manual refresh

### CSV Download Not Working

**Check:**
1. Pop-up blocker is disabled
2. Browser allows file downloads
3. Sufficient disk space
4. Console for errors

---

## 📱 Mobile/Responsive Design

The UI is responsive and works on mobile devices:

- **Desktop:** Full sidebar with labels
- **Tablet:** Compact sidebar (200px)
- **Mobile:** Icon-only sidebar (60px)

All tables are horizontally scrollable on small screens.

---

## 🔐 Security Notes

1. **Always use HTTPS in production** - Deploy behind nginx/Apache with SSL
2. **Change default credentials immediately**
3. **Use strong API keys** (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
4. **Restrict access** by IP if possible
5. **Regular backups** of `users.json` and `blocked_users.json`
6. **Monitor logs** in `access.log`

---

## 🎨 Customization

### Change Colors

Edit `static/css/style.css`:

```css
:root {
    --primary: #2196F3;  /* Main brand color */
    --success: #4CAF50;  /* Success/granted */
    --warning: #FF9800;  /* Warnings/blocked */
    --danger: #f44336;   /* Errors/denied */
}
```

### Modify Relay Names

Edit `templates/dashboard.html`, search for "Relay 1", "Relay 2", "Relay 3" and change the descriptions.

### Adjust Update Intervals

Edit `static/js/main.js`:

```javascript
// In initDashboard() function:
updateIntervals.push(setInterval(loadLiveTransactions, 5000));  // 5 seconds
updateIntervals.push(setInterval(loadTodayStats, 10000));       // 10 seconds
updateIntervals.push(setInterval(loadSystemStatus, 30000));     // 30 seconds
```

---

## 📦 File Structure

```
pi_zero_access/
├── app.py                      # Flask backend
├── templates/
│   ├── login.html             # Login page
│   └── dashboard.html         # Main dashboard
├── static/
│   ├── css/
│   │   └── style.css          # All styles
│   └── js/
│       ├── config.js          # API key helper
│       └── main.js            # Main application logic
├── .env                        # Configuration
└── README_FRONTEND.md         # This file
```

---

## 🚀 Deployment on Raspberry Pi

### Auto-start with systemd

Create `/etc/systemd/system/access-control.service`:

```ini
[Unit]
Description=Access Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/accessctl
Environment="PATH=/home/pi/accessctl/venv/bin"
ExecStart=/home/pi/accessctl/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable access-control
sudo systemctl start access-control
```

### Access from other devices

Find your Pi's IP address:
```bash
hostname -I
```

Access from any device on your network:
```
http://<pi-ip-address>:5001
```

---

## 📞 Support

For issues or questions:
1. Check console for errors (F12)
2. Check Flask logs: `tail -f /home/pi/accessctl/access.log`
3. Verify API key configuration
4. Test backend directly: `curl http://localhost:5001/status`

---

## ✅ Quick Test Checklist

After setup, verify:

- [ ] Login page loads
- [ ] Can log in with credentials
- [ ] Dashboard shows system status
- [ ] Live transactions update
- [ ] Can view all users
- [ ] Can add a test user
- [ ] Can search transactions
- [ ] CSV export works
- [ ] User analytics works
- [ ] Relay controls respond
- [ ] No 401 errors in console

---

**Version:** 1.0  
**Last Updated:** October 2025  
**Compatible with:** Raspberry Pi Zero 2W, Flask 2.x+

