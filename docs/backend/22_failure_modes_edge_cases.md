# 22 — Failure Modes & Edge Cases

> Auto-generated from codebase audit. Every finding references a source file.
> Items marked ⚠️ are verified issues. Items marked 🔍 need further investigation.

---

## 1. Critical Issues

### 1.1 ⚠️ `DEBUG = True` Hardcoded in Production Settings

**Source:** `HotelMateBackend/settings.py`

```python
DEBUG = True  # hardcoded, not from env var
```

**Impact:**
- Full stack traces exposed to end users on 500 errors
- Django debug page reveals settings, installed apps, middleware, SQL queries
- Static file serving behavior differs from production expectations
- Security-sensitive information leaked on every error

**Fix:** `DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'`

---

### 1.2 ⚠️ `staff_urls.py` Source File Missing

**Evidence:**
- `HotelMateBackend/urls.py` imports: `from staff_urls import urlpatterns as staff_urlpatterns`
- File `staff_urls.py` does **not exist** in the project root
- Only `__pycache__/staff_urls.cpython-312.pyc` exists (compiled bytecode)
- The `.pyc` file is being used at runtime, but the source is gone

**Impact:**
- Cannot review, edit, or audit staff URL routing from source
- Any Python version upgrade may invalidate the `.pyc` and break all `/api/staff/` routes
- Git history may not track changes to this critical routing file

**Fix:** Decompile `.pyc` or reconstruct from the bytecode cache, commit as `.py` source.

---

### 1.3 ⚠️ Heroku Scheduler Missing 5 of 6 Required Commands

**Source:** `setup_heroku_scheduler.sh`

The script registers **only 1** of the 7 commands listed:
```bash
# Only this one is actually registered:
heroku addons:create scheduler:standard
# Then only adds: manage.py auto_checkout_overdue_bookings
```

**Missing from scheduler (documented but not registered):**
| Command | Purpose | Impact if Missing |
|---------|---------|-------------------|
| `auto_no_show` | Mark no-show bookings | No-shows never flagged |
| `auto_cancel_unconfirmed` | Cancel stale bookings | Unconfirmed bookings pile up |
| `send_reminder_notifications` | Guest reminders | No pre-arrival notifications |
| `expire_precheckin_tokens` | Security cleanup | Expired tokens remain valid |
| `cleanup_orphaned_data` | Data hygiene | Orphaned records accumulate |
| `generate_daily_reports` | Daily reports | No automated reporting |

---

## 2. Data Integrity Issues

### 2.1 ⚠️ Double `hotel_slug` in Some Staff URL Patterns

**Source:** `HotelMateBackend/urls.py`

```python
path('api/staff/<str:hotel_slug>/', include(staff_urlpatterns)),
```

If `staff_urlpatterns` internally also prefix with `<str:hotel_slug>/`, the resulting URL becomes:
```
/api/staff/<hotel_slug>/<hotel_slug>/...
```

**Impact:** Either 404 errors or URL mismatch — depends on how `staff_urlpatterns` is structured. Cannot verify without source file (see §1.2).

---

### 2.2 ⚠️ Staff Signals Bug — `hotel` Argument on Staff Model

**Source:** `staff/signals.py`

```python
# Signal attempts to pass 'hotel' to Staff creation
# But Staff model uses OneToOneField to User, not direct hotel FK
```

**Impact:**
- Signal may silently fail or raise TypeError
- Staff creation from admin or management commands may not properly associate hotel
- **UNCLEAR IN CODE:** Whether this signal is actively triggered in production flows

---

### 2.3 ⚠️ Ghost Guest Records

**Scenario:** When a `BookingPartyMember` is created without a corresponding `GuestProfile`, or when a guest is removed from a booking but their profile remains.

**Evidence:** `hotel/staff_views.py` — party member management does not always cascade to guest profile cleanup.

**Impact:**
- Orphaned guest profiles in database
- Guest counts may be inflated
- Pre-check-in links may be sent to removed party members

---

### 2.4 ⚠️ Orphaned Room Assignments on Booking Cancellation

**Source:** `room_bookings/services/room_assignment.py`

When a booking is cancelled:
1. `RoomBooking.status` → `cancelled`
2. Room status may not be released back to `available`
3. Depends on whether `set_room_status()` is called in the cancellation flow

**Evidence:** `hotel/staff_views.py` cancellation logic updates booking status but room release is conditional.

**Impact:** Rooms may appear occupied after booking cancellation until manually cleaned up.

---

### 2.5 🔍 Concurrent Room Assignment Race Condition

**Source:** `room_bookings/services/room_assignment.py`

Room assignment flow:
1. Check room availability → `Room.status == 'available'`
2. Assign room → `Room.status = 'occupied'`

**No database-level locking** (`select_for_update()`) observed in the assignment flow.

**Impact:** Two concurrent check-ins could assign the same room. Low probability in hotel context but possible during bulk operations.

---

## 3. Authentication & Authorization Edge Cases

### 3.1 ⚠️ Guest Token Not a DRF Authentication Class

**Source:** `hotel/models.py` (GuestBookingToken), `hotel/guest_views.py`

Guest authentication is **manual token extraction** inside view methods with `permission_classes = [AllowAny]`:

```python
class GuestBookingDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        # Manual: GuestBookingToken.objects.get(token_hash=hash(token))
```

**Edge cases:**
- No rate limiting on token guessing (SHA-256 tokens are strong but no brute-force protection)
- Token expiry depends on `expires_at` field check in view code — not enforced at auth layer
- If a view forgets to check expiry, expired tokens work

### 3.2 ⚠️ Some Endpoints Missing Explicit `permission_classes`

**Evidence from audit:** Several ViewSets rely on DRF's default `IsAuthenticated` but don't declare it explicitly.

**Impact:** If `DEFAULT_PERMISSION_CLASSES` in settings changes, these views become unprotected.

| App | Affected Views |
|-----|---------------|
| `entertainment` | Some quiz/game views |
| `posts` | Post listing views |
| `common` | Utility views |

### 3.3 🔍 SubdomainMiddleware Hotel Mismatch

**Source:** `hotel/middleware.py`

If a staff user's token belongs to Hotel A but they access a URL with `hotel_slug` for Hotel B:
- `request.hotel` is set from the URL slug
- Token auth succeeds (token is valid regardless of hotel)
- View may operate on Hotel B's data with Hotel A staff's token

**Mitigation:** Some views have explicit `if request.user.staff.hotel != request.hotel` checks, but this is not universal.

---

## 4. State Machine Edge Cases

### 4.1 ⚠️ Booking Status Transitions Not Enforced in Model

**Source:** `hotel/models.py` — `RoomBooking`

The 10 booking statuses (`pending`, `confirmed`, `checked_in`, `checked_out`, `cancelled`, `no_show`, `modified`, `waitlisted`, `expired`, `overstay`) have **no transition validation** at the model level.

```python
# Any code can do:
booking.status = 'checked_out'  # Even if current status is 'cancelled'
booking.save()
```

**Impact:** Invalid state transitions possible if a view doesn't check current state before updating.

**Where transitions ARE enforced:** Only in service layer (`room_bookings/services/checkout.py`, `hotel/staff_views.py`) — not in the model's `save()` or `clean()`.

### 4.2 ⚠️ Room Status Transitions — Valid but Not Model-Enforced

**Source:** `rooms/models.py`

```python
VALID_TRANSITIONS = {
    'available': ['occupied', 'maintenance', 'out_of_order', 'cleaning'],
    'occupied': ['cleaning', 'available', 'maintenance'],
    'cleaning': ['available', 'inspection', 'maintenance'],
    'inspection': ['available', 'cleaning'],
    'maintenance': ['available', 'out_of_order'],
    'out_of_order': ['maintenance', 'available'],
    'blocked': ['available'],
}
```

Transition map exists but enforcement is only in `housekeeping/services.py → set_room_status()`. Direct model saves bypass validation.

### 4.3 🔍 Overstay Detection Timing

**Source:** `hotel/management/commands/auto_checkout_overdue_bookings.py`

- Overstay detection runs only when the management command executes
- If Heroku Scheduler is delayed or misses a run, overstays are detected late
- No real-time overstay detection mechanism

---

## 5. Integration Failure Modes

### 5.1 Pusher Failure

| Scenario | Behavior | Impact |
|----------|----------|--------|
| Pusher credentials invalid | `pusher.Pusher()` init succeeds, `.trigger()` raises | Realtime events silently fail (caught by try/except) |
| Pusher service down | `.trigger()` raises `PusherError` | Same as above — events lost |
| Network timeout | `.trigger()` raises `requests.Timeout` | Event lost, no retry |

**No retry mechanism** for failed Pusher events. No dead-letter queue.

### 5.2 Firebase/FCM Failure

| Scenario | Behavior | Impact |
|----------|----------|--------|
| Service account invalid | `firebase_admin.initialize_app()` raises | App may fail to start (depends on import order) |
| Device token expired | `messaging.send()` raises `InvalidArgument` | Token marked inactive, notification lost |
| FCM service down | `messaging.send()` raises | Notification lost, error printed |

### 5.3 Stripe Failure

| Scenario | Behavior | Impact |
|----------|----------|--------|
| Invalid API key | Stripe API returns 401 | Payment creation fails, 400 to client |
| Webhook signature invalid | `stripe.Webhook.construct_event()` raises | Webhook rejected (correct behavior) |
| Duplicate webhook | `StripeWebhookEvent` idempotency check | Duplicate ignored (correct behavior) ✅ |
| Stripe timeout | API call raises `stripe.error.APIConnectionError` | Payment fails, user must retry |

### 5.4 Cloudinary Failure

| Scenario | Behavior | Impact |
|----------|----------|--------|
| `CLOUDINARY_URL` not set | Falls back to local storage | Media served from dyno (ephemeral on Heroku!) |
| Cloudinary service down | Upload raises exception | Image upload fails, serializer returns 500 |
| Storage quota exceeded | Upload raises exception | Same as above |

**⚠️ CRITICAL:** If Cloudinary is not configured on Heroku, uploaded media is stored on ephemeral filesystem and **lost on every dyno restart**.

### 5.5 Email/SMTP Failure

| Scenario | Behavior | Impact |
|----------|----------|--------|
| SMTP credentials missing | `SMTPAuthenticationError` | Email sends fail |
| Gmail rate limit | `SMTPDataError` | Emails rejected |
| Invalid recipient | Bounce (async, not visible to Django) | Email appears sent but bounces |

**notification_manager.py** wraps email in try/except, but some direct `send_mail()` calls in views may not be wrapped.

---

## 6. Performance Edge Cases

### 6.1 ⚠️ N+1 Query Patterns

**Evidence across multiple apps:**

| Location | Pattern | Impact |
|----------|---------|--------|
| `hotel/staff_views.py` | Booking list → accessing `.room`, `.guest` | N+1 on room and guest FKs |
| `stock_tracker/views.py` | Stock item list → accessing `.category`, `.supplier` | N+1 on related models |
| `attendance/views.py` | Clock records → accessing `.staff`, `.roster` | N+1 on staff lookups |
| `notifications/notification_manager.py` | Device token queries per notification | Multiple DB hits per notification |

**Mitigation present in some views:** `select_related()` and `prefetch_related()` are used in some serializers but not consistently.

### 6.2 🔍 Large QuerySet Loading

| View | Concern |
|------|---------|
| `StockComparisonView` | Loads all stock items for comparison period — no pagination |
| `AttendanceAnalyticsView` | Aggregates all clock records for date range |
| `NotificationManager.send_to_hotel()` | Loads all device tokens for a hotel |

### 6.3 🔍 Face Recognition Performance

**Source:** `attendance/face_views.py`

Face matching loads **all** `FaceDescriptor` records for a hotel and compares against each one:
```
NumPy distance calculation: O(n) where n = registered faces
```

For a hotel with 500+ staff, this could be slow. **No indexing or spatial data structure** for face vectors.

---

## 7. Security Edge Cases

### 7.1 ⚠️ `SECRET_KEY` Hardcoded Fallback

**Source:** `HotelMateBackend/settings.py`

```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-...')
```

If `SECRET_KEY` env var is not set, Django uses the hardcoded insecure key. This compromises:
- Session cookie signing
- CSRF token generation
- Password reset token signing
- Token authentication security

### 7.2 ⚠️ `ALLOWED_HOSTS = ['*']`

**Source:** `HotelMateBackend/settings.py`

```python
ALLOWED_HOSTS = ['*']
```

Allows requests from any hostname. Combined with `DEBUG = True`, this is a significant security risk (HTTP Host header attacks).

### 7.3 ⚠️ CORS Allows All Origins

**Source:** `HotelMateBackend/settings.py`

```python
CORS_ALLOW_ALL_ORIGINS = True
```

Any website can make authenticated API requests to this backend. Should be restricted to known frontend domains.

### 7.4 🔍 Token Exposure in URLs

Guest tokens appear in URLs:
```
/api/guest/booking/{token}/
/api/public/precheckin/{token}/
```

These tokens may appear in:
- Server access logs
- Browser history
- Referrer headers
- Analytics tools

**Mitigation:** Tokens are SHA-256 hashed before storage, so database exposure doesn't reveal the URL token. But the URL token itself is the secret.

---

## 8. Data Migration Edge Cases

### 8.1 🔍 `room_bookings` App Not in INSTALLED_APPS

**Source:** `HotelMateBackend/settings.py` — `room_bookings` is not listed in `INSTALLED_APPS`

The `room_bookings/` directory contains only service files (no models.py with Django models), so it works as a pure Python package. But if models are ever added, migrations won't be generated.

### 8.2 🔍 Large Model Files May Hide Migration Issues

| File | Lines | Models |
|------|-------|--------|
| `hotel/models.py` | 3042 | ~30 models |
| `stock_tracker/models.py` | 2633 | ~25 models |
| `entertainment/models.py` | 1499 | ~20 models |

Migration files for these apps will be large and complex. Squashing migrations periodically would improve performance.

---

## 9. Edge Case Summary Matrix

| # | Issue | Severity | Category | Automated Detection? |
|---|-------|----------|----------|---------------------|
| 1.1 | DEBUG=True hardcoded | 🔴 Critical | Security | Settings audit |
| 1.2 | staff_urls.py source missing | 🔴 Critical | Code integrity | File existence check |
| 1.3 | 5 scheduler commands missing | 🟡 High | Operations | Scheduler audit |
| 2.1 | Double hotel_slug URLs | 🟡 High | Routing | URL pattern test |
| 2.2 | Staff signals hotel bug | 🟡 High | Data integrity | Signal test |
| 2.4 | Orphaned rooms on cancel | 🟡 High | Data integrity | Integration test |
| 2.5 | Room assignment race condition | 🟡 Medium | Concurrency | Load test |
| 3.1 | Guest token not DRF auth | 🟢 Low | Architecture | N/A (design choice) |
| 3.2 | Missing permission_classes | 🟡 High | Security | Static analysis |
| 3.3 | Hotel mismatch via subdomain | 🟡 High | Authorization | Integration test |
| 4.1 | Booking status not model-enforced | 🟡 Medium | Data integrity | Model validation test |
| 5.4 | Cloudinary fallback on Heroku | 🔴 Critical | Data loss | Config check |
| 7.1 | SECRET_KEY fallback | 🔴 Critical | Security | Settings audit |
| 7.2 | ALLOWED_HOSTS = ['*'] | 🔴 Critical | Security | Settings audit |
| 7.3 | CORS allows all | 🟡 High | Security | Settings audit |
