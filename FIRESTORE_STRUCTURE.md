# 🔥 Firestore Database Structure

## Overview

The access control system uses Firebase Firestore for **optional** cloud storage and synchronization of transaction data. The system works fully offline (storing locally), but can optionally sync to Firestore when internet is available.

---

## Database Hierarchy

```
Firestore Root
│
└── entities (Collection)
    │
    ├── [ENTITY_ID] (Document) - e.g., "default_entity", "building_a", "site_123"
    │   │
    │   └── transactions (Sub-collection)
    │       │
    │       ├── [TIMESTAMP-RANDOM] (Document) - e.g., "1728574245-a3f2d8e1"
    │       │   ├── name: "John Doe"
    │       │   ├── card: "12345678"
    │       │   ├── reader: 1
    │       │   ├── status: "Access Granted"
    │       │   └── timestamp: 1728574245
    │       │
    │       ├── [TIMESTAMP-RANDOM] (Document)
    │       │   ├── name: "Jane Smith"
    │       │   ├── card: "87654321"
    │       │   ├── reader: 2
    │       │   ├── status: "Access Denied"
    │       │   └── timestamp: 1728574250
    │       │
    │       └── ... (more transaction documents)
    │
    ├── [ANOTHER_ENTITY_ID] (Document) - e.g., "building_b"
    │   └── transactions (Sub-collection)
    │       └── ... (transactions for this entity)
    │
    └── ... (more entities)
```

---

## Collection Details

### 1. **entities** (Root Collection)

**Purpose**: Organize transactions by entity/site/location

**Type**: Collection

**Documents**: Each document represents a separate entity (building, site, installation)

**Key**: Entity ID (configurable via environment variable or web UI)

---

### 2. **[ENTITY_ID]** (Document in entities collection)

**Purpose**: Represents a specific entity/site/installation

**Example Entity IDs**:
- `default_entity` (default)
- `building_a`
- `site_123`
- `headquarters`
- `warehouse_north`

**Type**: Document

**Configuration**:
- Set via environment variable: `ENTITY_ID='your_entity_id'`
- Or change in web UI: Configuration tab > Entity Configuration

**Sub-collections**:
- `transactions` (stores all access control transactions)

---

### 3. **transactions** (Sub-collection)

**Purpose**: Store all access control transactions for this entity

**Type**: Sub-collection (nested under entity document)

**Documents**: Each document represents a single card scan/access attempt

---

## Transaction Document Structure

Each transaction document contains the following fields:

### Document ID
**Format**: `{timestamp}-{random_hex}`

**Example**: `1728574245-a3f2d8e1`

**Components**:
- `timestamp`: Unix timestamp (seconds since epoch)
- `random_hex`: 8-character random hex string for uniqueness

**Purpose**: Ensures unique document IDs even if multiple transactions occur in the same second

**Code**:
```python
ts_id = str(tx.get("timestamp", int(time.time())))
doc_id = f"{ts_id}-{secrets.token_hex(4)}"
```

### Document Fields

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `name` | String | User's name (from users database) | "John Doe", "Unknown", "Blocked" |
| `card` | String | RFID card number (as string) | "12345678", "87654321" |
| `reader` | Integer | Reader ID (1, 2, or 3) | 1, 2, 3 |
| `status` | String | Access control result | "Access Granted", "Access Denied", "Blocked" |
| `timestamp` | Integer | Unix timestamp (seconds) | 1728574245 |

### Example Transaction Document

**Path**: 
```
/entities/default_entity/transactions/1728574245-a3f2d8e1
```

**Data**:
```json
{
  "name": "John Doe",
  "card": "12345678",
  "reader": 1,
  "status": "Access Granted",
  "timestamp": 1728574245
}
```

---

## Status Values

The `status` field can have one of three values:

| Status | Meaning | When It Occurs |
|--------|---------|----------------|
| `Access Granted` | User allowed | Card found in users database and not blocked |
| `Access Denied` | User not recognized | Card not in users database |
| `Blocked` | User blocked | Card in users database but marked as blocked |

---

## Data Flow

### 1. **Card Scan** → Local Storage → Cloud Sync

```
RFID Card Scanned
     ↓
Transaction Created (in memory)
     ↓
Saved to Local JSONL File (immediate, offline-capable)
     ↓
Added to Upload Queue
     ↓
Background Worker Attempts Cloud Upload
     ↓
If Internet Available: Upload to Firestore
If Offline: Stays in local storage only
```

### 2. **Code Flow** (app.py)

```python
# 1. Create transaction object
tx = {
    "name": name, 
    "card": str(card_int), 
    "reader": reader_id,
    "status": status, 
    "timestamp": ts
}

# 2. Save locally (always happens)
append_local_transaction(tx)

# 3. Queue for cloud upload (if Firebase available)
transaction_queue.put(tx)

# 4. Background worker uploads (transaction_uploader function)
if db is not None and is_internet():
    ts_id = str(tx.get("timestamp", int(time.time())))
    doc_id = f"{ts_id}-{secrets.token_hex(4)}"
    db.collection("entities").document(ENTITY_ID)\
        .collection("transactions").document(doc_id).set(tx)
```

---

## Multi-Site Setup

For multiple installations (e.g., multiple buildings), you can use different entity IDs:

### Scenario: Company with 3 Buildings

**Building A**:
- Entity ID: `building_a`
- Path: `/entities/building_a/transactions/...`

**Building B**:
- Entity ID: `building_b`
- Path: `/entities/building_b/transactions/...`

**Warehouse**:
- Entity ID: `warehouse`
- Path: `/entities/warehouse/transactions/...`

### Firestore Structure:
```
/entities
  /building_a
    /transactions
      /1728574245-a3f2d8e1 {...}
      /1728574250-b7c4e9f2 {...}
  /building_b
    /transactions
      /1728574255-c8d5f1a3 {...}
  /warehouse
    /transactions
      /1728574260-d9e6g2b4 {...}
```

### Configuration:

**Option 1: Environment Variable** (before service starts)
```bash
export ENTITY_ID='building_a'
```

**Option 2: Web UI** (after service is running)
1. Login to dashboard
2. Go to Configuration tab
3. Find "Entity Configuration" section
4. Enter your entity ID (e.g., "building_a")
5. Click "Save Entity ID"

---

## Firebase Setup

### 1. **Create Firebase Project**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project (or use existing)
3. Enable Firestore Database
4. Set security rules (see below)

### 2. **Generate Service Account Key**

1. Go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save as `service.json` in your project directory
4. Update path in `.env` if different

### 3. **Environment Configuration**

Add to your `.env` file or environment:
```bash
FIREBASE_CRED_FILE=service.json
ENTITY_ID=default_entity
```

---

## Firestore Security Rules

### Recommended Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Entities collection
    match /entities/{entityId} {
      // Allow read/write to authenticated service accounts only
      allow read, write: if request.auth != null;
      
      // Transactions sub-collection
      match /transactions/{transactionId} {
        // Allow read/write to authenticated service accounts only
        allow read, write: if request.auth != null;
        
        // Validate transaction data structure
        allow create: if request.resource.data.keys().hasAll(['name', 'card', 'reader', 'status', 'timestamp'])
                      && request.resource.data.name is string
                      && request.resource.data.card is string
                      && request.resource.data.reader is int
                      && request.resource.data.status in ['Access Granted', 'Access Denied', 'Blocked']
                      && request.resource.data.timestamp is int;
      }
    }
  }
}
```

### Stricter Rules (Production)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Deny all by default
    match /{document=**} {
      allow read, write: if false;
    }
    
    // Only allow specific entities
    match /entities/{entityId} {
      // Only authenticated service accounts
      allow read, write: if request.auth != null 
                         && request.auth.token.email != null;
      
      match /transactions/{transactionId} {
        // Only allow creates, not updates or deletes
        allow create: if request.auth != null
                      && request.resource.data.keys().hasAll(['name', 'card', 'reader', 'status', 'timestamp'])
                      && request.resource.data.name is string
                      && request.resource.data.card is string
                      && request.resource.data.reader in [1, 2, 3]
                      && request.resource.data.status in ['Access Granted', 'Access Denied', 'Blocked']
                      && request.resource.data.timestamp is int
                      && request.resource.data.timestamp <= request.time.toMillis() / 1000 + 60; // Allow 60s clock skew
        
        // Allow reads for authenticated users
        allow read: if request.auth != null;
      }
    }
  }
}
```

---

## Querying Firestore Data

### From Firebase Console

Navigate to:
```
Firestore Database > Data > entities > [your_entity_id] > transactions
```

### Using Firebase SDK (Python)

```python
from firebase_admin import credentials, firestore, initialize_app

# Initialize
cred = credentials.Certificate("service.json")
initialize_app(cred)
db = firestore.client()

# Query all transactions for an entity
entity_id = "default_entity"
transactions_ref = db.collection("entities").document(entity_id).collection("transactions")

# Get all transactions
docs = transactions_ref.stream()
for doc in docs:
    print(f"ID: {doc.id}")
    print(f"Data: {doc.to_dict()}")

# Query by status
granted = transactions_ref.where("status", "==", "Access Granted").stream()
for doc in granted:
    print(doc.to_dict())

# Query by timestamp range (last 24 hours)
import time
yesterday = int(time.time()) - 86400
recent = transactions_ref.where("timestamp", ">=", yesterday).stream()
for doc in recent:
    print(doc.to_dict())

# Query by reader
reader1 = transactions_ref.where("reader", "==", 1).stream()
for doc in reader1:
    print(doc.to_dict())

# Query by card number
card_txs = transactions_ref.where("card", "==", "12345678").stream()
for doc in card_txs:
    print(doc.to_dict())
```

### Common Queries

**1. Get today's transactions:**
```python
from datetime import datetime

today_start = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
today_txs = transactions_ref.where("timestamp", ">=", today_start)\
                            .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                            .stream()
```

**2. Get denied/blocked access attempts:**
```python
denied = transactions_ref.where("status", "in", ["Access Denied", "Blocked"])\
                         .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                         .limit(100)\
                         .stream()
```

**3. Get specific user's history:**
```python
user_history = transactions_ref.where("card", "==", "12345678")\
                               .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                               .stream()
```

**4. Count transactions by status:**
```python
from collections import Counter

all_txs = transactions_ref.stream()
statuses = [doc.to_dict()["status"] for doc in all_txs]
print(Counter(statuses))
# Output: Counter({'Access Granted': 150, 'Access Denied': 25, 'Blocked': 5})
```

---

## Privacy Protection Impact

### Normal User (Privacy Protection Disabled)
```
RFID Scan → Transaction Created → Saved Locally → Uploaded to Firestore
```

### Privacy Protected User
```
RFID Scan → Access Granted → NO Transaction Created → Nothing Stored
```

**Note**: Users with privacy protection enabled will have NO records in Firestore or local storage.

---

## Local vs Cloud Storage

### Local Storage (Always)
- **Location**: `~/accessctl/transactions/transactions_YYYYMMDD.jsonl`
- **Format**: JSONL (one JSON object per line)
- **Purpose**: Primary storage, offline-capable
- **Retention**: Managed by auto-purge (default 16GB cap)

### Cloud Storage (Optional)
- **Location**: Firestore `/entities/[ENTITY_ID]/transactions/`
- **Format**: Firestore documents
- **Purpose**: Backup, multi-device access, analytics
- **Retention**: Managed by you (manual deletion or TTL policies)

### Comparison

| Feature | Local Storage | Firestore |
|---------|---------------|-----------|
| **Requires Internet** | No | Yes |
| **Automatic Backup** | No | Yes |
| **Multi-Device Access** | No | Yes |
| **Query Capabilities** | Limited | Full |
| **Storage Limit** | 16GB (configurable) | Unlimited |
| **Cost** | Free | Based on usage |
| **Speed** | Very Fast | Network dependent |
| **Offline Access** | Yes | No (unless cached) |

---

## Troubleshooting

### Issue: Transactions not uploading to Firestore

**Check**:
1. Is Firebase initialized?
   ```bash
   tail -f ~/accessctl/access.log | grep -i firebase
   ```
   Should see: "Firebase initialized"

2. Is service.json present and valid?
   ```bash
   ls -la service.json
   cat service.json | python3 -m json.tool
   ```

3. Is internet available?
   ```bash
   ping -c 3 8.8.8.8
   curl -I https://firestore.googleapis.com
   ```

4. Check Firestore rules allow writes

5. Check logs for upload errors:
   ```bash
   tail -f ~/accessctl/access.log | grep -i "firebase upload"
   ```

### Issue: Wrong entity being used

**Solution**:
1. Check current entity ID:
   ```bash
   grep ENTITY_ID ~/accessctl/.env
   ```

2. Update via web UI:
   - Configuration tab > Entity Configuration
   - Or restart with new environment variable:
   ```bash
   sudo systemctl stop access-control
   export ENTITY_ID='your_new_entity'
   sudo systemctl start access-control
   ```

---

## Best Practices

### 1. **Entity Naming**
- Use descriptive names: `headquarters`, `warehouse_a`
- Avoid spaces: Use underscores or hyphens
- Keep it short and memorable
- Document your entity IDs

### 2. **Security**
- Keep `service.json` secure (never commit to git)
- Use appropriate Firestore security rules
- Regularly review access logs
- Consider using different service accounts per entity

### 3. **Data Retention**
- Set up Firestore TTL policies for old transactions
- Or use Cloud Functions to archive old data
- Keep local storage cap reasonable for your SD card

### 4. **Monitoring**
- Regularly check Firebase console for anomalies
- Monitor upload queue size (shouldn't grow indefinitely)
- Check local storage usage periodically

---

## Summary

**Structure**: `/entities/{entity_id}/transactions/{timestamp-random}`

**Data**: Each transaction has name, card, reader, status, timestamp

**Flow**: Card scan → Local JSONL → Queue → Firestore (if online)

**Multi-Site**: Different entity IDs for different locations

**Optional**: System works fully offline; Firestore is backup/sync only

**Configurable**: Entity ID via environment or web UI

---

For more information, see:
- Firebase Console: https://console.firebase.google.com/
- Firestore Documentation: https://firebase.google.com/docs/firestore
- Python Admin SDK: https://firebase.google.com/docs/admin/setup


