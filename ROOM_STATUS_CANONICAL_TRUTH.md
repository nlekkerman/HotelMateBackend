# ROOM STATUS CANONICAL TRUTH — BACKEND SOURCE OF TRUTH

**Date**: December 20, 2025  
**Status**: ✅ **COMPLETE ANALYSIS**  
**Purpose**: Definitive answers for frontend implementation  

---

## 1️⃣ EXACT ROOM_STATUS_CHOICES (Current)

**Source**: `/rooms/models.py` Line 38-45

```python
ROOM_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('OCCUPIED', 'Occupied'),
    ('CHECKOUT_DIRTY', 'Checkout Dirty'),
    ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
    ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'), 
    ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
    ('OUT_OF_ORDER', 'Out of Order'),
    ('READY_FOR_GUEST', 'Ready for Guest'),
]
```

**Default Status**: `'AVAILABLE'`

---

## 2️⃣ LEGACY STATUS ANALYSIS

### ❌ AVAILABLE — LEGACY STATUS

**Answer**: ✅ **YES, AVAILABLE IS LEGACY**

**Evidence**:
- **Still actively set**: Only as default in migrations and tests
- **Code usage**: Treated identically to `READY_FOR_GUEST` in all business logic
- **is_bookable() method**: `self.room_status in {'AVAILABLE', 'READY_FOR_GUEST'}`
- **Room assignment service**: `room_status__in=['AVAILABLE', 'READY_FOR_GUEST']`
- **Check-in validation**: **ONLY accepts `READY_FOR_GUEST`** (Line 577 rooms/views.py)

**Treatment**: AVAILABLE should be treated as **READY_FOR_GUEST** by frontend

**Recommendation**: 
- Frontend should **display AVAILABLE as "Ready for Guest"**
- Frontend should **allow same actions as READY_FOR_GUEST**
- Backend should eventually migrate all AVAILABLE → READY_FOR_GUEST

### ✅ All Other Statuses — CANONICAL
- `OCCUPIED` — Active status
- `CHECKOUT_DIRTY` — Active status  
- `CLEANING_IN_PROGRESS` — Active status
- `CLEANED_UNINSPECTED` — Active status
- `READY_FOR_GUEST` — **Primary canonical ready status**
- `MAINTENANCE_REQUIRED` — Active status
- `OUT_OF_ORDER` — Active status

---

## 3️⃣ CANONICAL WORKFLOW ORDER

**Source**: `can_transition_to()` method in Room model (Line 129-137)

### Complete State Machine:
```
CHECKOUT_DIRTY 
    ↓
CLEANING_IN_PROGRESS 
    ↓
CLEANED_UNINSPECTED 
    ↓
READY_FOR_GUEST 
    ↓
OCCUPIED 
    ↓
CHECKOUT_DIRTY (cycle repeats)
```

### AVAILABLE Position:
```
AVAILABLE (legacy) ≡ READY_FOR_GUEST (canonical)
    ↓
OCCUPIED
    ↓  
CHECKOUT_DIRTY
```

**Valid Transitions Matrix**:
```python
'AVAILABLE': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
'OCCUPIED': ['CHECKOUT_DIRTY'],
'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'CLEANED_UNINSPECTED', 'MAINTENANCE_REQUIRED'],
'CLEANING_IN_PROGRESS': ['CLEANED_UNINSPECTED', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
'CLEANED_UNINSPECTED': ['READY_FOR_GUEST', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
'MAINTENANCE_REQUIRED': ['CHECKOUT_DIRTY', 'OUT_OF_ORDER'],
'OUT_OF_ORDER': ['CHECKOUT_DIRTY'],
'READY_FOR_GUEST': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
```

---

## 4️⃣ CLEANING WORKFLOW RULES

### When is "Start Cleaning" Allowed?
**Answer**: ✅ **ONLY when room is dirty**

**Dirty Room Statuses**:
1. `CHECKOUT_DIRTY` — Primary dirty status after checkout
2. `CLEANING_IN_PROGRESS` — Already cleaning (can restart/rollback)

**Explicitly NOT Allowed**:
- ❌ `AVAILABLE` — Room is clean/ready
- ❌ `READY_FOR_GUEST` — Room is clean/ready
- ❌ `OCCUPIED` — Guest in room
- ❌ `CLEANED_UNINSPECTED` — Already cleaned, awaiting inspection

### Housekeeping Permissions (Line 105-115 housekeeping/policy.py):
```python
allowed_transitions = {
    'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'MAINTENANCE_REQUIRED'],
    'CLEANING_IN_PROGRESS': ['CLEANED_UNINSPECTED', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
    'CLEANED_UNINSPECTED': ['READY_FOR_GUEST', 'MAINTENANCE_REQUIRED'],
    'AVAILABLE': ['MAINTENANCE_REQUIRED'],  # Only maintenance, NO cleaning
    'READY_FOR_GUEST': ['MAINTENANCE_REQUIRED'],  # Only maintenance, NO cleaning
}
```

**Frontend Rule**: 
- Show "Start Cleaning" button ONLY for `CHECKOUT_DIRTY`
- Show "Resume/Restart Cleaning" for `CLEANING_IN_PROGRESS`
- Show "Mark Cleaned" for `CLEANING_IN_PROGRESS`
- Show "Inspect Room" for `CLEANED_UNINSPECTED`

---

## 5️⃣ AUTHORITATIVE "READY" STATE

### Check-In Eligibility
**Answer**: ✅ **ONLY `READY_FOR_GUEST` allows check-in**

**Evidence**: Check-in endpoint validation (Line 577 rooms/views.py):
```python
if room.room_status != 'READY_FOR_GUEST':
    return Response({
        'success': False,
        'error': 'INVALID_ROOM_STATUS',
        'message': f'Room status \'{room.room_status}\' is not ready for guest check-in.',
```

**Booking Eligibility** (Different from check-in):
- `AVAILABLE` — ✅ Can be assigned to bookings
- `READY_FOR_GUEST` — ✅ Can be assigned to bookings

**Frontend Rule**:
- Show "Check In" button ONLY for `READY_FOR_GUEST`
- Treat `AVAILABLE` as "Ready for Booking" not "Ready for Check-In"

---

## 6️⃣ BACKEND OPERATIONAL STATUS EXPOSURE

### Current Implementation
❌ **Backend does NOT currently expose operational_status or allowed_actions**

### Recommendation
✅ **Backend SHOULD expose `allowed_actions` array**

**Optimal Implementation**:
```json
{
    "room_status": "AVAILABLE", 
    "operational_status": "READY_FOR_GUEST",
    "allowed_actions": ["assign_booking", "maintenance"],
    "is_bookable": true,
    "can_checkin": false
}
```

**Alternatively** (Minimum Change):
```json
{
    "room_status": "CHECKOUT_DIRTY",
    "allowed_actions": ["start_cleaning", "maintenance"],
    "can_checkin": false,
    "is_bookable": false
}
```

### Action Mapping by Status:

```javascript
const ALLOWED_ACTIONS = {
    'AVAILABLE': ['assign_booking', 'maintenance'],
    'READY_FOR_GUEST': ['checkin', 'assign_booking', 'maintenance'],  
    'OCCUPIED': ['checkout', 'maintenance'],
    'CHECKOUT_DIRTY': ['start_cleaning', 'maintenance'],
    'CLEANING_IN_PROGRESS': ['mark_cleaned', 'restart_cleaning', 'maintenance'],
    'CLEANED_UNINSPECTED': ['inspect_room', 'maintenance'],
    'MAINTENANCE_REQUIRED': ['resolve_maintenance'],
    'OUT_OF_ORDER': ['resolve_maintenance']
};
```

**Backend Implementation Location**: Add to `RoomSerializer` in `/rooms/serializers.py`

---

## 7️⃣ FRONTEND IMPLEMENTATION RULES

### Status Display Rules
1. **Display `AVAILABLE` as "Ready for Guest" (legacy alias)**
2. **Show canonical status names for all others**
3. **Use operational_status if backend provides it**

### Action Button Rules
1. **"Start Cleaning"** — ONLY show for `CHECKOUT_DIRTY`
2. **"Check In"** — ONLY show for `READY_FOR_GUEST` (NOT for AVAILABLE)
3. **"Assign Booking"** — Show for both `AVAILABLE` and `READY_FOR_GUEST`
4. **"Mark Cleaned"** — ONLY show for `CLEANING_IN_PROGRESS`
5. **"Inspect Room"** — ONLY show for `CLEANED_UNINSPECTED`
6. **"Check Out"** — ONLY show for `OCCUPIED`

### Workflow Progression
```
User clicks "Start Cleaning" (CHECKOUT_DIRTY)
  ↓ Status becomes CLEANING_IN_PROGRESS
  
User clicks "Mark Cleaned" (CLEANING_IN_PROGRESS)
  ↓ Status becomes CLEANED_UNINSPECTED
  
User clicks "Approve Inspection" (CLEANED_UNINSPECTED) 
  ↓ Status becomes READY_FOR_GUEST
  
User clicks "Check In" (READY_FOR_GUEST)
  ↓ Status becomes OCCUPIED
  
User clicks "Check Out" (OCCUPIED)
  ↓ Status becomes CHECKOUT_DIRTY
```

---

## 8️⃣ BACKEND RECOMMENDATIONS

### Immediate (No Code Changes)
✅ **Use this document as canonical source**
✅ **Frontend locks to these rules**
✅ **No optimistic UI updates**

### Short Term (Recommended)
1. **Add `allowed_actions` field** to RoomSerializer
2. **Add `operational_status` field** that maps AVAILABLE → READY_FOR_GUEST
3. **Add `can_checkin` boolean** field for explicit check-in eligibility

### Long Term (Future Refactor)
1. **Migrate all AVAILABLE → READY_FOR_GUEST**
2. **Remove AVAILABLE from ROOM_STATUS_CHOICES**
3. **Update default status to READY_FOR_GUEST**

---

## 9️⃣ CRITICAL INTEGRATION POINTS

### Realtime Updates
- ✅ Existing `NotificationManager.realtime_room_updated()` works correctly
- ✅ Frontend receives status changes via Pusher
- ✅ No additional realtime changes needed

### Permission System
- ✅ Housekeeping staff can only do cleaning workflow
- ✅ Managers can override any status
- ✅ Front desk has limited status access
- ✅ Check-in/out requires rooms permission

### Data Consistency  
- ✅ All status changes go through canonical `set_room_status()` service
- ✅ Audit trail via `RoomStatusEvent` table
- ✅ Transaction safety with `select_for_update`

---

## 🎯 FINAL ANSWER TO FRONTEND

### Status Truth:
```
AVAILABLE = READY_FOR_GUEST (legacy alias)
READY_FOR_GUEST = canonical ready state  
CHECKOUT_DIRTY = dirty, needs cleaning
CLEANING_IN_PROGRESS = being cleaned
CLEANED_UNINSPECTED = cleaned, awaiting inspection
OCCUPIED = guest checked in
MAINTENANCE_REQUIRED = needs maintenance
OUT_OF_ORDER = temporarily unavailable
```

### Action Rules:
```
Check-In: ONLY READY_FOR_GUEST
Cleaning: ONLY CHECKOUT_DIRTY  
Booking Assignment: AVAILABLE or READY_FOR_GUEST
Checkout: ONLY OCCUPIED
```

### Backend Commitment:
✅ **Backend WILL expose allowed_actions array in next sprint**  
✅ **This document is the canonical source until then**  
✅ **No breaking changes to existing status values**

**Status**: 🟢 **FRONTEND UNBLOCKED** — Implement UI using these rules immediately
