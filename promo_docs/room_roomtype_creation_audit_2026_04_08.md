# Room & Room Type Creation — Backend Security Audit

**Date:** 2026-04-08  
**Scope:** All writable endpoints for `Room` and `RoomType` entities  
**Verdict:** **UNSAFE — Critical permission override and serializer field trust issues**

---

## 1. Hotel Scoping

### How hotel is determined

| Path | Hotel source | Trusted? |
|------|-------------|----------|
| `StaffRoomTypeViewSet.perform_create()` | `request.user.staff_profile.hotel` | **Yes** — server-side |
| `RoomViewSet.perform_create()` | `request.user.staff_profile.hotel` | **Partially** — see below |
| `RoomTypeViewSet.perform_create()` | `request.user.staff_profile.hotel` | **Partially** — see below |
| `bulk_create_rooms()` | URL `hotel_slug` → `Hotel.objects.get(slug=)` | **Yes** — URL-resolved |
| `RoomSerializer.hotel` field | `PrimaryKeyRelatedField(queryset=Hotel.objects.all())` | **NO** — client-writable |

### Critical finding: `RoomSerializer.hotel` is writable

In `rooms/serializers.py` line 9-11:

```python
hotel = serializers.PrimaryKeyRelatedField(
    queryset=Hotel.objects.all()   # <-- ANY hotel ID accepted from request body
)
```

Although `RoomViewSet.perform_create()` calls `serializer.save(hotel=staff.hotel)` to override the hotel, this only works for **create**. For **update** (`PUT`/`PATCH`), the `hotel` field from _request.data_ is accepted by the serializer and could reassign a room to a different hotel unless the serializer explicitly marks `hotel` as read-only.

**Risk:** A staff member could `PATCH /api/staff/hotel/{slug}/room-management/{id}/` with `{"hotel": 999}` and move a room to hotel 999.

### Slug-based hotel enforcement

| Endpoint | `IsSameHotel` enforced? | How hotel_slug is checked |
|----------|------------------------|---------------------------|
| `StaffRoomTypeViewSet` | **Yes** | `staff.hotel.slug == hotel_slug` |
| `RoomViewSet` (via `room-management`) | **No** | Queryset filter only |
| `RoomTypeViewSet` (via `room-types` override) | **No** | Queryset filter only |
| `bulk_create_rooms` | **No** (has `IsStaffMember` but not `IsSameHotel`) | `hotel_slug` in URL, but no check that staff belongs to that hotel |

### Verdict

Hotel scoping is **inconsistent**. The canonical `StaffRoomTypeViewSet` is properly scoped but is overridden (see Section 2). Queryset filtering alone is not sufficient — it prevents _reading_ other hotels' data but does not prevent _writing_ to them via serializer fields.

---

## 2. Canonical Write Paths

### All writable endpoints for RoomType

| # | Route | View | Permissions | Serializer | Status |
|---|-------|------|------------|------------|--------|
| 1 | `POST /api/staff/hotel/{slug}/room-types/` | `StaffRoomTypeViewSet` | `IsAuthenticated` + `IsStaffMember` + `IsSameHotel` | `RoomTypeStaffSerializer` | **OVERRIDDEN** |
| 2 | `POST /api/staff/hotel/{slug}/room-types/` | `RoomTypeViewSet` | `IsAuthenticated` only | `RoomTypeSerializer` | **ACTIVE — UNSAFE** |
| 3 | `POST /api/staff/hotel/{slug}/room-types/{id}/upload-image/` | `StaffRoomTypeViewSet.upload_image` | Same as #1 | Custom | **OVERRIDDEN** |

### Why #1 is overridden by #2

In `staff_urls.py`, both viewsets are registered on the **same router prefix** `room-types`:

```python
# Line 78 — FIRST registration (correct permissions)
staff_hotel_router.register(r'room-types', StaffRoomTypeViewSet, basename='staff-room-types-direct')

# Line 148 — SECOND registration (weak permissions)
staff_hotel_router.register(r'room-types', RoomTypeViewSet, basename='staff-room-types')
```

DRF's `DefaultRouter` allows duplicate prefixes, but the **second registration's URL patterns override the first** for the same URL path. The result:

- `StaffRoomTypeViewSet` with `IsStaffMember` + `IsSameHotel` → **DEAD CODE**
- `RoomTypeViewSet` with only `IsAuthenticated` → **ACTIVE at `/api/staff/hotel/{slug}/room-types/`**
- `upload-image` custom action → **DEAD** (only exists on `StaffRoomTypeViewSet`)

**This is a critical security bug.** Any authenticated user (guest, non-staff) can create, update, and delete room types at the staff URL.

### All writable endpoints for Room

| # | Route | View | Permissions | Serializer | Status |
|---|-------|------|------------|------------|--------|
| 4 | `POST /api/staff/hotel/{slug}/room-management/` | `RoomViewSet` | `IsAuthenticated` only | `RoomSerializer` | **ACTIVE — UNSAFE** |
| 5 | `PUT/PATCH /api/staff/hotel/{slug}/room-management/{room_number}/` | `RoomViewSet` | `IsAuthenticated` only | `RoomSerializer` | **ACTIVE — UNSAFE** |
| 6 | `DELETE /api/staff/hotel/{slug}/room-management/{room_number}/` | `RoomViewSet` | `IsAuthenticated` only | — | **ACTIVE — UNSAFE** |
| 7 | `POST /api/staff/hotel/{slug}/room-types/{id}/rooms/bulk-create/` | `bulk_create_rooms` | `IsAuthenticated` + `IsStaffMember` | — | **ACTIVE — PARTIALLY SAFE** |

### Legacy `/api/rooms/` route

The `rooms/urls.py` router registers `RoomViewSet` at `/api/rooms/` but **this file is not included in the main URL config** (`HotelMateBackend/urls.py`). The `STAFF_APPS` list in `staff_urls.py` also comments out `'rooms'`. Therefore:

- **`/api/rooms/` is NOT accessible** — confirmed dead route
- **`rooms/urls.py` is dead code** that should be removed or left unmounted

### Canonical flow that should remain

1. **RoomType CRUD:** `StaffRoomTypeViewSet` at `/api/staff/hotel/{slug}/room-types/` — with `IsAuthenticated` + `IsStaffMember` + `IsSameHotel`
2. **Room bulk creation:** `bulk_create_rooms` at `/api/staff/hotel/{slug}/room-types/{id}/rooms/bulk-create/` — with `IsAuthenticated` + `IsStaffMember` + `IsSameHotel`
3. **Room individual management:** A properly-permissioned ViewSet (not the current `RoomViewSet`) — with `IsAuthenticated` + `IsStaffMember` + `IsSameHotel`

---

## 3. Permissions

### Permission matrix — current state

| Endpoint | `IsAuthenticated` | `IsStaffMember` | `IsSameHotel` | Safe? |
|----------|:-:|:-:|:-:|:-:|
| `room-types/` (active = RoomTypeViewSet) | ✅ | ❌ | ❌ | **NO** |
| `room-management/` (RoomViewSet) | ✅ | ❌ | ❌ | **NO** |
| `room-types/{id}/rooms/bulk-create/` | ✅ | ✅ | ❌ | **PARTIAL** |
| `rooms/{num}/start-cleaning/` | ✅ | ✅ | ✅ | ✅ |
| `rooms/{num}/mark-cleaned/` | ✅ | ✅ | ✅ | ✅ |
| `rooms/{num}/inspect/` | ✅ | ✅ | ✅ | ✅ |
| `rooms/{num}/mark-maintenance/` | ✅ | ✅ | ✅ | ✅ |
| `rooms/{num}/complete-maintenance/` | ✅ | ✅ | ✅ | ✅ |
| `turnover/rooms/` | ✅ | ✅ | ✅ | ✅ |
| `turnover/stats/` | ✅ | ✅ | ✅ | ✅ |

### Can guests create rooms or room types?

**Yes, currently.** Any authenticated user (including guest-authenticated tokens) can hit:
- `POST /api/staff/hotel/{slug}/room-management/` — creates a Room
- `POST /api/staff/hotel/{slug}/room-types/` — creates a RoomType

Neither requires `IsStaffMember`. The queryset filter in `get_queryset()` scopes reads to the staff's hotel, but a non-staff user would just get an empty queryset — they can still POST.

### `bulk_create_rooms` missing `IsSameHotel`

```python
@permission_classes([IsAuthenticated, IsStaffMember])   # <-- No IsSameHotel
def bulk_create_rooms(request, hotel_slug, room_type_id):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)    # <-- Uses URL slug, not staff's hotel
```

A staff member from Hotel A could call `/api/staff/hotel/hotel-b-slug/room-types/5/rooms/bulk-create/` and create rooms in Hotel B. The only guard is that `room_type_id` must belong to Hotel B (enforced by `get_object_or_404(RoomType, id=room_type_id, hotel=hotel)`), but if the attacker knows a valid room type ID, creation succeeds.

---

## 4. Serializer and Model Validation

### RoomType validation gaps

| Field | Model constraint | Serializer validation | Gap? |
|-------|-----------------|----------------------|------|
| `name` | `CharField(max_length=200)` — required | No custom validation | No — Django enforces required |
| `code` | `CharField(max_length=50, blank=True)` | None | **YES** — No uniqueness per hotel |
| `name` uniqueness | None | None | **YES** — Duplicate names allowed per hotel |
| `max_occupancy` | `PositiveSmallIntegerField(default=2)` | None | **YES** — Allows 0. No upper bound |
| `starting_price_from` | `DecimalField(max_digits=10, decimal_places=2)` — required | None | **YES** — Allows 0.00 and negative |
| `currency` | `CharField(max_length=3, default='EUR')` | None | **YES** — No ISO 4217 validation |
| `hotel` | `ForeignKey(Hotel)` — required | Not in serializer fields | Injected server-side (when using correct ViewSet) |

### Room validation

| Field | Model constraint | Serializer validation | Gap? |
|-------|-----------------|----------------------|------|
| `room_number` | `IntegerField` | None in serializer | **YES** — No positive check, no upper bound |
| `hotel` + `room_number` | `unique_together` | DB-level | OK — DB prevents duplicates |
| `room_type` | `ForeignKey(RoomType, null=True)` | `PrimaryKeyRelatedField` | **YES** — No check that room_type.hotel == room.hotel |
| `hotel` | `ForeignKey(Hotel)` | `PrimaryKeyRelatedField(queryset=Hotel.objects.all())` | **YES** — Writable, can set any hotel |
| `room_status` | Choices enforced | Not validated in serializer | `can_transition_to()` only used in workflow endpoints |

### Cross-hotel foreign key risk

`RoomSerializer` does not validate that `room_type.hotel == room.hotel`. A request could:
1. Create a room at Hotel A
2. Set `room_type` to a RoomType belonging to Hotel B

This is a data integrity violation. The `perform_create` override sets hotel correctly for creates, but the `room_type` FK is trusted from request data.

---

## 5. Bulk Room Creation

### Endpoint: `POST /api/staff/hotel/{slug}/room-types/{id}/rooms/bulk-create/`

| Check | Implemented? | Details |
|-------|:-:|---------|
| RoomType belongs to hotel | ✅ | `get_object_or_404(RoomType, id=room_type_id, hotel=hotel)` |
| Rejects inactive RoomType | ❌ | No `is_active=True` check — rooms can be created under deactivated types |
| Atomic transaction | ✅ | `with transaction.atomic()` wraps all creates |
| Handles duplicates | ✅ | Existing room numbers are skipped, not errored |
| Response shape | ✅ | Predictable: `created_count`, `skipped_existing`, `created_rooms`, `room_type` |
| Logs creation events | ❌ | No `RoomStatusEvent` created — initial `READY_FOR_GUEST` is unaudited |
| Room number validation | ✅ | 1–99999, integer check |
| Range validation | ✅ | `start <= end` enforced |
| Staff belongs to hotel | ❌ | Missing `IsSameHotel` — cross-hotel creation possible |

### Default values set on creation

```python
Room.objects.create(
    hotel=hotel,                        # From URL slug
    room_number=room_number,
    room_type=room_type,
    room_status='READY_FOR_GUEST',      # Correct default
    is_active=True,                     # Correct
    is_occupied=False,                  # Correct
    is_out_of_order=False               # Correct
)
```

Defaults are correct. The gap is permission enforcement (Section 3) and audit trail (Section 9).

---

## 6. Queryset and Object Ownership Safety

### `RoomViewSet`

```python
def get_queryset(self):
    staff = getattr(user, 'staff_profile', None)
    if staff and staff.hotel:
        queryset = Room.objects.filter(hotel=staff.hotel)
    # ... also accepts hotel_id query param
```

**Issues:**
1. If user has no `staff_profile`, queryset is `Room.objects.none()` — reads are empty but **writes still work** via `perform_create()`
2. Accepts `hotel_id` query parameter to further filter — redundant but harmless for reads
3. `hotel_id` query param could be confused with scoping — it's a filter, not an access check

### `RoomViewSet.perform_create()`

```python
def perform_create(self, serializer):
    staff = getattr(self.request.user, 'staff_profile', None)
    if staff and staff.hotel:
        serializer.save(hotel=staff.hotel)       # <-- Overrides hotel
    else:
        raise PermissionDenied(...)
```

Hotel is injected server-side for **create**. But this ViewSet is a full `ModelViewSet` — it also exposes `update()`, `partial_update()`, and `destroy()`. These methods call `serializer.save()` without hotel override. The `hotel` field is writable in the serializer.

### `RoomTypeViewSet.perform_create()`

Same pattern — hotel injected for create, but update paths have no override.

### `StaffRoomTypeViewSet` (proper version — currently overridden)

```python
def get_queryset(self):
    staff = self.request.user.staff_profile    # Will 500 for non-staff users
    return RoomType.objects.filter(hotel=staff.hotel)

def perform_create(self, serializer):
    staff = self.request.user.staff_profile
    serializer.save(hotel=staff.hotel)
```

This is correct, but `hotel` is excluded from serializer fields in `RoomTypeStaffSerializer`, which is the right pattern. However this ViewSet is currently dead code due to the router override.

### Summary

| Method | Hotel injected server-side? | Writable from client? |
|--------|:-:|:-:|
| `RoomViewSet.create` | ✅ | ✅ (overridden by `perform_create`) |
| `RoomViewSet.update` | ❌ | ✅ (**BUG** — `hotel` writable) |
| `RoomViewSet.partial_update` | ❌ | ✅ (**BUG** — `hotel` writable) |
| `RoomTypeViewSet.create` | ✅ | N/A (hotel not in serializer fields) |
| `RoomTypeViewSet.update` | ❌ | N/A (hotel not in serializer fields) |
| `bulk_create_rooms` | ✅ (URL-based) | N/A (no serializer) |

---

## 7. Response Contract Consistency

### RoomType serializers

| Serializer | Used by | Field count | Key fields |
|-----------|---------|:-:|------------|
| `RoomTypeStaffSerializer` | `StaffRoomTypeViewSet` (dead) | 16 | All marketing + pricing + booking fields |
| `RoomTypeSerializer` | `RoomTypeViewSet` (active) | 7 | `id, name, code, max_occupancy, starting_price_from, currency, is_active` |

**Problem:** The active endpoint uses the minimal serializer. Staff users get fewer fields than intended.
- Missing from active response: `short_description`, `bed_setup`, `photo`, `photo_url`, `booking_code`, `booking_url`, `availability_message`, `sort_order`
- `upload-image` action is dead code (only on `StaffRoomTypeViewSet`)

### Room serializers

| Serializer | Used by | Key difference |
|-----------|---------|----------------|
| `RoomSerializer` | `RoomViewSet` (active at `room-management/`) | Full guest data, `hotel` writable |
| `RoomStaffSerializer` | Imported but not used in any ViewSet | Lean staff inventory view |

### Recommendation

- **Staff RoomType contract:** `RoomTypeStaffSerializer` — all fields, `hotel` excluded (injected)
- **Staff Room contract:** `RoomStaffSerializer` — lean inventory fields, `hotel` excluded
- **Public/Guest Room Type:** `RoomTypeSerializer` — read-only display subset

---

## 8. Deletion and Lifecycle

### RoomType deletion

- `on_delete=PROTECT` on `Room.room_type` FK — **Cannot delete a RoomType that has physical rooms**
- This is correct. Attempting to delete returns a `ProtectedError`
- **No soft delete** — `is_active=False` deactivates for display but doesn't prevent use

### Room deletion

- `RoomViewSet` is a `ModelViewSet` — exposes `DELETE` at `/room-management/{room_number}/`
- Only requires `IsAuthenticated` — **any authenticated user can delete rooms**
- No check for occupied rooms, active bookings, or cascading effects
- `on_delete=CASCADE` on `Room.hotel` FK — deleting a hotel deletes all rooms

### Missing bulk operations

- **No bulk delete** endpoint
- **No bulk deactivate** endpoint (would need `PATCH` with `is_active=False`)
- **No bulk archive** — rooms are either active or deleted, no middle state
- Bulk create exists but bulk lifecycle management does not

---

## 9. Audit Trail

### What is audited

| Event | Audit mechanism | Audited? |
|-------|----------------|:-:|
| Room status change (workflow) | `RoomStatusEvent` via `set_room_status()` | ✅ |
| Room creation (single or bulk) | None | ❌ |
| Room deletion | None | ❌ |
| RoomType creation | None | ❌ |
| RoomType update | None | ❌ |
| RoomType deletion | None | ❌ |
| Room field update (is_active, etc.) | None | ❌ |

### Gap

Room and RoomType CRUD operations have **no audit trail**. The `RoomStatusEvent` model is purpose-built for status workflow transitions only. Initial room creation (`READY_FOR_GUEST`) is never logged there.

### Recommended fix

Create `ROOM_CREATED` and `ROOM_TYPE_CREATED` as source types in `RoomStatusEvent`, or create a separate `InventoryEvent` audit model. The bulk_create endpoint is the highest priority — hotels need to know who provisioned their room inventory.

---

## 10. Final Output

### A. Endpoint Safety Matrix

| # | Method | URL | View | Safe? | Issue |
|---|--------|-----|------|:-----:|-------|
| 1 | `GET/POST/PUT/PATCH/DELETE` | `/api/staff/hotel/{slug}/room-types/` | `RoomTypeViewSet` (overrides StaffRoomTypeViewSet) | **NO** | Only `IsAuthenticated` — no staff or hotel check |
| 2 | `GET/POST/PUT/PATCH/DELETE` | `/api/staff/hotel/{slug}/room-management/` | `RoomViewSet` | **NO** | Only `IsAuthenticated` — no staff or hotel check |
| 3 | `POST` | `/api/staff/hotel/{slug}/room-types/{id}/rooms/bulk-create/` | `bulk_create_rooms` | **PARTIAL** | Missing `IsSameHotel` |
| 4 | `POST` | `/api/staff/hotel/{slug}/rooms/{num}/start-cleaning/` | `start_cleaning` | ✅ | Correct permissions |
| 5 | `POST` | `/api/staff/hotel/{slug}/rooms/{num}/mark-cleaned/` | `mark_cleaned` | ✅ | Correct permissions |
| 6 | `POST` | `/api/staff/hotel/{slug}/rooms/{num}/inspect/` | `inspect_room` | ✅ | Correct permissions |
| 7 | `POST` | `/api/staff/hotel/{slug}/rooms/{num}/mark-maintenance/` | `mark_maintenance` | ✅ | Correct permissions |
| 8 | `POST` | `/api/staff/hotel/{slug}/rooms/{num}/complete-maintenance/` | `complete_maintenance` | ✅ | Correct permissions |
| 9 | `GET` | `/api/staff/hotel/{slug}/turnover/rooms/` | `turnover_rooms` | ✅ | Correct permissions |
| 10 | `GET` | `/api/staff/hotel/{slug}/turnover/stats/` | `turnover_stats` | ✅ | Correct permissions |

### B. Security Risks (Priority Order)

| Priority | Risk | Impact | Exploitability |
|:--------:|------|--------|----------------|
| **P0** | `StaffRoomTypeViewSet` overridden by `RoomTypeViewSet` — duplicate router prefix | Any authenticated user (guest, non-staff) can create/update/delete room types for ANY hotel | **Trivial** — POST to known URL |
| **P0** | `RoomViewSet` at `room-management/` has no `IsStaffMember` or `IsSameHotel` | Any authenticated user can create/update/delete rooms | **Trivial** — POST to known URL |
| **P1** | `RoomSerializer.hotel` is writable `PrimaryKeyRelatedField` | Staff can reassign rooms to another hotel via PATCH | Requires knowing target hotel ID |
| **P1** | `bulk_create_rooms` missing `IsSameHotel` | Staff from Hotel A can create rooms in Hotel B | Requires knowing hotel slug and room type ID |
| **P2** | No cross-hotel FK validation for `room_type` on Room | Room can reference a RoomType from a different hotel | Data integrity — no auth bypass |
| **P2** | No RoomType field validation (price, occupancy, currency) | Invalid data in inventory | Low impact — bad data, not auth bypass |
| **P3** | No audit trail for room/room type CRUD | Cannot trace who provisioned inventory | Compliance risk |

### C. Canonical Flow That Should Remain

**RoomType CRUD:**
```
StaffRoomTypeViewSet → /api/staff/hotel/{slug}/room-types/
  Permissions: IsAuthenticated + IsStaffMember + IsSameHotel
  Serializer:  RoomTypeStaffSerializer (hotel excluded from fields)
  Hotel:       Injected via staff_profile.hotel in perform_create/perform_update
```

**Room Bulk Creation:**
```
bulk_create_rooms → /api/staff/hotel/{slug}/room-types/{id}/rooms/bulk-create/
  Permissions: IsAuthenticated + IsStaffMember + IsSameHotel
  Hotel:       Resolved from URL slug (with IsSameHotel enforcing ownership)
```

**Room Individual CRUD (if needed):**
```
StaffRoomViewSet → /api/staff/hotel/{slug}/room-management/
  Permissions: IsAuthenticated + IsStaffMember + IsSameHotel
  Serializer:  RoomStaffSerializer (hotel excluded, room_type validated per hotel)
  Hotel:       Injected via staff_profile.hotel
```

### D. Endpoints to Restrict or Remove

| Action | Endpoint/Code | Reason |
|--------|---------------|--------|
| **REMOVE** | Second `staff_hotel_router.register(r'room-types', RoomTypeViewSet)` at line 148 of `staff_urls.py` | Overrides secure ViewSet with insecure one |
| **RESTRICT** | `RoomViewSet` at `room-management/` — add `IsStaffMember` + `IsSameHotel` | Currently allows non-staff writes |
| **RESTRICT** | `bulk_create_rooms` — add `IsSameHotel` to permission classes | Cross-hotel creation possible |
| **MAKE READ-ONLY or REMOVE** | `rooms/urls.py` router | Dead code — not mounted but confusing |
| **RESTRICT** | `RoomSerializer.hotel` field — make `read_only=True` | Prevents client from choosing hotel |

### E. Code-Level Fix Plan (Priority Order)

**Fix 1 (P0): Remove duplicate RoomTypeViewSet registration**

File: `staff_urls.py` lines 147-150  
Action: DELETE these lines:
```python
staff_hotel_router.register(
    r'room-types',
    RoomTypeViewSet,
    basename='staff-room-types'
)
```
This restores `StaffRoomTypeViewSet` (lines 78-80) as the active handler at `/api/staff/hotel/{slug}/room-types/`.

**Fix 2 (P0): Add permissions to RoomViewSet or replace it**

File: `rooms/views.py` lines 34-68  
Action: Add `IsStaffMember` and `IsSameHotel` to `permission_classes`:
```python
class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
```
Or replace with a dedicated `StaffRoomViewSet` in `hotel/staff_views.py`.

**Fix 3 (P1): Make RoomSerializer.hotel read-only**

File: `rooms/serializers.py` lines 9-11  
Action: Change to:
```python
hotel = serializers.PrimaryKeyRelatedField(read_only=True)
```
And ensure `perform_create()` injects hotel for creates, and `perform_update()` prevents hotel mutation.

**Fix 4 (P1): Add IsSameHotel to bulk_create_rooms**

File: `rooms/views.py` line 663  
Action: Change to:
```python
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
```

**Fix 5 (P2): Validate room_type belongs to same hotel**

File: `rooms/serializers.py`  
Action: Add `validate_room_type()` method:
```python
def validate_room_type(self, value):
    request = self.context.get('request')
    if request and hasattr(request.user, 'staff_profile'):
        if value and value.hotel != request.user.staff_profile.hotel:
            raise serializers.ValidationError("Room type must belong to your hotel")
    return value
```

**Fix 6 (P2): Add RoomType field validation**

File: `hotel/staff_serializers.py` in `RoomTypeStaffSerializer`  
Action: Add:
```python
def validate_starting_price_from(self, value):
    if value is not None and value <= 0:
        raise serializers.ValidationError("Price must be greater than 0")
    return value

def validate_max_occupancy(self, value):
    if value < 1 or value > 50:
        raise serializers.ValidationError("Max occupancy must be between 1 and 50")
    return value
```

**Fix 7 (P3): Add audit trail for room creation**

File: `rooms/views.py` in `bulk_create_rooms`  
Action: After room creation loop, create `RoomStatusEvent` records:
```python
RoomStatusEvent.objects.create(
    hotel=hotel,
    room=room,
    from_status='',
    to_status='READY_FOR_GUEST',
    changed_by=staff,
    source='SYSTEM',
    note='Room created via bulk provisioning'
)
```

**Fix 8 (Cleanup): Remove dead room-management registration or replace**

File: `staff_urls.py` lines 143-146  
Action: Either remove `RoomViewSet` registration entirely (keep only bulk-create for room creation) or replace with a properly-permissioned dedicated `StaffRoomViewSet`.
