# RBAC Wave 1 Audit — guests + hotel_info

Scope: backend apps `guests` and `hotel_info` only. No code changes.

URL mounting reference (from [staff_urls.py](staff_urls.py#L48-L65) and [HotelMateBackend/urls.py](HotelMateBackend/urls.py#L46-L48)):

- `guests` and `hotel_info` are listed in `STAFF_APPS`, mounted at
  `/api/staff/hotel/<hotel_slug>/{app}/...` via `include(f'{app}.urls')`.
- Neither app is mounted under `guest_urls.py` (guest zone) or
  `public_urls.py` (public zone). All endpoints below are reached via the
  staff zone only.

---

## 1. Endpoint inventory

### guests app

Source: [guests/urls.py](guests/urls.py#L1-L12), [guests/views.py](guests/views.py#L1-L27)

| Endpoint | Method | View | Current permissions | Staff/guest/public | Risk |
|---|---|---|---|---|---|
| `/api/staff/hotel/<hotel_slug>/guests/<hotel_slug>/guests/` | GET | `GuestViewSet.list` | `IsAuthenticated`, `HasNavPermission('rooms')`, `IsStaffMember`, `IsSameHotel` | Staff | URL has double `<hotel_slug>` (staff wrapper + app urls) — already enforced same-hotel + nav. Low. |
| `/api/staff/hotel/<hotel_slug>/guests/<hotel_slug>/guests/<pk>/` | GET | `GuestViewSet.retrieve` | same as above | Staff | `get_object()` filters by `hotel_slug` — cross-hotel risk mitigated. Low. |
| `/api/staff/hotel/<hotel_slug>/guests/<hotel_slug>/guests/<pk>/` | PUT | `GuestViewSet.update` | same as above | Staff | **Write endpoint with no capability check** — only nav + tier-agnostic. Medium. |

Note: `GuestViewSet` is a `ModelViewSet` but `urls.py` only wires `list`, `retrieve`, and `update`. `create`/`partial_update`/`destroy` are not routed.

### hotel_info app

Source: [hotel_info/urls.py](hotel_info/urls.py#L1-L21), [hotel_info/views.py](hotel_info/views.py#L1-L195)

Mounted at `/api/staff/hotel/<hotel_slug>/hotel_info/`.

| Endpoint | Method | View | Current permissions | Staff/guest/public | Risk |
|---|---|---|---|---|---|
| `.../hotel_info/hotelinfo/` | GET | `HotelInfoViewSet.list` | `IsAuthenticatedOrReadOnly` | "Public/anon read" allowed | **Anonymous reads allowed even though mounted under `/api/staff/`. No hotel scoping on queryset (returns all hotels' info)** unless `?hotel__slug=` filter passed. High (info disclosure). |
| `.../hotel_info/hotelinfo/<pk>/` | GET | `HotelInfoViewSet.retrieve` | `IsAuthenticatedOrReadOnly` | Same | Anonymous read of any hotel's info row by PK. High. |
| `.../hotel_info/hotelinfo/` | POST | `HotelInfoViewSet.create` | `IsAuthenticated, HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel` | Staff | `IsSameHotel` reads `view.kwargs['hotel_slug']` — only effective if URL carries one. URL is `/hotel_info/hotelinfo/` (no slug in router path), so `IsSameHotel.has_permission` returns False → effectively only Django superusers can create via this route. Medium-High (broken). |
| `.../hotel_info/hotelinfo/<pk>/` | PUT/PATCH/DELETE | `HotelInfoViewSet.update/destroy` | same | Staff | Same `IsSameHotel` issue (no `hotel_slug` in URL kwargs). Plus no per-object hotel check → cross-hotel write risk if `IsSameHotel` is bypassed. **High**. |
| `.../hotel_info/categories/` | GET | `HotelInfoCategoryViewSet.list` | `AllowAny` (via `get_permissions`) | Public | Categories are global (no hotel FK). Acceptable as public taxonomy. Low. |
| `.../hotel_info/categories/<pk>/` | GET | `HotelInfoCategoryViewSet.retrieve` | `AllowAny` | Public | Low. |
| `.../hotel_info/categories/` | POST | `HotelInfoCategoryViewSet.create` | `IsAuthenticated, HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel` | Staff | Same `IsSameHotel` URL-kwarg gap as above. **Medium-High (broken / unreachable for staff except superusers)**. Side-effect: also auto-creates `CategoryQRCode` for the requesting staff's hotel (good — uses `staff.hotel`, not request data). |
| `.../hotel_info/categories/<pk>/` | PUT/PATCH/DELETE | category mutations | same | Staff | Same gap. Categories are global rows (no hotel FK), so a successful mutation here affects every hotel. **High** if `IsSameHotel` is later loosened. |
| `.../hotel_info/categories/<hotel_slug>/categories/` (custom action `by_hotel`) | GET | `HotelInfoCategoryViewSet.by_hotel` | `AllowAny` (safe-method bypass) | Public | Returns categories filtered by hotel. Low. |
| `.../hotel_info/hotelinfo/create/` | POST | `HotelInfoCreateView` (CreateAPIView) | `IsAuthenticated, HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel` (static `permission_classes`) | Staff | Same `IsSameHotel` URL-kwarg gap (URL has no `hotel_slug`). **Hotel taken from `request.data['hotel_slug']`** in serializer — caller picks any hotel. Cross-hotel write risk. **High**. |
| `.../hotel_info/category_qr/` | GET | `CategoryQRView.get` | `IsAuthenticated` | Staff (any auth user) | No staff/hotel check; reads QR by `hotel_slug` + `category_slug` from query params. Cross-hotel read possible. Medium (QRs are non-secret URLs but still). |
| `.../hotel_info/category_qr/` | POST | `CategoryQRView.post` | `IsAuthenticated` + inline loop of `HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel` | Staff | Inline `IsSameHotel` instantiation has no `hotel_slug` in URL kwargs → **`IsSameHotel.has_permission` returns False for all staff**, so only Django superusers pass. Effectively broken for normal staff. Hotel is correctly taken from `staff.hotel` (good). Medium (broken access). |
| `.../hotel_info/category_qr/download_all/` | GET | `download_all_qrs` | `IsAuthenticated, HasHotelInfoNav, IsStaffMember` | Staff | **No `IsSameHotel` and no validation that `hotel_slug` query param matches `staff.hotel.slug`**. Any staff in any hotel can list QR records of any other hotel by passing its slug. Medium (cross-hotel disclosure). |

---

## 2. Current protection

### guests

[guests/views.py](guests/views.py#L11-L18):

```python
class GuestViewSet(viewsets.ModelViewSet):
    serializer_class = GuestSerializer

    def get_permissions(self):
        base = [permissions.IsAuthenticated(), HasNavPermission('rooms'),
                IsStaffMember(), IsSameHotel()]
        return base
```

Inline checks:
- [guests/views.py](guests/views.py#L20-L26) `get_queryset` filters by `hotel__slug=hotel_slug`.
- [guests/views.py](guests/views.py#L24-L26) `get_object` likewise filters.
- No capability check, no per-method differentiation, no `update`-specific authority class.

### hotel_info

[hotel_info/views.py](hotel_info/views.py#L40-L48) `HotelInfoViewSet.get_permissions`:
- Safe methods: `IsAuthenticatedOrReadOnly` (i.e. anonymous read allowed).
- Unsafe methods: `IsAuthenticated, HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel`.

[hotel_info/views.py](hotel_info/views.py#L72-L82) `HotelInfoCategoryViewSet.get_permissions`:
- Safe methods: `AllowAny`.
- Unsafe methods: same staff stack as above.

[hotel_info/views.py](hotel_info/views.py#L107-L108) `HotelInfoCreateView`:
- Static `permission_classes = [IsAuthenticated, HasHotelInfoNav, IsStaffMember, IsSameHotel, CanConfigureHotel]`.

[hotel_info/views.py](hotel_info/views.py#L128-L129) `CategoryQRView`:
- Static `permission_classes = [IsAuthenticated]`.
- Inline manual loop in `post` ([hotel_info/views.py](hotel_info/views.py#L153-L157)) instantiates `HasHotelInfoNav(), IsStaffMember(), IsSameHotel(), CanConfigureHotel()` and raises `PermissionDenied`.

[hotel_info/views.py](hotel_info/views.py#L20-L21) `download_all_qrs`:
- `@permission_classes([IsAuthenticated, HasHotelInfoNav, IsStaffMember])`.

No serializer-level hotel scope or per-object permissions on any view.

---

## 3. Gaps

### guests

- **Write without capability check**: PUT on `GuestViewSet.update` is gated only by `HasNavPermission('rooms')` (a *visibility* gate per [staff/permissions.py](staff/permissions.py#L235-L240) — explicitly "NOT mutation authority") + `IsStaffMember` + `IsSameHotel`. Per the contract this is exactly the "nav-only security on writes" pattern that must be replaced with an action-level capability.
- **No tier/role/capability gate** for guest record updates, deletions, or any guest workflow action.
- **Nav slug mismatch**: Module is gated by `rooms` nav, but conceptually guests are a distinct domain; tying it to `rooms` couples the gate to an unrelated module's visibility.
- **No serializer hotel-scope guard**: `hotel` is a writable field on `GuestSerializer` (see [guests/serializers.py](guests/serializers.py#L26-L42)). On PUT a same-hotel staff could try to move a guest to another hotel; only the queryset filter prevents it (and only because `update` doesn't change `kwargs['hotel_slug']`). Cross-hotel risk if a future route lacks the slug.
- **Public/guest-zone**: none expected. Guest data is staff-only — current routing is correct.

### hotel_info

- **Anonymous reads on staff-zone endpoints**: `HotelInfoViewSet.list/retrieve` allow unauthenticated reads via `IsAuthenticatedOrReadOnly`, although mounted under `/api/staff/`. The queryset is unscoped (`HotelInfo.objects.all()`); only the optional `?hotel__slug=` query filter narrows it. **Anyone can list every hotel's info content.** This contradicts the contract: staff zone must require auth + staff + same-hotel.
- **`IsSameHotel` is broken for these endpoints**: `IsSameHotel.has_permission` reads `view.kwargs.get('hotel_slug')` ([staff_chat/permissions.py](staff_chat/permissions.py#L57-L66)). The URL paths `/hotel_info/hotelinfo/`, `/hotel_info/categories/`, `/hotel_info/hotelinfo/create/`, `/hotel_info/category_qr/` carry **no `hotel_slug` URL kwarg**, so the check returns False → only Django superusers pass. Staff-admin / super-staff-admin write attempts fail closed today even though they should be allowed.
- **`HotelInfoCreateView` trusts `request.data['hotel_slug']`**: serializer pulls hotel from request body ([hotel_info/serializers.py](hotel_info/serializers.py#L96-L102)) — combined with the broken `IsSameHotel` above, only superusers can create, but if `IsSameHotel` is later "fixed" to fall back to body, the body field becomes a cross-hotel write vector.
- **`download_all_qrs` lacks `IsSameHotel` and lacks body-vs-staff hotel match**: any authenticated staff with the `hotel_info` nav can fetch QR records of any hotel by passing its slug ([hotel_info/views.py](hotel_info/views.py#L20-L36)). Cross-hotel disclosure.
- **`CategoryQRView.get` has only `IsAuthenticated`**: not staff-gated, not hotel-scoped. Authenticated guests (any user with a token) can read QR URLs.
- **`HotelInfoCategory` mutations have no scoping by design** because the model is global (no hotel FK). Today only superusers can mutate (because of the `IsSameHotel` break); when fixed, mutations to global rows must require a higher tier than per-hotel staff_admin (rows affect every hotel). Currently `CanConfigureHotel` (super_staff_admin+) is correct *level* but wrong *boundary* — a Hotel A super_staff_admin would still be editing categories used by Hotel B.
- **Nav-only on reads**: `HotelInfoViewSet` reads aren't even nav-gated (anonymous allowed).
- **No capability checks anywhere**: every mutation uses `CanConfigureHotel` (tier check), which is the legacy pattern the RBAC contract is migrating away from for module-specific mutations.
- **Public/guest endpoints expected and safe**: the QR codes themselves point at `https://hotelsmates.com/hotel_info/<hotel_slug>/<category_slug>` ([hotel_info/models.py](hotel_info/models.py#L52)) and `https://hotelsmates.com/good_to_know/...` ([hotel_info/models.py](hotel_info/models.py#L130)). Those are frontend routes, not backend endpoints, and are not served by this app. There is **no current public/guest-zone backend endpoint serving hotel info to guests** — meaning the guest-facing landing page either uses the public zone (hotel public-page builder) or the QR points at a frontend page that calls another API. The currently anonymous-readable `HotelInfoViewSet` GETs may have been the de-facto guest endpoint, in which case they need to move out of the staff zone.

---

## 4. Proposed canonical RBAC modules/actions  (PROPOSED)

Based on the actual endpoints above, the suggested shape becomes:

```txt
guest:
  read              # GuestViewSet.list, .retrieve
  update            # GuestViewSet.update (PUT)
  # NOT proposed (no current endpoint):
  #   create        — guests are created by booking flow / check-in, not this viewset
  #   delete        — no DELETE route is wired
  #   checkout      — handled by room_bookings/rooms apps, not guests app

hotel_info:
  entry_read           # HotelInfoViewSet GETs (per-hotel scoped)
  entry_create         # HotelInfoViewSet POST + HotelInfoCreateView
  entry_update         # HotelInfoViewSet PUT/PATCH
  entry_delete         # HotelInfoViewSet DELETE
  category_read        # HotelInfoCategoryViewSet GETs (may stay public)
  category_manage      # HotelInfoCategoryViewSet POST/PUT/PATCH/DELETE
                       #   — global rows; should require platform-level tier
  qr_generate          # CategoryQRView.post (regenerate QR for staff's hotel)
  qr_read              # CategoryQRView.get + download_all_qrs (per-hotel)
```

Deviations from the suggested shape in the prompt:

- `guest:delete`, `guest:checkout` are dropped — no current endpoints back them.
- `hotel_info:qr_download` is renamed to `qr_read` since both `category_qr/` GET and `download_all_qrs` are reads of an existing QR; there is no separate "download" mutation distinct from "read".
- `hotel_info:category_manage` should be enforced at platform-tier (super_user) given categories are global rows shared across all hotels — recommend gating it via `IsDjangoSuperUser` plus the capability slug, not `CanConfigureHotel`.

---

## 5. Implementation plan

### 5.1 `staff/capability_catalog.py` — additions

Add to `CANONICAL_CAPABILITIES` and assign to presets:

```python
# --- Guests (Wave 1) ---
GUEST_RECORD_READ   = 'guest.record.read'
GUEST_RECORD_UPDATE = 'guest.record.update'

# --- Hotel info (Wave 1) ---
HOTEL_INFO_MODULE_VIEW    = 'hotel_info.module.view'
HOTEL_INFO_ENTRY_READ     = 'hotel_info.entry.read'
HOTEL_INFO_ENTRY_CREATE   = 'hotel_info.entry.create'
HOTEL_INFO_ENTRY_UPDATE   = 'hotel_info.entry.update'
HOTEL_INFO_ENTRY_DELETE   = 'hotel_info.entry.delete'
HOTEL_INFO_CATEGORY_READ  = 'hotel_info.category.read'    # may stay AllowAny in views
HOTEL_INFO_CATEGORY_MANAGE = 'hotel_info.category.manage' # super_user only
HOTEL_INFO_QR_READ        = 'hotel_info.qr.read'
HOTEL_INFO_QR_GENERATE    = 'hotel_info.qr.generate'
```

Assign:
- `TIER_DEFAULT_CAPABILITIES['regular_staff']` → none of the above (front-desk role preset can grant `guest.record.read`).
- `TIER_DEFAULT_CAPABILITIES['staff_admin']` and `'super_staff_admin'` → `HOTEL_INFO_MODULE_VIEW`, `HOTEL_INFO_ENTRY_READ`, `HOTEL_INFO_QR_READ`, `GUEST_RECORD_READ`.
- `'super_staff_admin'` → all `HOTEL_INFO_ENTRY_*` writes, `HOTEL_INFO_QR_GENERATE`, `GUEST_RECORD_UPDATE`.
- `HOTEL_INFO_CATEGORY_MANAGE` → not in any preset; granted only to `super_user` (Django superuser bypass already covers it).
- `ROLE_PRESET_CAPABILITIES['receptionist']` → add `GUEST_RECORD_READ`, `GUEST_RECORD_UPDATE` (front desk maintains guest profiles).

### 5.2 `staff/module_policy.py` — additions

Register two modules:

```python
'guest': {
    'view_capability': GUEST_RECORD_READ,    # no separate module slug today
    'read_capability': GUEST_RECORD_READ,
    'actions': {
        'update': GUEST_RECORD_UPDATE,
    },
},
'hotel_info': {
    'view_capability': HOTEL_INFO_MODULE_VIEW,
    'read_capability': HOTEL_INFO_ENTRY_READ,
    'actions': {
        'entry_create':    HOTEL_INFO_ENTRY_CREATE,
        'entry_update':    HOTEL_INFO_ENTRY_UPDATE,
        'entry_delete':    HOTEL_INFO_ENTRY_DELETE,
        'category_manage': HOTEL_INFO_CATEGORY_MANAGE,
        'qr_generate':     HOTEL_INFO_QR_GENERATE,
        'qr_read':         HOTEL_INFO_QR_READ,
    },
},
```

Also add the import block at the top of the file mirroring the existing pattern.

### 5.3 New permission classes

In [staff/permissions.py](staff/permissions.py):

```python
class CanReadGuest(HasCapability):
    required_capability = GUEST_RECORD_READ
    safe_methods_bypass = False  # this gates GET specifically

class CanUpdateGuest(HasCapability):
    required_capability = GUEST_RECORD_UPDATE
    # default safe_methods_bypass=True is fine — class only fires on PUT/PATCH

class HasHotelInfoModule(HasCapability):
    required_capability = HOTEL_INFO_MODULE_VIEW
    safe_methods_bypass = False

class CanReadHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_READ
    safe_methods_bypass = False

class CanCreateHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_CREATE

class CanUpdateHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_UPDATE

class CanDeleteHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_DELETE

class CanManageHotelInfoCategory(HasCapability):
    required_capability = HOTEL_INFO_CATEGORY_MANAGE

class CanGenerateHotelInfoQR(HasCapability):
    required_capability = HOTEL_INFO_QR_GENERATE

class CanReadHotelInfoQR(HasCapability):
    required_capability = HOTEL_INFO_QR_READ
    safe_methods_bypass = False
```

### 5.4 View `permission_classes` updates

[guests/views.py](guests/views.py) — `GuestViewSet`:

```python
def get_permissions(self):
    base = [IsAuthenticated(), IsStaffMember(), IsSameHotel(), CanReadGuest()]
    if self.request.method in ('PUT', 'PATCH'):
        base.append(CanUpdateGuest())
    return base
```

Drop `HasNavPermission('rooms')` — replace with capability gate. Optionally add a `guest` nav slug to [staff/nav_catalog.py](staff/nav_catalog.py) if a left-nav entry is desired, but it's not required for security.

[hotel_info/views.py](hotel_info/views.py):

- `HotelInfoViewSet.get_permissions`:
  - Safe methods: `[IsAuthenticated(), IsStaffMember(), IsSameHotel(), CanReadHotelInfo()]` — **stop allowing anonymous reads** (or split into a separate `public_urls.py` route if guests should keep reading).
  - Unsafe: `[IsAuthenticated(), IsStaffMember(), IsSameHotel(), HasHotelInfoModule()]` plus the matching `CanCreate/Update/DeleteHotelInfo` per method.
  - Override `get_queryset()` to filter by `request.user.staff_profile.hotel` (don't trust `?hotel__slug=`).
- `HotelInfoCategoryViewSet`:
  - Safe methods: keep `AllowAny` (taxonomy is acceptable to expose) **or** require `IsAuthenticated + CanReadHotelInfo` if categories should be staff-only.
  - Unsafe: replace stack with `[IsAuthenticated(), IsStaffMember(), CanManageHotelInfoCategory()]`. Drop `IsSameHotel` (model has no hotel FK); rely on the capability being super-user-only.
- `HotelInfoCreateView`:
  - Replace `permission_classes` with `[IsAuthenticated, IsStaffMember, IsSameHotel, CanCreateHotelInfo]`. URL must be re-mounted with a `<hotel_slug>` kwarg (currently `/hotelinfo/create/`) **or** drop `IsSameHotel` and have the view enforce `info.hotel == request.user.staff_profile.hotel` — see §5.5.
- `CategoryQRView`:
  - Static `permission_classes = [IsAuthenticated, IsStaffMember]`.
  - In `get` add `CanReadHotelInfoQR` and verify `hotel_slug` query param matches `staff.hotel.slug`.
  - In `post` replace inline loop with `CanGenerateHotelInfoQR` + same staff-hotel match.
- `download_all_qrs`:
  - Replace decorator: `@permission_classes([IsAuthenticated, IsStaffMember, CanReadHotelInfoQR])`.
  - Add inline check: reject if `hotel_slug` query param ≠ `request.user.staff_profile.hotel.slug` (or just ignore the param and use staff's hotel).

### 5.5 Serializer / queryset hotel-scope hardening

- [hotel_info/views.py](hotel_info/views.py#L42-L43): `HotelInfoViewSet.queryset = HotelInfo.objects.all()` → replace with a `get_queryset` that filters by `staff.hotel` for staff requests.
- [hotel_info/views.py](hotel_info/views.py#L116-L121): `HotelInfoCreateView.create` should ignore `request.data['hotel_slug']` and inject `staff.hotel.slug` server-side before calling the serializer (or remove `hotel_slug` from `HotelInfoCreateSerializer.fields`).
- [hotel_info/serializers.py](hotel_info/serializers.py#L142-L148): `HotelInfoUpdateSerializer.update` accepts a writable `hotel_slug` that re-parents an entry to another hotel. **Remove `hotel_slug` from `HotelInfoUpdateSerializer.fields`** so updates can't move rows cross-hotel.
- [guests/serializers.py](guests/serializers.py#L25-L48): make `hotel` and `room` read-only on update (remove from writable fields), or override `update` to forbid changes to those FKs.
- [guests/views.py](guests/views.py#L20-L26): `get_object` uses bare `Guest.objects.get(...)` — wrap in `get_object_or_404` for proper 404 handling and to engage DRF's permission-denied machinery.

### 5.6 URL routing fix (prerequisite for `IsSameHotel`)

Today the staff wrapper produces paths like
`/api/staff/hotel/<hotel_slug>/hotel_info/hotelinfo/...` where the **outer** `hotel_slug` is in `view.kwargs` (because the `include()` carries it down). Verify with a request — if the outer slug is correctly available in `view.kwargs`, no change is needed. If not (e.g. because the `include` strips it before reaching the router), `hotel_info/urls.py` must be re-shaped to mount the router under `<str:hotel_slug>/...`.

Same applies to the doubled `<hotel_slug>` in [guests/urls.py](guests/urls.py#L9-L10): `path('<str:hotel_slug>/guests/...')` is mounted under `hotel/<str:hotel_slug>/guests/`, so the canonical request URL is `/api/staff/hotel/<a>/guests/<b>/guests/...` with two slugs. The view uses the **inner** one. Recommendation: drop the inner `<str:hotel_slug>/` prefix from `guests/urls.py` and rely on the wrapper's outer slug.

---

## 6. Minimal tests needed

### guests

1. Unauthenticated GET `/api/staff/hotel/<slug>/guests/<slug>/guests/` → 401.
2. Staff from a different hotel GET → 403 (`IsSameHotel`).
3. Staff with `IsStaffMember` but **without** `GUEST_RECORD_UPDATE` PUT a guest record → 403.
4. Staff with `GUEST_RECORD_UPDATE` PUT a same-hotel guest → 200.
5. Staff with `GUEST_RECORD_UPDATE` PUT trying to change `hotel` field → field is read-only (200 with no change) or 400.

### hotel_info

1. Unauthenticated GET `/api/staff/hotel/<slug>/hotel_info/hotelinfo/` → 401 (after closing anonymous read).
2. Staff from another hotel GET → 403.
3. Staff with no `HOTEL_INFO_ENTRY_CREATE` POST `/hotelinfo/create/` → 403.
4. Staff with `HOTEL_INFO_ENTRY_CREATE` POST against own hotel → 201.
5. Staff with `HOTEL_INFO_ENTRY_CREATE` POST with body `hotel_slug` of another hotel → entry created in **own** hotel (server-side override).
6. Authenticated non-staff GET `/category_qr/?hotel_slug=other&category_slug=x` → 403 (after `IsStaffMember` added).
7. Staff with `HOTEL_INFO_QR_READ` GET `download_all/?hotel_slug=other` → 403 / scoped to own hotel.
8. Non-superuser staff POST `/categories/` (create category) → 403 (`CanManageHotelInfoCategory`).
9. Public GET `/categories/` → 200 (if the AllowAny decision is kept).
10. Superuser POST `/categories/` → 201.
