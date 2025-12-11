#!/usr/bin/env python3
# Pi Zero 2 W: lightweight, no image capture; local transaction storage + auto-purge
import os, sys, time, json, hashlib, secrets, threading, logging, signal, base64
from datetime import datetime, timedelta
from functools import wraps
from queue import Queue
from collections import deque  # CHANGED: for thread-safe recent buffer pattern

import pigpio
import RPi.GPIO as GPIO
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv

# Optional Firebase
db = None
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1 import SERVER_TIMESTAMP
    FROM_FIREBASE = True
except Exception:
    FROM_FIREBASE = False

# =========================
# Env & constants
# =========================
load_dotenv()
BASE_DIR   = os.environ.get('BASE_DIR', '/home/maxpark')
os.makedirs(BASE_DIR, exist_ok=True)

# File paths
USER_DATA_FILE         = os.path.join(BASE_DIR, "users.json")
BLOCKED_USERS_FILE     = os.path.join(BASE_DIR, "blocked_users.json")
DAILY_STATS_FILE       = os.path.join(BASE_DIR, "daily_stats.json")
CONFIG_FILE            = os.path.join(BASE_DIR, "config.json")
FAILED_TX_CACHE_FILE   = os.path.join(BASE_DIR, "failed_transactions_cache.jsonl")

# NEW: transaction directory (daily JSONL files)
TX_DIR                 = os.path.join(BASE_DIR, "transactions")
os.makedirs(TX_DIR, exist_ok=True)

# Storage controls (for TX_DIR only)
MAX_TX_STORAGE_GB          = float(os.environ.get("MAX_TX_STORAGE_GB", "16"))  # cap, e.g., 16 GB
CLEANUP_FRACTION           = float(os.environ.get("CLEANUP_FRACTION", "0.5"))  # how much to free when cap exceeded
TX_STORAGE_CHECK_INTERVAL  = int(os.environ.get("TX_STORAGE_CHECK_INTERVAL", "300"))  # seconds

FIREBASE_CRED_FILE = os.environ.get('FIREBASE_CRED_FILE', "service.json")
ENTITY_ID          = os.environ.get('ENTITY_ID', 'default_entity')

LOG_FILE  = os.environ.get('LOG_FILE', os.path.join(BASE_DIR, 'access.log'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(filename=LOG_FILE, level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s %(levelname)s %(message)s")

# Auth config
ADMIN_USERNAME      = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH',
                                     hashlib.sha256('admin123'.encode()).hexdigest())  # NOTE: unchanged per request
API_KEY             = os.environ.get('API_KEY', 'your-api-key-change-this')
SESSION_TTL_HOURS   = int(os.environ.get('SESSION_TTL_HOURS', '24'))

# Rate-limit same card scans
SCAN_DELAY_SECONDS  = int(os.environ.get("SCAN_DELAY_SECONDS", "60"))

# GPIO Pins
RELAY_1 = int(os.environ.get('RELAY_1', 25))
RELAY_2 = int(os.environ.get('RELAY_2', 26))
RELAY_3 = int(os.environ.get('RELAY_3', 27))

D0_PIN_1 = int(os.environ.get('D0_PIN_1', 18))
D1_PIN_1 = int(os.environ.get('D1_PIN_1', 23))
D0_PIN_2 = int(os.environ.get('D0_PIN_2', 19))
D1_PIN_2 = int(os.environ.get('D1_PIN_2', 24))
D0_PIN_3 = int(os.environ.get('D0_PIN_3', 20))
D1_PIN_3 = int(os.environ.get('D1_PIN_3', 21))

# =========================
# Helpers
# =========================
def atomic_write_json(path, data):
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def read_json_or_default(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

# NOTE: password hashing left as-is per your request
def hash_password(password:str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed) -> bool:
    return hash_password(password) == hashed

def is_internet():
    import urllib.request
    try:
        urllib.request.urlopen("http://clients3.google.com/generate_204", timeout=3)
        return True
    except Exception:
        return False

def get_cpu_temperature():
    """Read CPU temperature from Raspberry Pi thermal zone."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read().strip()) / 1000.0  # Convert millidegrees to degrees
            return round(temp, 1)
    except Exception as e:
        logging.error(f"Failed to read CPU temperature: {e}")
        return None

# =========================
# Data stores (thread-safe)
# =========================
USERS_LOCK = threading.RLock()
BLOCKED_LOCK = threading.RLock()
ALLOWED_SET_LOCK = threading.RLock()
BLOCKED_SET_LOCK = threading.RLock()
CONFIG_LOCK = threading.RLock()

users = read_json_or_default(USER_DATA_FILE, {})
blocked_users = read_json_or_default(BLOCKED_USERS_FILE, {})
ALLOWED_SET = set()
BLOCKED_SET = set()

def _card_str_to_int(s):
    try: return int(s)
    except: return None

def _rebuild_allowed():
    global ALLOWED_SET
    with ALLOWED_SET_LOCK:
        ALLOWED_SET = set()
        for k in users.keys():
            ci = _card_str_to_int(k)
            if ci is not None:
                ALLOWED_SET.add(ci)

def _rebuild_blocked():
    global BLOCKED_SET
    with BLOCKED_SET_LOCK:
        BLOCKED_SET = set()
        for k, v in blocked_users.items():
            if v:
                ci = _card_str_to_int(k)
                if ci is not None:
                    BLOCKED_SET.add(ci)

def load_local_users():
    global users
    with USERS_LOCK:
        users = read_json_or_default(USER_DATA_FILE, {})
        _rebuild_allowed()
        return dict(users)

def save_local_users(new_users):
    global users
    with USERS_LOCK:
        users = dict(new_users)
        atomic_write_json(USER_DATA_FILE, users)
        _rebuild_allowed()

def load_blocked_users():
    global blocked_users
    with BLOCKED_LOCK:
        blocked_users = read_json_or_default(BLOCKED_USERS_FILE, {})
        _rebuild_blocked()
        return dict(blocked_users)

def save_blocked_users(new_blocked):
    global blocked_users
    with BLOCKED_LOCK:
        blocked_users = dict(new_blocked)
        atomic_write_json(BLOCKED_USERS_FILE, blocked_users)
        _rebuild_blocked()

# =========================
# Configuration management
# =========================
def get_config():
    """Load configuration from file with defaults."""
    with CONFIG_LOCK:
        default_config = {
            "wiegand_bits": {
                "reader_1": int(os.environ.get('WIEGAND_BITS_READER_1', '26')),
                "reader_2": int(os.environ.get('WIEGAND_BITS_READER_2', '26')),
                "reader_3": int(os.environ.get('WIEGAND_BITS_READER_3', '26'))
            },
            "wiegand_timeout_ms": int(os.environ.get('WIEGAND_TIMEOUT_MS', '25')),
            "scan_delay_seconds": int(os.environ.get('SCAN_DELAY_SECONDS', '60')),
            "entry_exit_tracking": {
                "enabled": False,
                "min_gap_seconds": 300  # 5 minutes default
            },
            "entity_id": os.environ.get('ENTITY_ID', 'default_entity')
        }
        config = read_json_or_default(CONFIG_FILE, default_config)
        # Ensure all keys exist
        if "wiegand_bits" not in config:
            config["wiegand_bits"] = default_config["wiegand_bits"]
        if "wiegand_timeout_ms" not in config:
            config["wiegand_timeout_ms"] = default_config["wiegand_timeout_ms"]
        if "scan_delay_seconds" not in config:
            config["scan_delay_seconds"] = default_config["scan_delay_seconds"]
        if "entry_exit_tracking" not in config:
            config["entry_exit_tracking"] = default_config["entry_exit_tracking"]
        if "entity_id" not in config:
            config["entity_id"] = default_config["entity_id"]
        return config

def save_config(new_config):
    """Save configuration to file."""
    with CONFIG_LOCK:
        atomic_write_json(CONFIG_FILE, new_config)

# =========================
# Transaction local storage (daily JSONL) + purge
# =========================
def _tx_file_for_day(dt=None):
    dt = dt or datetime.now()
    return os.path.join(TX_DIR, f"transactions_{dt.strftime('%Y%m%d')}.jsonl")

def append_local_transaction(tx: dict):
    """Append a single JSON line to today's transaction file."""
    path = _tx_file_for_day()
    line = json.dumps(tx, separators=(",", ":"))  # compact
    with open(path, "a") as f:
        f.write(line + "\n")

# =========================
# Failed Transaction Cache (persistent storage)
# =========================
FAILED_TX_LOCK = threading.RLock()

def append_failed_transaction(tx: dict):
    """Append a failed transaction to persistent cache file."""
    try:
        with FAILED_TX_LOCK:
            line = json.dumps(tx, separators=(",", ":"))
            with open(FAILED_TX_CACHE_FILE, "a") as f:
                f.write(line + "\n")
        logging.info(f"Added to failed transaction cache: {tx.get('card')} - {tx.get('status')}")
    except Exception as e:
        logging.error(f"Failed to write to cache file: {e}")

def load_failed_transactions():
    """Load all failed transactions from cache file."""
    failed_txs = []
    try:
        with FAILED_TX_LOCK:
            if os.path.exists(FAILED_TX_CACHE_FILE):
                with open(FAILED_TX_CACHE_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                failed_txs.append(json.loads(line))
                            except json.JSONDecodeError as e:
                                logging.error(f"Invalid JSON in cache file: {e}")
                logging.info(f"Loaded {len(failed_txs)} failed transactions from cache")
    except Exception as e:
        logging.error(f"Failed to load cache file: {e}")
    return failed_txs

def clear_failed_transactions_cache():
    """Clear the failed transactions cache file (after successful upload)."""
    try:
        with FAILED_TX_LOCK:
            if os.path.exists(FAILED_TX_CACHE_FILE):
                os.remove(FAILED_TX_CACHE_FILE)
                logging.info("Cleared failed transactions cache")
    except Exception as e:
        logging.error(f"Failed to clear cache file: {e}")

def update_failed_transactions_cache(remaining_txs):
    """Update cache file with remaining failed transactions."""
    try:
        with FAILED_TX_LOCK:
            # Write remaining transactions to a temp file
            temp_file = f"{FAILED_TX_CACHE_FILE}.tmp"
            with open(temp_file, "w") as f:
                for tx in remaining_txs:
                    line = json.dumps(tx, separators=(",", ":"))
                    f.write(line + "\n")
            # Replace original file
            os.replace(temp_file, FAILED_TX_CACHE_FILE)
            logging.info(f"Updated failed transactions cache: {len(remaining_txs)} remaining")
    except Exception as e:
        logging.error(f"Failed to update cache file: {e}")

def get_tx_dir_size_bytes() -> int:
    total = 0
    try:
        for name in os.listdir(TX_DIR):
            fp = os.path.join(TX_DIR, name)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    except Exception as e:
        logging.error(f"TX size error: {e}")
    return total

def purge_old_transactions(max_bytes: int, free_target_bytes: int):
    """
    Delete oldest files in TX_DIR until we have freed at least free_target_bytes.
    Keeps today's file if possible.
    """
    try:
        files = []
        today_name = os.path.basename(_tx_file_for_day())
        for name in os.listdir(TX_DIR):
            if not name.endswith(".jsonl"):
                continue
            fp = os.path.join(TX_DIR, name)
            if not os.path.isfile(fp):
                continue
            mtime = os.path.getmtime(fp)
            size = os.path.getsize(fp)
            files.append((mtime, size, fp, name))

        # Oldest first
        files.sort(key=lambda x: x[0])

        freed = 0
        for _, size, fp, name in files:
            # Try not to delete today's active file unless necessary
            if name == today_name and freed < free_target_bytes:
                continue
            try:
                os.remove(fp)
                freed += size
                logging.info(f"Purged TX file: {name} ({size/1024/1024:.2f} MB)")
                if freed >= free_target_bytes:
                    break
            except Exception as e:
                logging.error(f"Purge error removing {name}: {e}")

        logging.info(f"TX purge completed. Freed ~{freed/1024/1024:.2f} MB")
    except Exception as e:
        logging.error(f"TX purge failure: {e}")

def tx_storage_monitor_worker():
    """Background worker that enforces MAX_TX_STORAGE_GB for TX_DIR."""
    max_bytes = int(MAX_TX_STORAGE_GB * 1024 * 1024 * 1024)
    interval = max(60, TX_STORAGE_CHECK_INTERVAL)  # at least once/min
    while True:
        try:
            while True:
                total = get_tx_dir_size_bytes()
                if total <= max_bytes:
                    break
                free_target_bytes = min(total - max_bytes, int(max_bytes * CLEANUP_FRACTION))
                logging.warning(
                    f"TX storage exceeded cap ({total/1024/1024/1024:.2f} GB > {MAX_TX_STORAGE_GB:.2f} GB). "
                    f"Purging oldest ~{free_target_bytes/1024/1024/1024:.2f} GB…"
                )
                purge_old_transactions(max_bytes, free_target_bytes)
        except Exception as e:
            logging.error(f"TX storage monitor error: {e}")
        time.sleep(interval)

# =========================
# Optional Firebase Sync (reads from local JSONL not required; we push live)
# =========================
if FROM_FIREBASE and os.path.exists(FIREBASE_CRED_FILE):
    try:
        cred = credentials.Certificate(FIREBASE_CRED_FILE)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        logging.info("Firebase initialized")
    except Exception as e:
        logging.error(f"Firebase init failed: {e}")
        db = None
else:
    db = None
    logging.info("Firebase disabled (no creds or library missing)")

# =========================
# Simple stats
# =========================
def update_daily_stats(status):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        stats = read_json_or_default(DAILY_STATS_FILE, {})
        if today not in stats:
            stats[today] = {"date":today,"valid_entries":0,"invalid_entries":0,"blocked_entries":0}
        if status == "Access Granted":
            stats[today]['valid_entries'] += 1
        elif status == "Access Denied":
            stats[today]['invalid_entries'] += 1
        elif status == "Blocked":
            stats[today]['blocked_entries'] += 1
        atomic_write_json(DAILY_STATS_FILE, stats)
    except Exception as e:
        logging.error(f"daily stats error: {e}")

def _ts_to_epoch(ts):
    try:
        if hasattr(ts, "timestamp"): return float(ts.timestamp())
        return float(ts)
    except Exception:
        return time.time()

# =========================
# Rate limiter
# =========================
class ScanRateLimiter:
    def __init__(self, delay=60):
        self.delay = delay
        self.last = {}
        self.lock = threading.Lock()
    def should_process(self, card_int):
        now = time.time()
        with self.lock:
            t = self.last.get(card_int, 0)
            if now - t >= self.delay:
                self.last[card_int] = now
                return True
            return False

# =========================
# Entry/Exit Tracker
# =========================
class EntryExitTracker:
    """Track card scans to only log transactions if entry/exit gap is satisfied."""
    def __init__(self, enabled=False, min_gap_seconds=300):
        self.enabled = enabled
        self.min_gap_seconds = min_gap_seconds
        self.last_scan = {}  # card_int -> {timestamp, reader}
        self.lock = threading.Lock()
    
    def should_create_transaction(self, card_int, reader_id):
        """Returns True if transaction should be created."""
        if not self.enabled:
            return True  # Tracking disabled, always create
        
        now = time.time()
        with self.lock:
            if card_int not in self.last_scan:
                # First scan, record it but don't create transaction yet
                self.last_scan[card_int] = {"timestamp": now, "reader": reader_id}
                return False
            
            last = self.last_scan[card_int]
            gap = now - last["timestamp"]
            
            # Check if gap is satisfied
            if gap >= self.min_gap_seconds:
                # Different entry/exit - create transaction
                self.last_scan[card_int] = {"timestamp": now, "reader": reader_id}
                return True
            else:
                # Too soon, don't create transaction
                return False

rate_limiter = ScanRateLimiter(SCAN_DELAY_SECONDS)
entry_exit_tracker = EntryExitTracker()

# =========================
# pigpio + Wiegand
# =========================
class WiegandDecoder:
    def __init__(self, pi, d0, d1, callback, timeout_ms=25, expected_bits=26):
        self.pi = pi; self.d0=d0; self.d1=d1
        self.callback = callback
        self.timeout_ms = timeout_ms
        self.expected_bits = expected_bits
        self.value=0; self.bits=0; self.last_tick=None

        pi.set_mode(d0, pigpio.INPUT)
        pi.set_mode(d1, pigpio.INPUT)
        pi.set_pull_up_down(d0, pigpio.PUD_UP)
        pi.set_pull_up_down(d1, pigpio.PUD_UP)

        self.cb0 = pi.callback(d0, pigpio.FALLING_EDGE, self._d0)
        self.cb1 = pi.callback(d1, pigpio.FALLING_EDGE, self._d1)

    def _d0(self, gpio, level, tick): self._bit(0, tick)
    def _d1(self, gpio, level, tick): self._bit(1, tick)

    def _bit(self, bit, tick):
        if self.last_tick is not None and pigpio.tickDiff(self.last_tick, tick) > self.timeout_ms*1000:
            self.value=0; self.bits=0
        self.value = (self.value<<1)|bit
        self.bits += 1
        self.last_tick = tick
        if self.bits == self.expected_bits:
            try: self.callback(self.bits, self.value)
            finally:
                self.value=0; self.bits=0

    def cancel(self):
        try: self.cb0.cancel()
        except: pass
        try: self.cb1.cancel()
        except: pass

def _extract_wiegand(bits, value):
    """CHANGED: Add basic parity validation for 26-bit; pass-through for 34-bit."""
    b = f"{value:0{bits}b}"
    if bits == 26:
        data = b[1:25]
        # Even parity for first 12, odd parity for last 12 (typical 26-bit)
        even_ok = (data[:12].count('1') % 2 == 0) == (b[0] == '0')
        odd_ok  = (data[12:].count('1') % 2 == 1) == (b[-1] == '1')
        if not (even_ok and odd_ok):
            return None
        return int(data, 2)
    elif bits == 34:
        # Parity schemes vary; keep as-is unless you know the scheme
        data = b[1:33]
        return int(data, 2)
    return None

# =========================
# Relays + access handling
# =========================
try:
    GPIO.setmode(GPIO.BCM)
    for r in (RELAY_1, RELAY_2, RELAY_3):
        GPIO.setup(r, GPIO.OUT)
        GPIO.output(r, GPIO.HIGH)  # default closed
except Exception as e:
    logging.error(f"GPIO init failed: {e}")

def pulse_relay(relay_gpio, seconds=1.0):
    try:
        GPIO.output(relay_gpio, GPIO.LOW)
        time.sleep(seconds)
        GPIO.output(relay_gpio, GPIO.HIGH)
    except Exception as e:
        logging.error(f"Relay error: {e}")

# Track relay manual override states
relay_hold_states = {RELAY_1: None, RELAY_2: None, RELAY_3: None}
RELAY_HOLD_LOCK = threading.RLock()

def operate_relay(action, relay_gpio):
    global relay_hold_states
    with RELAY_HOLD_LOCK:
        if action == "open_hold":
            GPIO.output(relay_gpio, GPIO.LOW)
            relay_hold_states[relay_gpio] = "open_hold"
        elif action == "close_hold":
            GPIO.output(relay_gpio, GPIO.HIGH)
            relay_hold_states[relay_gpio] = "close_hold"
        elif action in ("normal","normal_rfid"):
            # Only operate if not in manual hold mode
            if relay_hold_states.get(relay_gpio) is None:
                threading.Thread(target=pulse_relay, args=(relay_gpio,1.0), daemon=True).start()
            # If in hold mode, ignore RFID-triggered relay operations
        
        # Clear hold state when normal pulse is explicitly requested (not from RFID)
        if action == "normal":
            relay_hold_states[relay_gpio] = None

# CHANGED: thread-safe in-memory buffers
RECENT_LOCK = threading.RLock()
recent_transactions = deque(maxlen=200)

transaction_queue = Queue()

def handle_access(bits, value, reader_id):
    if bits not in (26,34): return
    card_int = _extract_wiegand(bits, value)
    if card_int is None:
        logging.warning("Wiegand parity failed; dropping read")
        return

    if not rate_limiter.should_process(card_int):
        logging.info(f"Duplicate ignored: {card_int}")
        return

    relay = RELAY_1 if reader_id==1 else (RELAY_2 if reader_id==2 else RELAY_3)

    with BLOCKED_SET_LOCK:
        is_blocked = card_int in BLOCKED_SET
    with ALLOWED_SET_LOCK:
        is_allowed = card_int in ALLOWED_SET

    # Check blocked status FIRST - blocked users cannot access even if they're in allowed set
    if is_blocked:
        status = "Blocked"; name = "Blocked"
        privacy_protected = False
    elif is_allowed:
        # Check if user has privacy protection enabled
        with USERS_LOCK:
            u = users.get(str(card_int))
            name = u.get("name","Unknown") if u else "Unknown"
            privacy_protected = u.get("privacy_protected", False) if u else False
        status = "Access Granted"
        operate_relay("normal_rfid", relay)
    else:
        status = "Access Denied"; name = "Unknown"
        privacy_protected = False

    # PRIVACY PROTECTION: Skip transaction logging if user has privacy enabled
    if privacy_protected:
        logging.info(f"Privacy protected: Skipped transaction logging for card {card_int} ({name})")
        return  # Access granted, relay operated, but no transaction logged

    # Check if transaction should be created (entry/exit tracking)
    if not entry_exit_tracker.should_create_transaction(card_int, reader_id):
        logging.info(f"Entry/Exit tracking: Skipped transaction for card {card_int} (gap not satisfied)")
        return

    ts = int(time.time())
    tx = {"name":name, "card":str(card_int), "reader":reader_id,
          "status":status, "timestamp":ts}

    # Persist locally (append to JSONL) and update stats
    try:
        append_local_transaction(tx)
    except Exception as e:
        logging.error(f"append_local_transaction error: {e}")
    update_daily_stats(status)

    # Enqueue for optional cloud upload
    try:
        transaction_queue.put(tx)
    except Exception as e:
        logging.error(f"queue put error: {e}")

    # light in-memory buffer for UI
    with RECENT_LOCK:
        recent_transactions.append(tx)

# =========================
# Background workers
# =========================
def transaction_uploader():
    """Upload to Firebase if available; save to persistent cache if offline."""
    while True:
        tx = transaction_queue.get()
        
        try:
            if db is not None and is_internet():
                try:
                    # Create a copy and add server timestamp + entity_id
                    tx_with_metadata = dict(tx)
                    tx_with_metadata['created_at'] = SERVER_TIMESTAMP
                    tx_with_metadata['entity_id'] = ENTITY_ID
                    
                    # Use auto-generated document ID (push_id style)
                    db.collection("transactions").add(tx_with_metadata)
                    logging.info(f"Transaction uploaded to Firestore: {tx.get('card')} - {tx.get('status')}")
                except Exception as e:
                    # Upload failed - save to persistent cache
                    append_failed_transaction(tx)
                    logging.warning(f"Firebase upload failed, saved to cache: {e}")
            else:
                # No internet or Firebase not initialized - save to persistent cache
                append_failed_transaction(tx)
                logging.info(f"Offline - transaction saved to cache: {tx.get('card')}")
        except Exception as e:
            logging.error(f"Transaction uploader error: {e}")
        finally:
            transaction_queue.task_done()

def failed_transactions_processor():
    """Background worker to process failed transactions cache when online.
    Runs independently without blocking normal access operations."""
    
    # Initial delay before first check
    time.sleep(60)  # Wait 1 minute after startup
    
    while True:
        try:
            # Check if we have internet and Firebase is available
            if db is not None and is_internet():
                # Load failed transactions from persistent cache
                failed_txs = load_failed_transactions()
                
                if failed_txs:
                    logging.info(f"Processing {len(failed_txs)} failed transactions from cache...")
                    
                    successfully_uploaded = []
                    still_failing = []
                    
                    # Process each failed transaction
                    for tx in failed_txs:
                        try:
                            # Prepare transaction with metadata
                            tx_with_metadata = dict(tx)
                            tx_with_metadata['created_at'] = SERVER_TIMESTAMP
                            tx_with_metadata['entity_id'] = ENTITY_ID
                            
                            # Try to upload
                            db.collection("transactions").add(tx_with_metadata)
                            successfully_uploaded.append(tx)
                            logging.info(f"✓ Uploaded cached transaction: {tx.get('card')} - {tx.get('status')}")
                            
                            # Small delay between uploads to avoid overwhelming the server
                            time.sleep(0.5)
                            
                        except Exception as e:
                            # Still failing, keep in cache
                            still_failing.append(tx)
                            logging.warning(f"✗ Failed to upload cached transaction: {e}")
                    
                    # Update cache file with only the still-failing transactions
                    if still_failing:
                        update_failed_transactions_cache(still_failing)
                        logging.info(f"Cache updated: {len(successfully_uploaded)} uploaded, {len(still_failing)} remaining")
                    else:
                        # All successful, clear the cache
                        clear_failed_transactions_cache()
                        logging.info(f"✓ All {len(successfully_uploaded)} cached transactions uploaded successfully!")
                
                # Wait before next check (5 minutes when online)
                time.sleep(300)
            else:
                # Offline or Firebase not available, wait longer before checking again (10 minutes)
                time.sleep(600)
                
        except Exception as e:
            logging.error(f"Failed transactions processor error: {e}")
            time.sleep(300)  # Wait 5 minutes on error before retrying

def housekeeping_worker():
    """Session cleanup + optional sync hook."""
    while True:
        try:
            cleanup_expired_sessions()
        except Exception as e:
            logging.error(f"housekeeping: {e}")
        time.sleep(300)  # 5 min

# =========================
# Auth / sessions
# =========================
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))
active_sessions = {}
SESS_LOCK = threading.RLock()  # CHANGED: guard session map

def generate_session_token():
    return secrets.token_urlsafe(32)

def cleanup_expired_sessions():
    now = datetime.now()
    with SESS_LOCK:
        expired = [t for t,v in active_sessions.items() if now>v['expires']]
        for t in expired:
            active_sessions.pop(t, None)

def is_authenticated():
    token = request.headers.get('Authorization','').replace('Bearer ','')
    with SESS_LOCK:
        return token in active_sessions

def require_auth(f):
    @wraps(f)
    def _w(*a,**k):
        if not is_authenticated():
            return jsonify({"status":"error","message":"Authentication required"}), 401
        return f(*a,**k)
    return _w

def require_api_key(f):
    @wraps(f)
    def _w(*a,**k):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"status":"error","message":"Invalid API key"}), 401
        return f(*a,**k)
    return _w

def require_both(f):
    """CHANGED: Defense-in-depth for mutating routes (API key + session)."""
    @wraps(f)
    def _w(*a,**k):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({"status":"error","message":"Invalid API key"}), 401
        if not is_authenticated():
            return jsonify({"status":"error","message":"Authentication required"}), 401
        return f(*a,**k)
    return _w

# =========================
# Flask routes (lean)
# =========================
@app.route("/")
def home(): return redirect(url_for('login_page'))

@app.route("/setup")
def setup_page(): return render_template("setup.html") if os.path.exists("templates/setup.html") else "Setup page not found"

@app.route("/login")
def login_page(): return render_template("login.html") if os.path.exists("templates/login.html") else "OK"

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")
        if username==ADMIN_USERNAME and verify_password(password, ADMIN_PASSWORD_HASH):
            token = generate_session_token()
            with SESS_LOCK:
                active_sessions[token] = {
                    "username": username,
                    "login_time": datetime.now(),
                    "expires": datetime.now()+timedelta(hours=SESSION_TTL_HOURS)
                }
            return jsonify({"status":"success","token":token})
        return jsonify({"status":"error","message":"Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"login error: {e}")
        return jsonify({"status":"error","message":"Login failed"}), 500

@app.route("/logout", methods=["POST"])
@require_auth
def logout():
    token = request.headers.get('Authorization','').replace('Bearer ','')
    with SESS_LOCK:
        active_sessions.pop(token, None)
    return jsonify({"status":"success"})

@app.route("/status")
def status():
    try:
        pigpio_ok = bool(pi and pi.connected)
    except:
        pigpio_ok = False
    try:
        readers_ok = all(x is not None for x in (wiegand1, wiegand2, wiegand3))
    except:
        readers_ok = False
    return jsonify({
        "system":"online",
        "timestamp": datetime.now().isoformat(),
        "components":{
            "firebase": db is not None,
            "pigpio": pigpio_ok,
            "rfid_readers": readers_ok,
            "internet": is_internet()
        },
        "storage":{
            "tx_dir_gb": round(get_tx_dir_size_bytes()/1024/1024/1024, 3),
            "cap_gb": MAX_TX_STORAGE_GB,
            "cleanup_fraction": CLEANUP_FRACTION
        },
        "files":{
            "users": os.path.exists(USER_DATA_FILE),
            "blocked": os.path.exists(BLOCKED_USERS_FILE),
            "daily_stats": os.path.exists(DAILY_STATS_FILE)
        },
        "temperature": {
            "cpu_celsius": get_cpu_temperature()
        }
    })

# --- Users ---
@app.route("/get_users", methods=["GET"])
@require_auth
def get_users():
    u = load_local_users()
    b = load_blocked_users()
    out = []
    for card, data in u.items():
        out.append({"card_number":card,
                    "id":data.get("id",""),
                    "name":data.get("name",""),
                    "ref_id":data.get("ref_id",""),
                    "blocked": b.get(card, False),
                    "privacy_protected": data.get("privacy_protected", False)})
    out.sort(key=lambda x: x["name"].lower())
    return jsonify(out)

@app.route("/add_user", methods=["POST"])
@require_both  # CHANGED: both API key and session
def add_user():
    try:
        data = request.get_json(force=True)
        card = str(data.get("card_number","")).strip()
        uid  = data.get("id","")
        name = data.get("name","")
        if not (card.isdigit() and uid and name):
            return jsonify({"status":"error","message":"card_number,id,name required"}), 400
        curr = load_local_users()
        curr[card] = {"id":uid, "name":name, "card_number":card, "ref_id": data.get("ref_id","")}
        save_local_users(curr)
        return jsonify({"status":"success"})
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

@app.route("/delete_user", methods=["POST"])
@require_both  # CHANGED
def delete_user():
    try:
        data = request.get_json(force=True)
        card = str(data.get("card_number","")).strip()
        curr = load_local_users()
        if card in curr:
            curr.pop(card)
            save_local_users(curr)
            return jsonify({"status":"success"})
        return jsonify({"status":"error","message":"not found"}), 404
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

# --- Block/Unblock ---
@app.route("/block_user", methods=["POST"])
@require_both  # CHANGED
def block_user():
    data = request.get_json(force=True)
    card = str(data.get("card_number","")).strip()
    b = load_blocked_users()
    b[card] = True
    save_blocked_users(b)
    return jsonify({"status":"success"})

@app.route("/unblock_user", methods=["POST"])
@require_both  # CHANGED
def unblock_user():
    data = request.get_json(force=True)
    card = str(data.get("card_number","")).strip()
    b = load_blocked_users()
    if card in b: b.pop(card)
    save_blocked_users(b)
    return jsonify({"status":"success"})

# --- Privacy Protection ---
@app.route("/toggle_privacy", methods=["POST"])
@require_both
def toggle_privacy():
    """Toggle privacy protection for a user (requires password confirmation)."""
    try:
        data = request.get_json(force=True)
        card = str(data.get("card_number","")).strip()
        password = data.get("password", "")
        enable = data.get("enable", True)
        
        # Verify admin password
        if not verify_password(password, ADMIN_PASSWORD_HASH):
            logging.warning(f"Privacy toggle failed: Invalid password for card {card}")
            return jsonify({"status":"error","message":"Invalid password"}), 401
        
        # Update user
        curr = load_local_users()
        if card not in curr:
            return jsonify({"status":"error","message":"User not found"}), 404
        
        curr[card]["privacy_protected"] = enable
        save_local_users(curr)
        
        action = "enabled" if enable else "disabled"
        logging.warning(f"Privacy protection {action} for card {card} ({curr[card].get('name', 'Unknown')})")
        
        return jsonify({
            "status":"success",
            "message":f"Privacy protection {action} for {curr[card].get('name', 'Unknown')}"
        })
    except Exception as e:
        logging.error(f"toggle_privacy error: {e}")
        return jsonify({"status":"error","message":str(e)}), 500

# --- Transactions (latest from memory + quick tail read) ---
def tail_transactions(limit=50):
    """
    Return newest -> oldest. Fast path from in-memory deque.
    Fallback reads last ~256KB from newest files.
    """
    with RECENT_LOCK:
        if len(recent_transactions) >= limit:
            out = list(recent_transactions)[-limit:]
            return list(reversed(out))  # newest -> oldest

    files = [n for n in os.listdir(TX_DIR) if n.endswith(".jsonl")]
    files.sort(reverse=True)  # newest file first
    acc = []
    for name in files:
        try:
            with open(os.path.join(TX_DIR, name), "rb") as f:
                f.seek(0, os.SEEK_END)
                sz = f.tell()
                chunk = 262144
                pos = max(0, sz - chunk)
                f.seek(pos, os.SEEK_SET)
                data = f.read().decode("utf-8", errors="ignore").splitlines()
                # iterate from end to get newest first
                for line in reversed(data):
                    try:
                        acc.append(json.loads(line))
                        if len(acc) >= limit:
                            return acc
                    except Exception:
                        continue
        except Exception:
            continue
    return acc

@app.route("/get_transactions", methods=["GET"])
@require_auth
def get_transactions():
    try:
        limit = int(request.args.get("limit", 50))
        return jsonify(tail_transactions(limit))
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

@app.route("/get_today_stats", methods=["GET"])
@require_auth
def get_today_stats():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {"total":0,"granted":0,"denied":0,"blocked":0}
        rows = read_json_or_default(DAILY_STATS_FILE, {})
        if today in rows:
            r = rows[today]
            stats["granted"] = r.get("valid_entries",0)
            stats["denied"]  = r.get("invalid_entries",0)
            stats["blocked"] = r.get("blocked_entries",0)
            stats["total"]   = stats["granted"]+stats["denied"]+stats["blocked"]
        return jsonify(stats)
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

# --- Advanced Analytics ---
@app.route("/get_analytics", methods=["GET"])
@require_auth
def get_analytics():
    """Get comprehensive analytics for all users or specific user."""
    try:
        days = int(request.args.get("days", 7))  # Last N days
        user_card = request.args.get("card", None)  # Optional: specific user
        
        # Get transactions for the period
        limit = min(days * 500, 5000)  # Estimate ~500 transactions per day, cap at 5000
        transactions = tail_transactions(limit)
        
        # Filter by date range
        cutoff_time = time.time() - (days * 24 * 3600)
        transactions = [tx for tx in transactions if tx.get("timestamp", 0) >= cutoff_time]
        
        # Filter by user if specified
        if user_card:
            transactions = [tx for tx in transactions if tx.get("card") == user_card]
        
        # Calculate analytics
        analytics = {
            "period_days": days,
            "total_transactions": len(transactions),
            "status_breakdown": {"granted": 0, "denied": 0, "blocked": 0},
            "reader_breakdown": {1: 0, 2: 0, 3: 0},
            "hourly_distribution": {str(i): 0 for i in range(24)},
            "daily_distribution": {},
            "top_users": {},
            "peak_hour": 0,
            "peak_day": "",
            "busiest_reader": 1,
            "unique_users": 0,
            "unique_cards": set()
        }
        
        # Process transactions
        for tx in transactions:
            # Status breakdown
            status = tx.get("status", "")
            if status == "Access Granted":
                analytics["status_breakdown"]["granted"] += 1
            elif status == "Access Denied":
                analytics["status_breakdown"]["denied"] += 1
            elif status == "Blocked":
                analytics["status_breakdown"]["blocked"] += 1
            
            # Reader breakdown
            reader = tx.get("reader", 1)
            if reader in analytics["reader_breakdown"]:
                analytics["reader_breakdown"][reader] += 1
            
            # Hourly distribution
            ts = tx.get("timestamp", 0)
            dt = datetime.fromtimestamp(ts)
            hour = str(dt.hour)
            analytics["hourly_distribution"][hour] += 1
            
            # Daily distribution
            day = dt.strftime("%Y-%m-%d")
            analytics["daily_distribution"][day] = analytics["daily_distribution"].get(day, 0) + 1
            
            # Top users (if not filtering by user)
            if not user_card:
                card = tx.get("card", "Unknown")
                name = tx.get("name", "Unknown")
                key = f"{name}|{card}"
                analytics["top_users"][key] = analytics["top_users"].get(key, 0) + 1
                analytics["unique_cards"].add(card)
        
        # Calculate derived stats
        if analytics["hourly_distribution"]:
            analytics["peak_hour"] = int(max(analytics["hourly_distribution"].items(), key=lambda x: x[1])[0])
        
        if analytics["daily_distribution"]:
            analytics["peak_day"] = max(analytics["daily_distribution"].items(), key=lambda x: x[1])[0]
        
        if analytics["reader_breakdown"]:
            analytics["busiest_reader"] = max(analytics["reader_breakdown"].items(), key=lambda x: x[1])[0]
        
        analytics["unique_users"] = len(analytics["unique_cards"])
        
        # Convert top users to list (sorted by count)
        if not user_card:
            top_users_list = []
            for key, count in sorted(analytics["top_users"].items(), key=lambda x: x[1], reverse=True)[:10]:
                name, card = key.split("|", 1)
                top_users_list.append({"name": name, "card": card, "count": count})
            analytics["top_users"] = top_users_list
        
        # Convert unique_cards set to count
        analytics["unique_cards"] = analytics["unique_users"]
        
        return jsonify({
            "status": "success",
            "analytics": analytics,
            "user_filter": user_card
        })
    except Exception as e:
        logging.error(f"get_analytics error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_user_report", methods=["GET"])
@require_auth
def get_user_report():
    """Get detailed report for a specific user."""
    try:
        card = request.args.get("card", "")
        days = int(request.args.get("days", 30))
        
        if not card:
            return jsonify({"status": "error", "message": "Card number required"}), 400
        
        # Get user info
        users_data = load_local_users()
        blocked = load_blocked_users()
        
        user_info = users_data.get(card, {})
        if not user_info:
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        # Get transactions
        limit = min(days * 100, 2000)
        all_transactions = tail_transactions(limit)
        
        cutoff_time = time.time() - (days * 24 * 3600)
        user_transactions = [
            tx for tx in all_transactions 
            if tx.get("card") == card and tx.get("timestamp", 0) >= cutoff_time
        ]
        
        # Calculate statistics
        report = {
            "user": {
                "name": user_info.get("name", "Unknown"),
                "card": card,
                "id": user_info.get("id", ""),
                "ref_id": user_info.get("ref_id", ""),
                "blocked": blocked.get(card, False)
            },
            "period_days": days,
            "summary": {
                "total_accesses": len(user_transactions),
                "granted": 0,
                "denied": 0,
                "blocked": 0,
                "avg_per_day": 0
            },
            "patterns": {
                "most_used_reader": 1,
                "favorite_hour": 0,
                "first_access": None,
                "last_access": None
            },
            "timeline": [],
            "hourly_pattern": {str(i): 0 for i in range(24)},
            "reader_usage": {1: 0, 2: 0, 3: 0}
        }
        
        if not user_transactions:
            return jsonify({"status": "success", "report": report})
        
        # Process transactions
        first_ts = float('inf')
        last_ts = 0
        
        for tx in user_transactions:
            status = tx.get("status", "")
            ts = tx.get("timestamp", 0)
            reader = tx.get("reader", 1)
            
            # Status counts
            if status == "Access Granted":
                report["summary"]["granted"] += 1
            elif status == "Access Denied":
                report["summary"]["denied"] += 1
            elif status == "Blocked":
                report["summary"]["blocked"] += 1
            
            # Hourly pattern
            hour = datetime.fromtimestamp(ts).hour
            report["hourly_pattern"][str(hour)] += 1
            
            # Reader usage
            if reader in report["reader_usage"]:
                report["reader_usage"][reader] += 1
            
            # Timeline (last 20 transactions)
            report["timeline"].append({
                "timestamp": ts,
                "reader": reader,
                "status": status
            })
            
            # Track first/last
            if ts < first_ts:
                first_ts = ts
            if ts > last_ts:
                last_ts = ts
        
        # Sort timeline by time (newest first)
        report["timeline"] = sorted(report["timeline"], key=lambda x: x["timestamp"], reverse=True)[:20]
        
        # Calculate patterns
        report["patterns"]["first_access"] = first_ts if first_ts != float('inf') else None
        report["patterns"]["last_access"] = last_ts if last_ts > 0 else None
        
        if report["hourly_pattern"]:
            report["patterns"]["favorite_hour"] = int(max(report["hourly_pattern"].items(), key=lambda x: x[1])[0])
        
        if report["reader_usage"]:
            report["patterns"]["most_used_reader"] = max(report["reader_usage"].items(), key=lambda x: x[1])[0]
        
        if days > 0:
            report["summary"]["avg_per_day"] = round(len(user_transactions) / days, 2)
        
        return jsonify({"status": "success", "report": report})
    except Exception as e:
        logging.error(f"get_user_report error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Relays ---
@app.route("/relay", methods=["POST"])
@require_both  # CHANGED
def relay():
    data = request.get_json(force=True)
    action = data.get("action","normal")
    relay_num = int(data.get("relay",1))
    relay_gpio = RELAY_1 if relay_num==1 else (RELAY_2 if relay_num==2 else RELAY_3)
    operate_relay(action, relay_gpio)
    return jsonify({"status":"success","message":f"relay {relay_num}:{action}"})

# --- Health ---
@app.route("/health_check", methods=["GET"])
def health_check():
    try:
        pigpio_ok = bool(pi and pi.connected)
    except:
        pigpio_ok = False
    return jsonify({
        "internet": is_internet(),
        "firebase": db is not None,
        "pigpio": pigpio_ok
    })

# --- Time Management ---
@app.route("/get_system_time", methods=["GET"])
@require_auth
def get_system_time():
    """Get current system time and timezone info."""
    try:
        now = datetime.now()
        return jsonify({
            "status": "success",
            "system_time": now.isoformat(),
            "timestamp": int(now.timestamp()),
            "timezone": time.strftime("%Z %z"),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        logging.error(f"get_system_time error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/set_system_time", methods=["POST"])
@require_both
def set_system_time():
    """Set system time from client browser or manual input."""
    try:
        data = request.get_json(force=True)
        timestamp = data.get("timestamp")  # Unix timestamp in seconds
        
        if not timestamp:
            return jsonify({"status": "error", "message": "Timestamp required"}), 400
        
        # Convert timestamp to datetime
        new_time = datetime.fromtimestamp(timestamp)
        
        # Format for system date command: YYYY-MM-DD HH:MM:SS
        time_str = new_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Set system time using timedatectl (systemd method, preferred)
        # This requires appropriate permissions
        try:
            import subprocess
            result = subprocess.run(
                ["sudo", "timedatectl", "set-time", time_str],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logging.warning(f"System time updated to {time_str} by {active_sessions.get(request.headers.get('Authorization','').replace('Bearer ',''), {}).get('username', 'unknown')}")
                return jsonify({
                    "status": "success",
                    "message": f"System time set to {time_str}",
                    "new_time": new_time.isoformat()
                })
            else:
                # Fallback to date command
                result = subprocess.run(
                    ["sudo", "date", "-s", time_str],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logging.warning(f"System time updated to {time_str} (via date) by {active_sessions.get(request.headers.get('Authorization','').replace('Bearer ',''), {}).get('username', 'unknown')}")
                    return jsonify({
                        "status": "success",
                        "message": f"System time set to {time_str}",
                        "new_time": new_time.isoformat()
                    })
                else:
                    raise Exception(f"Failed to set time: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            return jsonify({
                "status": "error",
                "message": "Time setting command timed out"
            }), 500
        except Exception as e:
            logging.error(f"Time setting error: {e}")
            return jsonify({
                "status": "error",
                "message": f"Failed to set system time: {str(e)}. Ensure sudo permissions are configured."
            }), 500
            
    except Exception as e:
        logging.error(f"set_system_time error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/enable_ntp", methods=["POST"])
@require_both
def enable_ntp():
    """Enable or disable NTP time synchronization."""
    try:
        data = request.get_json(force=True)
        enable = data.get("enable", True)
        
        import subprocess
        result = subprocess.run(
            ["sudo", "timedatectl", "set-ntp", "true" if enable else "false"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            action = "enabled" if enable else "disabled"
            logging.warning(f"NTP time sync {action} by {active_sessions.get(request.headers.get('Authorization','').replace('Bearer ',''), {}).get('username', 'unknown')}")
            return jsonify({
                "status": "success",
                "message": f"NTP time synchronization {action}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to configure NTP: {result.stderr}"
            }), 500
            
    except Exception as e:
        logging.error(f"enable_ntp error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Configuration ---
@app.route("/get_config", methods=["GET"])
@require_auth
def get_config_route():
    """Get current system configuration."""
    try:
        config = get_config()
        return jsonify({
            "status": "success",
            "config": config
        })
    except Exception as e:
        logging.error(f"get_config error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/update_config", methods=["POST"])
@require_both
def update_config_route():
    """Update system configuration and reinitialize readers if needed."""
    global wiegand1, wiegand2, wiegand3, rate_limiter, entry_exit_tracker, ENTITY_ID
    try:
        data = request.get_json(force=True)
        new_config = data.get("config", {})
        
        # Validate wiegand bits
        if "wiegand_bits" in new_config:
            for reader_key in ["reader_1", "reader_2", "reader_3"]:
                bits = new_config["wiegand_bits"].get(reader_key)
                if bits not in [26, 34]:
                    return jsonify({
                        "status": "error",
                        "message": f"Invalid bits for {reader_key}. Must be 26 or 34."
                    }), 400
        
        # Get current config
        current_config = get_config()
        
        # Check if Wiegand settings changed
        wiegand_changed = False
        if "wiegand_bits" in new_config:
            for reader_key in ["reader_1", "reader_2", "reader_3"]:
                if new_config["wiegand_bits"].get(reader_key) != current_config["wiegand_bits"].get(reader_key):
                    wiegand_changed = True
                    break
        
        # Update scan delay if changed
        if "scan_delay_seconds" in new_config:
            rate_limiter.delay = new_config["scan_delay_seconds"]
        
        # Update entry/exit tracking if changed
        if "entry_exit_tracking" in new_config:
            entry_exit_tracker.enabled = new_config["entry_exit_tracking"].get("enabled", False)
            entry_exit_tracker.min_gap_seconds = new_config["entry_exit_tracking"].get("min_gap_seconds", 300)
            logging.info(f"Entry/Exit tracking: {'enabled' if entry_exit_tracker.enabled else 'disabled'}, gap={entry_exit_tracker.min_gap_seconds}s")
        
        # Update entity ID if changed
        if "entity_id" in new_config:
            ENTITY_ID = new_config["entity_id"]
            logging.info(f"Entity ID updated to: {ENTITY_ID}")
        
        # Save new config
        save_config(new_config)
        
        # Reinitialize Wiegand decoders if settings changed
        if wiegand_changed and pi and pi.connected:
            try:
                # Cancel old decoders
                if wiegand1: wiegand1.cancel()
                if wiegand2: wiegand2.cancel()
                if wiegand3: wiegand3.cancel()
                
                time.sleep(0.1)  # Brief pause
                
                # Create new decoders with updated settings
                bits1 = new_config["wiegand_bits"]["reader_1"]
                bits2 = new_config["wiegand_bits"]["reader_2"]
                bits3 = new_config["wiegand_bits"]["reader_3"]
                t_ms = new_config.get("wiegand_timeout_ms", 25)
                
                wiegand1 = WiegandDecoder(pi, D0_PIN_1, D1_PIN_1, lambda b,v: handle_access(b,v,1), timeout_ms=t_ms, expected_bits=bits1)
                wiegand2 = WiegandDecoder(pi, D0_PIN_2, D1_PIN_2, lambda b,v: handle_access(b,v,2), timeout_ms=t_ms, expected_bits=bits2)
                wiegand3 = WiegandDecoder(pi, D0_PIN_3, D1_PIN_3, lambda b,v: handle_access(b,v,3), timeout_ms=t_ms, expected_bits=bits3)
                
                logging.info(f"Wiegand readers reinitialized: R1={bits1}bit, R2={bits2}bit, R3={bits3}bit")
            except Exception as e:
                logging.error(f"Wiegand reinit error: {e}")
                return jsonify({
                    "status": "warning",
                    "message": f"Config saved but reader reinit failed: {str(e)}"
                }), 200
        
        return jsonify({
            "status": "success",
            "message": "Configuration updated" + (" and readers reinitialized" if wiegand_changed else "")
        })
    except Exception as e:
        logging.error(f"update_config error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Security Settings ---
@app.route("/update_security", methods=["POST"])
@require_both
def update_security():
    """Update security settings (admin password and/or API key)."""
    global ADMIN_PASSWORD_HASH, API_KEY
    try:
        data = request.get_json(force=True)
        
        # Update admin password
        if "new_password" in data and data["new_password"]:
            new_password = data["new_password"]
            if len(new_password) < 8:
                return jsonify({
                    "status": "error",
                    "message": "Password must be at least 8 characters"
                }), 400
            
            ADMIN_PASSWORD_HASH = hash_password(new_password)
            logging.warning(f"Admin password changed by {active_sessions.get(request.headers.get('Authorization','').replace('Bearer ',''), {}).get('username', 'unknown')}")
        
        # Update API key
        if "new_api_key" in data and data["new_api_key"]:
            new_api_key = data["new_api_key"]
            if len(new_api_key) < 16:
                return jsonify({
                    "status": "error",
                    "message": "API key must be at least 16 characters"
                }), 400
            
            API_KEY = new_api_key
            logging.warning(f"API key changed by {active_sessions.get(request.headers.get('Authorization','').replace('Bearer ',''), {}).get('username', 'unknown')}")
        
        return jsonify({
            "status": "success",
            "message": "Security settings updated. Please update your saved credentials!"
        })
    except Exception as e:
        logging.error(f"update_security error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Dashboard ---
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html") if os.path.exists("templates/dashboard.html") else redirect(url_for('login_page'))

# --- CSV Export ---
@app.route("/download_transactions_csv", methods=["GET"])
@require_auth
def download_transactions_csv():
    try:
        limit = int(request.args.get("limit", 500))
        transactions = tail_transactions(limit)
        
        # Generate CSV
        csv_lines = ["Timestamp,Name,Card Number,Reader,Status"]
        for tx in transactions:
            timestamp = datetime.fromtimestamp(tx.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
            name = tx.get("name", "").replace(",", ";")  # Escape commas
            card = tx.get("card", "")
            reader = tx.get("reader", "")
            status = tx.get("status", "")
            csv_lines.append(f'{timestamp},{name},{card},{reader},{status}')
        
        csv_content = "\n".join(csv_lines)
        return jsonify({"status": "success", "csv": csv_content})
    except Exception as e:
        logging.error(f"CSV export error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================
# Startup (pigpio, readers, threads)
# =========================
pi = None
wiegand1 = wiegand2 = wiegand3 = None

def cleanup():
    try:
        if wiegand1: wiegand1.cancel()
        if wiegand2: wiegand2.cancel()
        if wiegand3: wiegand3.cancel()
    except: pass
    try:
        if pi: pi.stop()
    except: pass
    try:
        GPIO.cleanup()
    except: pass

def _sigterm(*_):
    cleanup()
    sys.exit(0)

def main():
    global pi, wiegand1, wiegand2, wiegand3
    # Trap SIGTERM (systemd)
    signal.signal(signal.SIGTERM, _sigterm)

    # Load sets at boot
    load_local_users()
    load_blocked_users()

    # pigpio
    try:
        pi = pigpio.pi()
        if not pi.connected:
            os.system("sudo pigpiod")
            time.sleep(0.3)
            pi = pigpio.pi()
            if not pi.connected:
                print("pigpio daemon not running. Start with: sudo pigpiod")
                sys.exit(1)
    except Exception as e:
        print(f"pigpio init failed: {e}")
        sys.exit(1)

    # Readers (bits configurable via web UI)
    config = get_config()
    bits1 = config["wiegand_bits"]["reader_1"]
    bits2 = config["wiegand_bits"]["reader_2"]
    bits3 = config["wiegand_bits"]["reader_3"]
    t_ms  = config["wiegand_timeout_ms"]
    
    # Load entry/exit tracking settings
    entry_exit_tracker.enabled = config["entry_exit_tracking"]["enabled"]
    entry_exit_tracker.min_gap_seconds = config["entry_exit_tracking"]["min_gap_seconds"]

    wiegand1 = WiegandDecoder(pi, D0_PIN_1, D1_PIN_1, lambda b,v: handle_access(b,v,1), timeout_ms=t_ms, expected_bits=bits1)
    wiegand2 = WiegandDecoder(pi, D0_PIN_2, D1_PIN_2, lambda b,v: handle_access(b,v,2), timeout_ms=t_ms, expected_bits=bits2)
    wiegand3 = WiegandDecoder(pi, D0_PIN_3, D1_PIN_3, lambda b,v: handle_access(b,v,3), timeout_ms=t_ms, expected_bits=bits3)
    
    logging.info(f"Wiegand readers initialized: R1={bits1}bit, R2={bits2}bit, R3={bits3}bit")
    logging.info(f"Entry/Exit tracking: {'enabled' if entry_exit_tracker.enabled else 'disabled'}, gap={entry_exit_tracker.min_gap_seconds}s")

    # Workers
    threading.Thread(target=transaction_uploader, daemon=True).start()
    threading.Thread(target=failed_transactions_processor, daemon=True).start()
    threading.Thread(target=housekeeping_worker,   daemon=True).start()
    threading.Thread(target=tx_storage_monitor_worker, daemon=True).start()

    # Flask
    host = os.environ.get('FLASK_HOST','0.0.0.0')
    port = int(os.environ.get('FLASK_PORT','5001'))
    debug= os.environ.get('FLASK_DEBUG','false').lower()=='true'
    try:
        print("Access controller ready. Waiting for Wiegand scans…")
        app.run(host=host, port=port, debug=debug, threaded=True)
    finally:
        cleanup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
