# 🔄 Firestore Structure Changes - Required Modifications

## Proposed Structure Change

### Current Structure:
```
/entities/{entity_id}/transactions/{timestamp-random}
```

### New Structure:
```
/transactions/{auto_generated_push_id}
```

### Document Changes:
- Remove manual `doc_id` generation
- Use Firestore auto-generated document ID (push_id style)
- Add `created_at` field with `SERVER_TIMESTAMP`

---

## Changes Required in `app.py`

### 1. **Import Section** (Lines 17-21)

**Current:**
```python
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FROM_FIREBASE = True
except Exception:
    FROM_FIREBASE = False
```

**Change Required:**
```python
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1 import SERVER_TIMESTAMP  # ADD THIS LINE
    FROM_FIREBASE = True
except Exception:
    FROM_FIREBASE = False
```

**Reason:** Need to import `SERVER_TIMESTAMP` for Firestore server-side timestamp generation

---

### 2. **transaction_uploader() Function** (Lines 573-590)

**Current Code:**
```python
def transaction_uploader():
    """Upload to Firebase if available; otherwise local-only (already appended)."""
    while True:
        tx = transaction_queue.get()
        try:
            if db is not None and is_internet():
                try:
                    # CHANGED: avoid collisions by adding a short nonce
                    ts_id = str(tx.get("timestamp", int(time.time())))
                    doc_id = f"{ts_id}-{secrets.token_hex(4)}"
                    db.collection("entities").document(ENTITY_ID)\
                        .collection("transactions").document(doc_id).set(tx)
                except Exception as e:
                    # We already have local copy; just log
                    logging.warning(f"Firebase upload failed: {e}")
            # else: offline, nothing to do (local already stored)
        finally:
            transaction_queue.task_done()
```

**New Code:**
```python
def transaction_uploader():
    """Upload to Firebase if available; otherwise local-only (already appended)."""
    while True:
        tx = transaction_queue.get()
        try:
            if db is not None and is_internet():
                try:
                    # Add server timestamp for when document is created in Firestore
                    tx_with_timestamp = dict(tx)  # Create a copy
                    tx_with_timestamp['created_at'] = SERVER_TIMESTAMP
                    
                    # Use auto-generated document ID (push_id style)
                    db.collection("transactions").add(tx_with_timestamp)
                except Exception as e:
                    # We already have local copy; just log
                    logging.warning(f"Firebase upload failed: {e}")
            # else: offline, nothing to do (local already stored)
        finally:
            transaction_queue.task_done()
```

**Changes Made:**
1. **Removed**: Manual `doc_id` generation (lines 581-582)
2. **Removed**: Entity-based path structure (lines 583-584)
3. **Added**: Copy of transaction dict to avoid modifying original
4. **Added**: `created_at` field with `SERVER_TIMESTAMP`
5. **Changed**: `.collection("entities").document(ENTITY_ID).collection("transactions").document(doc_id).set(tx)`
6. **To**: `.collection("transactions").add(tx_with_timestamp)`

**Why `.add()` instead of `.document().set()`:**
- `.add(document)` automatically generates a unique push_id-style document ID
- Returns document reference with the auto-generated ID
- Cleaner and more Firestore-native approach

---

## Impact Analysis

### ✅ What Will Work

1. **Offline Operation**: Still works perfectly
   - Local JSONL storage unaffected
   - Transactions saved locally first
   - Queue waits for internet connection

2. **Online Sync**: Simplified
   - No more entity_id in path (can still include in document if needed)
   - Firestore generates unique IDs automatically
   - SERVER_TIMESTAMP generated server-side when online

3. **Document Structure**: Enhanced
   ```json
   {
     "name": "John Doe",
     "card": "12345678",
     "reader": 1,
     "status": "Access Granted",
     "timestamp": 1728574245,
     "created_at": {Firestore SERVER_TIMESTAMP}
   }
   ```

### ⚠️ Important Notes

1. **SERVER_TIMESTAMP Behavior**:
   - Only generated when document is SUCCESSFULLY uploaded to Firestore
   - If offline, the field won't exist (upload will fail and retry later)
   - When retried online, SERVER_TIMESTAMP will be the retry time, not original scan time
   - Local `timestamp` field preserves the actual scan time

2. **Entity ID Handling**:
   - Entity ID no longer part of path structure
   - If you need to filter by entity, add it as a field in the document:
   ```python
   tx_with_timestamp['entity_id'] = ENTITY_ID
   tx_with_timestamp['created_at'] = SERVER_TIMESTAMP
   ```

3. **Backward Compatibility**:
   - Old data in `/entities/{entity_id}/transactions/` won't be affected
   - New data goes to `/transactions/`
   - You'll have two separate collections (can migrate later if needed)

4. **Error Handling**:
   - If upload fails, error is logged
   - Transaction stays in local storage
   - Will retry on next queue cycle (but won't auto-retry the same transaction)

---

## Optional Enhancement: Add Entity ID to Document

If you want to preserve entity separation, add entity_id as a document field:

```python
def transaction_uploader():
    """Upload to Firebase if available; otherwise local-only (already appended)."""
    while True:
        tx = transaction_queue.get()
        try:
            if db is not None and is_internet():
                try:
                    # Add server timestamp and entity_id
                    tx_with_timestamp = dict(tx)  # Create a copy
                    tx_with_timestamp['created_at'] = SERVER_TIMESTAMP
                    tx_with_timestamp['entity_id'] = ENTITY_ID  # ADD THIS LINE
                    
                    # Use auto-generated document ID (push_id style)
                    db.collection("transactions").add(tx_with_timestamp)
                except Exception as e:
                    # We already have local copy; just log
                    logging.warning(f"Firebase upload failed: {e}")
            # else: offline, nothing to do (local already stored)
        finally:
            transaction_queue.task_done()
```

**Benefit**: Can filter by entity in queries:
```python
# Query transactions for specific entity
db.collection("transactions").where("entity_id", "==", "building_a").stream()
```

---

## New Firestore Structure

### Path:
```
/transactions/{auto_generated_id}
```

### Example Document:
**Path**: `/transactions/AbCdEfGhIjKlMnOpQrSt`

**Data**:
```json
{
  "name": "John Doe",
  "card": "12345678",
  "reader": 1,
  "status": "Access Granted",
  "timestamp": 1728574245,
  "created_at": {
    "_seconds": 1728574246,
    "_nanoseconds": 123456000
  },
  "entity_id": "default_entity"  // optional, if included
}
```

### Field Descriptions:
- `name`: User name (from local database)
- `card`: RFID card number
- `reader`: Reader ID (1, 2, or 3)
- `status`: "Access Granted" / "Access Denied" / "Blocked"
- `timestamp`: Unix timestamp when card was scanned (client-side, preserved offline)
- `created_at`: Firestore SERVER_TIMESTAMP (server-side, only when uploaded)
- `entity_id`: Optional, entity/site identifier for multi-site deployments

---

## Querying Examples (After Changes)

### Query by Date Range (using created_at):
```python
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(days=1)
recent = db.collection("transactions")\
          .where("created_at", ">=", yesterday)\
          .order_by("created_at", direction=firestore.Query.DESCENDING)\
          .stream()
```

### Query by Entity (if entity_id field added):
```python
entity_txs = db.collection("transactions")\
              .where("entity_id", "==", "building_a")\
              .order_by("created_at", direction=firestore.Query.DESCENDING)\
              .stream()
```

### Query by Card:
```python
card_history = db.collection("transactions")\
                .where("card", "==", "12345678")\
                .order_by("created_at", direction=firestore.Query.DESCENDING)\
                .stream()
```

### Query Today's Transactions:
```python
from datetime import datetime

today_start = datetime.now().replace(hour=0, minute=0, second=0)
today_txs = db.collection("transactions")\
             .where("created_at", ">=", today_start)\
             .stream()
```

---

## Updated Firestore Security Rules

### Basic Rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Transactions collection
    match /transactions/{transactionId} {
      // Only authenticated service accounts can write
      allow create: if request.auth != null
                    && request.resource.data.keys().hasAll(['name', 'card', 'reader', 'status', 'timestamp'])
                    && request.resource.data.name is string
                    && request.resource.data.card is string
                    && request.resource.data.reader in [1, 2, 3]
                    && request.resource.data.status in ['Access Granted', 'Access Denied', 'Blocked']
                    && request.resource.data.timestamp is int;
      
      // Allow reads for authenticated users
      allow read: if request.auth != null;
    }
  }
}
```

### With Entity ID Field:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    match /transactions/{transactionId} {
      allow create: if request.auth != null
                    && request.resource.data.keys().hasAll(['name', 'card', 'reader', 'status', 'timestamp', 'entity_id'])
                    && request.resource.data.name is string
                    && request.resource.data.card is string
                    && request.resource.data.reader in [1, 2, 3]
                    && request.resource.data.status in ['Access Granted', 'Access Denied', 'Blocked']
                    && request.resource.data.timestamp is int
                    && request.resource.data.entity_id is string;
      
      allow read: if request.auth != null;
    }
  }
}
```

**Note**: `created_at` validation is not needed in rules since it's server-generated

---

## Migration Considerations

### Old Data Location:
```
/entities/{entity_id}/transactions/{timestamp-random}
```

### New Data Location:
```
/transactions/{auto_generated_id}
```

### Options:

1. **Keep Both** (Recommended):
   - Old data stays in `/entities/...`
   - New data goes to `/transactions/`
   - Query both collections if needed
   - Eventually archive old collection

2. **Migrate Old Data**:
   - Write a migration script to copy data
   - Add `entity_id` field to old documents
   - Move to new `/transactions` collection
   - Delete old collection

3. **Fresh Start**:
   - Keep old data as archive
   - Start fresh with new structure
   - Most appropriate for this use case

---

## Summary of Changes

### Files to Modify:
✅ **app.py** only (2 locations)

### Lines to Change:
1. **Line 18**: Add `SERVER_TIMESTAMP` import
2. **Lines 573-590**: Update `transaction_uploader()` function

### Testing Checklist:
- [ ] Online: Verify transaction uploaded with `created_at` field
- [ ] Offline: Verify transaction saved locally, upload fails gracefully
- [ ] Reconnect: Verify queued transaction uploads with current `created_at`
- [ ] Query: Verify can query by `created_at`, `entity_id`, etc.
- [ ] Check Firestore console for new document structure

---

## Recommendation

**Add entity_id as a document field** for better multi-site support:
```python
tx_with_timestamp['entity_id'] = ENTITY_ID
```

This gives you:
- Flat, simple structure
- Easy queries across all entities
- Filter by entity when needed
- Better scalability

**Would you like me to proceed with these changes?**


