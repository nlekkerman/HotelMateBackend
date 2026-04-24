# Rooms Structural Cleanup

**Phase:** 6B.0 (structural only — RBAC/permissions unchanged).
**Source of truth:** `rooms/views.py`, `rooms/urls.py`, `rooms/staff_urls.py`,
`hotel/staff_views.py`, `hotel/urls.py`, `staff_urls.py`,
`HotelMateBackend/urls.py`. No doc or comment was trusted; every claim
below is pinned to a line in code.
**Product correction applied:** Room-level QR functionality is not used in
product. QR actions carry no weight in the canonical-class decision.

---

## 1. Duplicate Viewsets Analysis

### 1.1 `StaffRoomViewSet` — A vs B

**A — `rooms.views.StaffRoomViewSet`** ([rooms/views.py](rooms/views.py#L72-L108))
```python
class StaffRoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    pagination_class = RoomPagination
    lookup_field = 'room_number'
    filter_backends = [filters.SearchFilter]
    search_fields = ['room_number']

    def get_permissions(self):
        perms = [IsAuthenticated(), HasNavPermission('rooms'),
                 IsStaffMember(), IsSameHotel()]
        if self.action not in ('list', 'retrieve'):
            perms.append(CanManageRooms())
        return perms

    def get_queryset(self):
        staff = self.request.user.staff_profile
        return Room.objects.filter(hotel=staff.hotel
               ).select_related('room_type').order_by('room_number')

    def perform_create(self, serializer):
        serializer.save(hotel=staff.hotel)

    def perform_update(self, serializer):
        serializer.save()
```
Custom actions: **none**.

**B — `hotel.staff_views.StaffRoomViewSet`** ([hotel/staff_views.py](hotel/staff_views.py#L280-L353))
```python
class StaffRoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomStaffSerializer

    def get_permissions(self):
        base = [IsAuthenticated(), HasNavPermission('rooms'),
                IsStaffMember(), IsSameHotel()]
        if self.action not in ('list', 'retrieve'):
            base.append(CanManageRooms())
        return base

    def get_queryset(self):
        staff = self.request.user.staff_profile
        return Room.objects.filter(hotel=staff.hotel).order_by('room_number')

    def perform_create(self, serializer):
        serializer.save(hotel=staff.hotel)

    @action(detail=True, methods=['post'])
    def generate_pin(self, request, pk=None):
        return Response({'error': '... DEPRECATED ...'}, status=400)

    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        # dispatches to room.generate_qr_code / chat_pin / restaurant
        ...
```
Custom actions: `generate_pin` (deprecated, returns 400), `generate_qr`.

### 1.2 Side-by-side

| Attribute | A (`rooms.views`) | B (`hotel.staff_views`) |
|---|---|---|
| `queryset` / `get_queryset` | `Room.objects.filter(hotel=staff.hotel).select_related('room_type').order_by('room_number')` | `Room.objects.filter(hotel=staff.hotel).order_by('room_number')` (no `select_related`) |
| `lookup_field` | `'room_number'` | default (`pk`) |
| `pagination_class` | `RoomPagination` (page_size=10, max=100) | none (no pagination) |
| `filter_backends` | `[filters.SearchFilter]` | none |
| `search_fields` | `['room_number']` | none |
| `perform_create` | sets `hotel` from staff profile | identical |
| `perform_update` | explicit passthrough `serializer.save()` | inherited (no override) |
| `@action generate_pin` | **absent** | present, returns HTTP 400 unconditionally |
| `@action generate_qr` | **absent** | present, calls `room.generate_qr_code / generate_chat_pin_qr_code / generate_booking_qr_for_restaurant` |
| `get_permissions` body | same 4-class base + `CanManageRooms` on writes | same 4-class base + `CanManageRooms` on writes |
| Mount URL | `/api/staff/hotel/{slug}/room-management/` (via `staff_urls.py` L140-143) | `/api/hotel/staff/rooms/` (via `hotel/urls.py` L79-82) |

### 1.3 `StaffRoomTypeViewSet` — only one class, mounted twice

- Single class: `hotel.staff_views.StaffRoomTypeViewSet`
  ([hotel/staff_views.py](hotel/staff_views.py#L153-L280)) — full CRUD
  + `@action upload_image` (POST `upload-image/`, accepts file or URL,
  broadcasts `room-type-image-updated` on `hotel-{slug}` channel).
- Mounted twice:
  - `staff_urls.py` L75-78 → `/api/staff/hotel/{slug}/room-types/`.
  - `hotel/urls.py` L73-77 → `/api/hotel/staff/room-types/`.
- No competing class in `rooms/`. There is however a legacy read-only
  `rooms.views.RoomTypeViewSet` ([rooms/views.py](rooms/views.py#L112-L125))
  that is not registered on any router (grep-verified).

---

## 2. Canonical Decision

### 2.1 `StaffRoomViewSet` — KEEP **A** (`rooms.views.StaffRoomViewSet`). DELETE **B**.

Justification, strictly from code:

1. **QR is out of product scope.** `generate_qr` is the only
   non-deprecated differentiator B has over A. Workspace-wide grep for
   callers of `generate_qr_code`, `generate_chat_pin_qr_code`, and
   `generate_booking_qr_for_restaurant` on `Room`:
   - **Only caller is B's own `generate_qr` action.** No management
     command, signal, or other view invokes them. Deleting B therefore
     removes zero live functionality from the rest of the codebase.
   - (`generate_qr_code` matches in `staff/models.py`,
     `entertainment/views.py`, `hotel_info/views.py` are different
     models — `StaffRegistrationCode`, `Tournament`, `HotelQR` — not
     the `Room` method.)
2. **`generate_pin` is dead** — returns HTTP 400 unconditionally, has
   no functional branch.
3. **A has the richer data contract** required by production:
   - `pagination_class = RoomPagination` (B has none; unpaginated list
     endpoints are a latent scalability issue).
   - `lookup_field = 'room_number'` (B uses default `pk`; frontend
     lookup by `room_number` requires A).
   - `SearchFilter` + `search_fields=['room_number']` (B has none).
   - `select_related('room_type')` (B issues N+1 for serializer access
     of `room_type`).
4. **Serializer is identical** (`RoomStaffSerializer`) — no data-shape
   regression in either direction.
5. **Permission bodies are identical** — no RBAC regression. The
   keep/delete choice is a pure structural change.

**Net:** removing B drops only deprecated/unused actions; keeping A
preserves the superset of real behaviour.

### 2.2 `StaffRoomTypeViewSet` — KEEP the single class, DELETE the duplicate mount.

Only one implementation exists (`hotel.staff_views.StaffRoomTypeViewSet`).
The cleanup is removing its `hotel/urls.py` mount, not choosing between
classes. The legacy `rooms.views.RoomTypeViewSet` (unrouted, read-only)
is deleted in §6.

---

## 3. Required Behavior Preservation

Features the canonical A already has (no additions required):

- [x] `pagination_class = RoomPagination` — present at
  [rooms/views.py L80](rooms/views.py#L80).
- [x] `lookup_field = 'room_number'` — present at
  [rooms/views.py L81](rooms/views.py#L81).
- [x] `filter_backends = [filters.SearchFilter]` — present at
  [rooms/views.py L82](rooms/views.py#L82).
- [x] `search_fields = ['room_number']` — present at
  [rooms/views.py L83](rooms/views.py#L83).
- [x] `select_related('room_type')` — present in `get_queryset` at
  [rooms/views.py L100](rooms/views.py#L100).
- [x] `perform_create` sets hotel from staff profile —
  [rooms/views.py L104-L106](rooms/views.py#L104-L106).
- [x] `get_permissions` chain `[IsAuthenticated, HasNavPermission('rooms'),
  IsStaffMember, IsSameHotel]` + `CanManageRooms` on writes —
  [rooms/views.py L85-L93](rooms/views.py#L85-L93).

Behaviour NOT preserved (by design):
- `generate_qr` action — product does not use room QR.
- `generate_pin` action — unconditionally 400, never served real data.

No code needs to be added to A. Only deletions elsewhere.

---

## 4. Routing Before

All rooms-touching mounts currently live. Verified by reading
`staff_urls.py`, `hotel/urls.py`, `rooms/urls.py`, `rooms/staff_urls.py`,
and the project root `HotelMateBackend/urls.py`.

| Prefix (final URL) | Source registration | Target |
|---|---|---|
| `/api/staff/hotel/{slug}/room-management/` | `staff_urls.py` L140-143, `staff_hotel_router` | `rooms.views.StaffRoomViewSet` (A) |
| `/api/staff/hotel/{slug}/room-types/` | `staff_urls.py` L75-78, `staff_hotel_router` | `hotel.staff_views.StaffRoomTypeViewSet` |
| `/api/staff/hotel/{slug}/room-images/` | `staff_urls.py` L145-148, `staff_hotel_router` | `rooms.views.RoomImageViewSet` |
| `/api/staff/hotel/{slug}/rooms/checkout/` | `rooms/staff_urls.py` L15 | `rooms.views.checkout_rooms` |
| `/api/staff/hotel/{slug}/room-types/{room_type_id}/rooms/bulk-create/` | `rooms/staff_urls.py` L18 | `rooms.views.bulk_create_rooms` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/start-cleaning/` | `rooms/staff_urls.py` L21 | `rooms.views.start_cleaning` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/mark-cleaned/` | `rooms/staff_urls.py` L22 | `rooms.views.mark_cleaned` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/inspect/` | `rooms/staff_urls.py` L23 | `rooms.views.inspect_room` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/mark-maintenance/` | `rooms/staff_urls.py` L24 | `rooms.views.mark_maintenance` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/complete-maintenance/` | `rooms/staff_urls.py` L25 | `rooms.views.complete_maintenance` |
| `/api/staff/hotel/{slug}/turnover/rooms/` | `rooms/staff_urls.py` L28 | `rooms.views.turnover_rooms` |
| `/api/staff/hotel/{slug}/turnover/stats/` | `rooms/staff_urls.py` L29 | `rooms.views.turnover_stats` |
| **`/api/hotel/staff/rooms/`** | `hotel/urls.py` L79-82, `staff_router` | `hotel.staff_views.StaffRoomViewSet` (B) |
| **`/api/hotel/staff/rooms/{pk}/generate_pin/`** | `@action` on B | `B.generate_pin` |
| **`/api/hotel/staff/rooms/{pk}/generate_qr/`** | `@action` on B | `B.generate_qr` |
| **`/api/hotel/staff/room-types/`** | `hotel/urls.py` L73-77, `staff_router` | `hotel.staff_views.StaffRoomTypeViewSet` |
| **`/api/hotel/staff/room-types/{pk}/upload-image/`** | `@action` on `StaffRoomTypeViewSet` | `upload_image` |
| (orphan) `rooms/urls.py` router + 4 paths | `rooms/urls.py` (file not `include()`d anywhere) | `RoomViewSet`, `AddGuestToRoomView`, `RoomByHotelAndNumberView`, `checkout_rooms`, `checkout_needed` — **all unreachable** |

Bold rows = legacy mounts to be removed.

---

## 5. Routing After

Every route below is reachable via exactly one URL. No `/api/hotel/staff/…`
room surface remains.

| URL | Target |
|---|---|
| `/api/staff/hotel/{slug}/room-management/` (list/create) | `rooms.views.StaffRoomViewSet` |
| `/api/staff/hotel/{slug}/room-management/{room_number}/` (detail/update/delete) | same |
| `/api/staff/hotel/{slug}/room-types/` (list/create) | `hotel.staff_views.StaffRoomTypeViewSet` |
| `/api/staff/hotel/{slug}/room-types/{pk}/` (detail/update/delete) | same |
| `/api/staff/hotel/{slug}/room-types/{pk}/upload-image/` (POST) | `StaffRoomTypeViewSet.upload_image` |
| `/api/staff/hotel/{slug}/room-types/{room_type_id}/rooms/bulk-create/` (POST) | `rooms.views.bulk_create_rooms` |
| `/api/staff/hotel/{slug}/room-images/` (list/create) | `rooms.views.RoomImageViewSet` |
| `/api/staff/hotel/{slug}/room-images/{pk}/` (detail/update/delete) | same |
| `/api/staff/hotel/{slug}/room-images/bulk-upload/` (POST) | `RoomImageViewSet.bulk_upload` |
| `/api/staff/hotel/{slug}/room-images/reorder/` (POST) | `RoomImageViewSet.reorder` |
| `/api/staff/hotel/{slug}/room-images/{pk}/set-cover/` (POST) | `RoomImageViewSet.set_cover` |
| `/api/staff/hotel/{slug}/rooms/checkout/` (POST) | `rooms.views.checkout_rooms` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/start-cleaning/` (POST) | `rooms.views.start_cleaning` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/mark-cleaned/` (POST) | `rooms.views.mark_cleaned` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/inspect/` (POST) | `rooms.views.inspect_room` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/mark-maintenance/` (POST) | `rooms.views.mark_maintenance` |
| `/api/staff/hotel/{slug}/rooms/{room_number}/complete-maintenance/` (POST) | `rooms.views.complete_maintenance` |
| `/api/staff/hotel/{slug}/turnover/rooms/` (GET) | `rooms.views.turnover_rooms` |
| `/api/staff/hotel/{slug}/turnover/stats/` (GET) | `rooms.views.turnover_stats` |

**19 routes, 11 implementing symbols. No other room-related endpoints.**

---

## 6. Files to Delete

| Path | Reason (verified by grep) |
|---|---|
| `rooms/urls.py` | Not `include()`d anywhere. Workspace grep `include\(.rooms` returns one hit: `staff_urls.py` → `rooms.staff_urls` (different file). Entire file is unreachable routing. |

Classes / views / actions to delete (in-place, not file-level):

| Symbol | File | Reason |
|---|---|---|
| `RoomViewSet` (readonly) | `rooms/views.py` L39-68 | Only referenced in `rooms/urls.py` (being deleted). No other grep hits. |
| `RoomTypeViewSet` (legacy readonly) | `rooms/views.py` L112-125 | Never registered. Grep returns only the definition line. |
| `AddGuestToRoomView` | `rooms/views.py` L128-164 | Only referenced in `rooms/urls.py`. Forks guest onboarding outside the booking lifecycle — must not survive a router-mount regression. |
| `RoomByHotelAndNumberView` | `rooms/views.py` L167-174 | Only referenced in `rooms/urls.py`. |
| `checkout_needed` | `rooms/views.py` L339-354 | Only referenced in `rooms/urls.py`. |
| `StaffRoomViewSet` (class B) | `hotel/staff_views.py` L280-353 | Duplicate of canonical A. Only differentiators are QR/PIN, both dead per §2.1. |
| `generate_pin` action | inside class B | Returns HTTP 400 unconditionally. |
| `generate_qr` action | inside class B | Sole caller of `Room.generate_qr_code` / `generate_chat_pin_qr_code` / `generate_booking_qr_for_restaurant`; no product usage. Removed with class B. |

---

## 7. Files to Modify

### 7.1 `rooms/views.py`

Delete the classes and functions listed in §6.

Clean up now-unused module imports at top of file:
- `rest_framework.views.APIView` — only `AddGuestToRoomView` /
  `RoomByHotelAndNumberView` used it.
- `guests.serializers.GuestSerializer` — only `AddGuestToRoomView`.
- `rest_framework.exceptions.PermissionDenied` — unused after deletions.
- `datetime`, `timedelta` — only `AddGuestToRoomView`.
- `.serializers.RoomTypeSerializer` — only `RoomTypeViewSet` consumed it.

Keep (still used by surviving code):
- `guests.models.Guest` — still used in `checkout_rooms` destructive
  branch (`Guest.objects.filter(room=room).delete()`).
- `RoomSerializer` — used by `turnover_rooms`, `checkout_rooms`,
  `checkout_needed` (deleted), and the (unreachable) `RoomByHotel…`
  view. After deletions still used by `turnover_rooms` and
  `checkout_rooms`.
- `RoomStaffSerializer` — used by canonical `StaffRoomViewSet` (A).
- `RoomImageSerializer`, `BulkRoomImageUploadSerializer`,
  `RoomImageReorderSerializer` — used by `RoomImageViewSet`.
- `HasNavPermission`, `HasRoomsNav`, `CanManageRooms` — still used
  across surviving views. Permission wiring is not being altered in
  this phase.

Do **not** touch: `RoomPagination`, `StaffRoomViewSet` (A),
`RoomImageViewSet`, `checkout_rooms`, `bulk_create_rooms`,
`start_cleaning`, `mark_cleaned`, `inspect_room`, `mark_maintenance`,
`complete_maintenance`, `turnover_rooms`, `turnover_stats`, or any
permission class reference.

### 7.2 `hotel/staff_views.py`

Delete class `StaffRoomViewSet` (B) in full, including both
`@action`-decorated methods (`generate_pin`, `generate_qr`).

Remove the `Restaurant` import if and only if no surviving class in the
file references it. (Grep before deletion to confirm. If another class
references `Restaurant`, leave the import.)

Do **not** touch: `StaffRoomTypeViewSet` (entire class, including
`upload_image`), `StaffAccessConfigViewSet`, or any other viewset /
view in this file.

### 7.3 `hotel/urls.py`

**Exact deletions.** Remove these two registrations from `staff_router`:

```python
staff_router.register(
    r'room-types',
    StaffRoomTypeViewSet,
    basename='staff-room-types'
)                                         # DELETE (duplicate mount)

staff_router.register(
    r'rooms',
    StaffRoomViewSet,
    basename='staff-rooms'
)                                         # DELETE (class B being removed)
```

Remove the now-unused imports from the top-of-file
`from .staff_views import (...)` block:
- `StaffRoomTypeViewSet` (still imported from `staff_urls.py` — that
  import is fine and points at the same class; only drop it from
  `hotel/urls.py`).
- `StaffRoomViewSet` (the class itself is being deleted in §7.2, so
  this import would break anyway).

Do **not** touch any other registration in `staff_router`, do not touch
`router` (the main `HotelViewSet` router), do not touch any urlpatterns
outside the `staff/` include.

### 7.4 `staff_urls.py`

**No change required.** Line 43 already imports `StaffRoomViewSet`
from `rooms.views` (canonical A):

```python
from rooms.views import StaffRoomViewSet, RoomImageViewSet
```

And the registration at L140-143 already points at A:

```python
staff_hotel_router.register(
    r'room-management',
    StaffRoomViewSet,
    basename='staff-rooms'
)
```

The `StaffRoomTypeViewSet` import at L23 and registration at L75-78
(→ `hotel.staff_views.StaffRoomTypeViewSet`) also stay — that is the
surviving canonical mount.

### 7.5 `rooms/staff_urls.py`

**No change required.** Every path in this file targets a surviving
function view in `rooms.views`.

### 7.6 Project root `HotelMateBackend/urls.py`

**No change required.** `api/hotel/` still routes to `hotel.urls`, but
after §7.3, `hotel.urls` no longer exposes any rooms / room-types
surface.

---

## 8. Final Endpoint Inventory

All rooms-module endpoints after cleanup. 19 routes, single canonical
path prefix `/api/staff/hotel/{slug}/…`.

```
/api/staff/hotel/{slug}/room-management/                                       [GET,POST]
/api/staff/hotel/{slug}/room-management/{room_number}/                         [GET,PUT,PATCH,DELETE]

/api/staff/hotel/{slug}/room-types/                                            [GET,POST]
/api/staff/hotel/{slug}/room-types/{pk}/                                       [GET,PUT,PATCH,DELETE]
/api/staff/hotel/{slug}/room-types/{pk}/upload-image/                          [POST]
/api/staff/hotel/{slug}/room-types/{room_type_id}/rooms/bulk-create/           [POST]

/api/staff/hotel/{slug}/room-images/                                           [GET,POST]
/api/staff/hotel/{slug}/room-images/{pk}/                                      [GET,PUT,PATCH,DELETE]
/api/staff/hotel/{slug}/room-images/bulk-upload/                               [POST]
/api/staff/hotel/{slug}/room-images/reorder/                                   [POST]
/api/staff/hotel/{slug}/room-images/{pk}/set-cover/                            [POST]

/api/staff/hotel/{slug}/rooms/checkout/                                        [POST]
/api/staff/hotel/{slug}/rooms/{room_number}/start-cleaning/                    [POST]
/api/staff/hotel/{slug}/rooms/{room_number}/mark-cleaned/                      [POST]
/api/staff/hotel/{slug}/rooms/{room_number}/inspect/                           [POST]
/api/staff/hotel/{slug}/rooms/{room_number}/mark-maintenance/                  [POST]
/api/staff/hotel/{slug}/rooms/{room_number}/complete-maintenance/              [POST]

/api/staff/hotel/{slug}/turnover/rooms/                                        [GET]
/api/staff/hotel/{slug}/turnover/stats/                                        [GET]
```

Endpoints that become **HTTP 404** after cleanup (gone on purpose):

```
/api/hotel/staff/rooms/
/api/hotel/staff/rooms/{pk}/
/api/hotel/staff/rooms/{pk}/generate_pin/
/api/hotel/staff/rooms/{pk}/generate_qr/
/api/hotel/staff/room-types/
/api/hotel/staff/room-types/{pk}/
/api/hotel/staff/room-types/{pk}/upload-image/
```

(The legacy `rooms/urls.py` paths — `rooms/`,
`{hotel}/rooms/{num}/`, `{hotel}/rooms/{num}/add-guest/`,
`{slug}/checkout/`, `{slug}/checkout-needed/` — were already 404
before cleanup; the file is deleted for hygiene.)

---

## 9. Validation Checklist

Every item is pass/fail checkable against code after the cleanup
commit lands.

- [ ] **No duplicate classes.** `grep 'class StaffRoomViewSet' rooms/
  hotel/` returns exactly one hit (`rooms/views.py`).
  `grep 'class StaffRoomTypeViewSet' rooms/ hotel/` returns exactly
  one hit (`hotel/staff_views.py`).
- [ ] **No duplicate registrations.** `grep "register(r'rooms'"
  hotel/urls.py` → zero. `grep "register(r'room-types'"
  hotel/urls.py` → zero. `grep "register(r'room-management'"
  staff_urls.py` → exactly one.
- [ ] **No dead files.** `rooms/urls.py` does not exist. `grep
  'include.*rooms\.urls'` across repo → zero.
- [ ] **No dead classes.** `grep` for each of `RoomViewSet`,
  `RoomTypeViewSet` (legacy readonly), `AddGuestToRoomView`,
  `RoomByHotelAndNumberView`, `checkout_needed` across the repo →
  zero matches outside migrations/docs.
- [ ] **No dead actions.** `grep 'def generate_pin'` across repo → zero.
  `grep 'def generate_qr\b' hotel/ rooms/` → zero. (Unrelated
  `generate_qr_*` helpers on `StaffRegistrationCode`, `Tournament`,
  `HotelQR` remain; different models, out of scope.)
- [ ] **No hidden routes.** `python manage.py show_urls | grep -E
  'rooms|room-'` lists exactly the 19 endpoints in §8 and nothing
  else. `resolve('/api/hotel/staff/rooms/')` raises `Resolver404`.
  `resolve('/api/hotel/staff/room-types/')` raises `Resolver404`.
- [ ] **Single canonical path.** Every endpoint in §8 sits under
  `/api/staff/hotel/{slug}/…`. Zero under `/api/hotel/staff/…`.
- [ ] **Behaviour preserved on A.** `reverse(
  'staff-rooms-detail', kwargs={'hotel_slug': '…', 'room_number':
  '101'})` resolves; pagination still applied to list; search filter
  still works; same serializer (`RoomStaffSerializer`).
- [ ] **Permissions unchanged.** `git diff staff/permissions.py` is
  empty for this commit. `get_permissions` body of A is byte-identical
  to pre-cleanup.
- [ ] **Imports clean.** `python -c "import rooms.views"` and `python
  -c "import hotel.staff_views"` both succeed. `python manage.py
  check` reports zero issues.

---

## 10. Go / No-Go

**Is the system ready for Phase 6B.1? NO — until this cleanup lands.**
**Is the cleanup itself ready to execute? YES.**

Cleanup is safe to execute immediately because:
- All dead symbols are verified dead by grep (single owner was
  `rooms/urls.py`, which itself is unreachable).
- QR/PIN actions are confirmed unused in product — no consumer exists
  for `Room.generate_qr_code`, `generate_chat_pin_qr_code`, or
  `generate_booking_qr_for_restaurant` outside class B itself.
- Canonical class A already has every data-contract attribute required
  (§3 all checked). Zero additions needed.
- Legacy `/api/hotel/staff/…` rooms surface has zero backend consumers;
  any frontend caller is already required to migrate independently
  (the `/api/staff/hotel/{slug}/…` surface is the Phase-1 zone).
- Permission wiring is not touched. RBAC hazards identified in the
  Phase-6B audit remain and are Phase-6B.1's job.

No-Go gates (would block Phase 6B.1 start):
- Any item in §9 failing.
- A live `/api/hotel/staff/rooms/…` or `/api/hotel/staff/room-types/…`
  mount still resolving.
- Any grep for deleted symbols returning live-code hits.
- Any import in `rooms/views.py` or `hotel/staff_views.py` becoming
  unresolved at `manage.py check`.

Once §9 is fully green, Phase 6B.1 (capability model rollout) may
begin against a single, auditable surface.
