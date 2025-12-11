# 🚀 Access Control System - Setup Guide

## Prerequisites

- Raspberry Pi Zero 2W with Raspbian/Raspberry Pi OS
- Python 3.7+
- 3x RFID readers (Wiegand protocol)
- 3x Relay modules
- Internet connection (optional, for Firebase sync)

---

## 📦 Installation Steps

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### 2. Clone/Copy Project Files

```bash
mkdir -p /home/pi/accessctl
cd /home/pi/accessctl
# Copy your app.py and all frontend files here
```

Your directory should look like:
```
/home/pi/accessctl/
├── app.py
├── templates/
│   ├── login.html
│   └── dashboard.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── config.js
│       └── main.js
├── .env
└── requirements.txt
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

Create `requirements.txt`:
```txt
Flask==2.3.0
python-dotenv==1.0.0
pigpio==1.78
RPi.GPIO==0.7.1
firebase-admin==6.2.0
```

Install:
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create `.env` file in `/home/pi/accessctl/`:

```bash
nano .env
```

Add this configuration:

```bash
# Base directory
BASE_DIR=/home/pi/accessctl

# Authentication - CHANGE THESE!
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
API_KEY=your-api-key-change-this

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=false

# Session
SESSION_TTL_HOURS=24
SESSION_SECRET=change-this-to-random-string

# Storage
MAX_TX_STORAGE_GB=16
CLEANUP_FRACTION=0.5

# GPIO - Relays
RELAY_1=25
RELAY_2=26
RELAY_3=27

# GPIO - RFID Readers
D0_PIN_1=18
D1_PIN_1=23
D0_PIN_2=19
D1_PIN_2=24
D0_PIN_3=20
D1_PIN_3=21

# Wiegand
WIEGAND_BITS_READER_1=26
WIEGAND_BITS_READER_2=26
WIEGAND_BITS_READER_3=26

# Logging
LOG_FILE=/home/pi/accessctl/access.log
LOG_LEVEL=INFO
```

### 6. Generate Secure Credentials

#### Change Admin Password:
```bash
python3 -c "import hashlib; password='YourNewPassword123'; print('Password Hash:', hashlib.sha256(password.encode()).hexdigest())"
```

Copy the hash and update `ADMIN_PASSWORD_HASH` in `.env`

#### Generate API Key:
```bash
python3 -c "import secrets; print('API Key:', secrets.token_hex(32))"
```

Copy the key and update `API_KEY` in `.env`

#### Generate Session Secret:
```bash
python3 -c "import secrets; print('Session Secret:', secrets.token_hex(32))"
```

Copy and update `SESSION_SECRET` in `.env`

### 7. Optional: Firebase Setup

If you want cloud sync:

1. Create Firebase project at https://console.firebase.google.com
2. Generate service account key (JSON file)
3. Save as `/home/pi/accessctl/service.json`
4. Add to `.env`:
   ```bash
   FIREBASE_CRED_FILE=service.json
   ENTITY_ID=your_entity_name
   ```

---

## 🎯 First Run

### Test the Application

```bash
cd /home/pi/accessctl
source venv/bin/activate
python app.py
```

You should see:
```
Access controller ready. Waiting for Wiegand scans…
 * Running on http://0.0.0.0:5001
```

### Access the Web Interface

1. Find your Pi's IP address:
   ```bash
   hostname -I
   ```

2. Open browser on any device on the same network:
   ```
   http://YOUR_PI_IP:5001
   ```

3. You'll be redirected to login page

4. **Configure API Key in Browser:**
   - Press `F12` to open Developer Tools
   - Go to Console tab
   - Run:
     ```javascript
     setApiKey('your-api-key-from-env-file')
     ```
   - Refresh the page

5. **Login:**
   - Username: `admin` (or what you set in `.env`)
   - Password: `admin123` (or what you used to generate hash)

---

## 🔧 Automatic Startup (systemd)

### Create Service File

```bash
sudo nano /etc/systemd/system/access-control.service
```

Add:
```ini
[Unit]
Description=RFID Access Control System
After=network.target pigpiod.service
Requires=pigpiod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/accessctl
Environment="PATH=/home/pi/accessctl/venv/bin"
ExecStart=/home/pi/accessctl/venv/bin/python /home/pi/accessctl/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable access-control
sudo systemctl start access-control
```

### Check Status

```bash
sudo systemctl status access-control
```

### View Logs

```bash
sudo journalctl -u access-control -f
```

Or application logs:
```bash
tail -f /home/pi/accessctl/access.log
```

---

## 🔌 GPIO Wiring

### Default Pin Configuration

**Relay Modules:**
- Relay 1: GPIO 25 (Pin 22)
- Relay 2: GPIO 26 (Pin 37)
- Relay 3: GPIO 27 (Pin 13)

**RFID Reader 1:**
- D0: GPIO 18 (Pin 12)
- D1: GPIO 23 (Pin 16)

**RFID Reader 2:**
- D0: GPIO 19 (Pin 35)
- D1: GPIO 24 (Pin 18)

**RFID Reader 3:**
- D0: GPIO 20 (Pin 38)
- D1: GPIO 21 (Pin 40)

### Wiring Diagram

```
RFID Reader → Pi Zero 2W
─────────────────────────
VCC         → 5V (Pin 2/4)
GND         → GND (Pin 6/9/14/20/25/30/34/39)
D0          → GPIO (see above)
D1          → GPIO (see above)
LED         → (optional, connect to 5V with resistor)
BEEP        → (optional, connect to 5V with resistor)

Relay Module → Pi Zero 2W
─────────────────────────
VCC         → 5V (Pin 2/4)
GND         → GND
IN1/IN2/IN3 → GPIO (see above)
```

---

## 📱 Using the Web Interface

### Dashboard Tab
- View system health (Internet, Firebase, RFID readers, storage)
- See today's statistics
- Monitor live transactions (auto-updates every 5 seconds)

### Transactions Tab
- View transaction history
- Search by name or card number
- Adjust record limit (50-500)
- **Download CSV** - Export transactions for analysis

### Users Tab
- View all authorized users
- **Add User** - Register new card holders
- Search users
- **Block/Unblock** - Temporarily disable access
- **Delete** - Remove users permanently

### Analytics Tab
- Search for specific user by name or card
- View user details
- See recent activity history

### Relay Control Tab
- Manual relay control for testing
- Pulse (1 second)
- Open & Hold
- Close & Hold

---

## 🧪 Testing

### Test RFID Readers

1. Go to Relay Control tab
2. Scan a card on Reader 1
3. Check logs:
   ```bash
   tail -f /home/pi/accessctl/access.log
   ```

### Test Adding User

1. Scan an RFID card (note the card number from logs)
2. Go to Users tab
3. Click "Add User"
4. Enter:
   - Name: Test User
   - Card Number: (from logs)
   - User ID: test001
5. Click "Add User"
6. Scan the card again - should grant access!

### Test Blocking

1. Find a user in Users tab
2. Click "Block"
3. Try scanning their card - should be blocked
4. Click "Unblock" to restore access

### Test CSV Export

1. Go to Transactions tab
2. Click "Download CSV"
3. File should download with all transaction data

---

## 🔒 Security Recommendations

### For Production Use:

1. **Change Default Credentials**
   ```bash
   # Generate new password hash
   python3 -c "import hashlib; print(hashlib.sha256('StrongPassword123!'.encode()).hexdigest())"
   ```

2. **Use Strong API Key**
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Enable Firewall**
   ```bash
   sudo ufw allow 5001/tcp
   sudo ufw enable
   ```

4. **Use Reverse Proxy with HTTPS**
   Install nginx:
   ```bash
   sudo apt-get install nginx certbot python3-certbot-nginx
   ```

5. **Regular Backups**
   ```bash
   # Backup user data
   cp /home/pi/accessctl/users.json /home/pi/backup/
   cp /home/pi/accessctl/blocked_users.json /home/pi/backup/
   ```

6. **Monitor Logs**
   ```bash
   # Set up log rotation
   sudo nano /etc/logrotate.d/access-control
   ```

---

## 🐛 Troubleshooting

### "pigpio daemon not running"

```bash
sudo systemctl start pigpiod
sudo systemctl enable pigpiod
```

### "GPIO errors"

```bash
# Reset GPIO
sudo pkill -9 python
gpio readall
```

### "401 Unauthorized" in browser

1. Check API key:
   ```javascript
   console.log(localStorage.getItem('apiKey'));
   ```

2. Verify it matches `.env` file

3. Update if needed:
   ```javascript
   setApiKey('correct-key-from-env')
   ```

### "Cannot connect to backend"

```bash
# Check if service is running
sudo systemctl status access-control

# Check port
sudo netstat -tulpn | grep 5001

# Check logs
tail -f /home/pi/accessctl/access.log
```

### "Transactions not updating"

1. Check browser console (F12)
2. Verify internet connection
3. Check if tab is visible (updates pause when hidden)
4. Manually refresh

### "Card reads not working"

1. Check pigpio daemon:
   ```bash
   sudo systemctl status pigpiod
   ```

2. Verify GPIO connections

3. Check log for reads:
   ```bash
   tail -f /home/pi/accessctl/access.log
   ```

4. Test with manual pulse:
   - Go to Relay Control tab
   - Click "Pulse" on any relay

---

## 📊 Storage Management

The system automatically manages storage:

- Transaction files stored in `/home/pi/accessctl/transactions/`
- Daily JSONL files (one per day)
- Auto-purge when exceeding `MAX_TX_STORAGE_GB`
- Keeps today's file when possible

### Manual Cleanup

```bash
# View transaction directory size
du -sh /home/pi/accessctl/transactions/

# List transaction files
ls -lh /home/pi/accessctl/transactions/

# Manually remove old files
rm /home/pi/accessctl/transactions/transactions_20231001.jsonl
```

---

## 📞 Support & Maintenance

### Check System Health

```bash
# Service status
sudo systemctl status access-control

# Resource usage
htop

# Disk space
df -h

# Memory
free -h

# Temperature
vcgencmd measure_temp
```

### Update System

```bash
cd /home/pi/accessctl
source venv/bin/activate

# Update Python packages
pip install --upgrade Flask python-dotenv

# Restart service
sudo systemctl restart access-control
```

### Backup & Restore

**Backup:**
```bash
tar -czf access-control-backup-$(date +%Y%m%d).tar.gz \
  /home/pi/accessctl/users.json \
  /home/pi/accessctl/blocked_users.json \
  /home/pi/accessctl/daily_stats.json \
  /home/pi/accessctl/.env
```

**Restore:**
```bash
tar -xzf access-control-backup-20231207.tar.gz -C /
sudo systemctl restart access-control
```

---

## ✅ Post-Setup Checklist

- [ ] Python dependencies installed
- [ ] `.env` file configured
- [ ] Admin password changed
- [ ] API key changed and configured in browser
- [ ] Session secret generated
- [ ] GPIO pins connected
- [ ] pigpiod running
- [ ] Can access web interface
- [ ] Can login
- [ ] Dashboard shows system status
- [ ] Can add test user
- [ ] RFID scan triggers relay
- [ ] Transactions recorded
- [ ] CSV export works
- [ ] systemd service enabled
- [ ] Auto-starts on boot
- [ ] Firewall configured (if applicable)

---

**Congratulations! Your access control system is ready! 🎉**

For detailed frontend usage, see `README_FRONTEND.md`

