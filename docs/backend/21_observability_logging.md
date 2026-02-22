# 21 — Observability & Logging

> Auto-generated from codebase audit. Every claim references a source file.

---

## 1. Django Logging Configuration

**Source:** `HotelMateBackend/settings.py`

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'room_services': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'redis': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### 1.1 What's Configured

| Logger Name | Level | Handler | Purpose |
|-------------|-------|---------|---------|
| `room_services` | DEBUG | console | Room service order processing |
| `channels` | DEBUG | console | Django Channels WebSocket layer |
| `redis` | DEBUG | console | Redis connection events |

### 1.2 What's Missing

| Logger | Status | Impact |
|--------|--------|--------|
| `django.request` | ❌ Not configured | 4xx/5xx errors not explicitly logged |
| `django.db.backends` | ❌ Not configured | No SQL query logging |
| `django.security` | ❌ Not configured | Security events not logged |
| Root logger (`''`) | ❌ Not configured | Uncaught app-level logs go to Django defaults |
| `notifications` | ❌ Not configured | NotificationManager errors only caught internally |
| `hotel` | ❌ Not configured | Core booking logic unlogged |
| `attendance` | ❌ Not configured | Face recognition events unlogged |
| `stock_tracker` | ❌ Not configured | Inventory changes unlogged |

**⚠️ Only 3 of 19 apps have explicit logging configured.** The remaining apps rely on Django's default logging behavior (WARNING level to console).

---

## 2. Application-Level Logging Patterns

### 2.1 NotificationManager (`notifications/notification_manager.py`)

The central notification hub uses **print statements and try/except** rather than Python's `logging` module:

```python
# Pattern found in notification_manager.py
try:
    pusher_client.trigger(channel, event, data)
except Exception as e:
    print(f"Pusher error: {e}")  # Not using logging module
```

| Pattern | Occurrences | Note |
|---------|-------------|------|
| `print()` for error output | Frequent | Not captured by logging infrastructure |
| `try/except` with pass | Some | Silent failure — errors swallowed |
| `try/except` with print | Common | Errors visible in stdout only |

### 2.2 Views Error Handling

Most views follow this pattern:
```python
# Common pattern in hotel/staff_views.py, stock_tracker/views.py, etc.
try:
    # business logic
except Exception as e:
    return Response({"error": str(e)}, status=400)
```

**⚠️ Broad `except Exception` catches mask the original error type and stack trace.**

### 2.3 Logger Usage in Apps

| App | Uses `logging` module? | Method |
|-----|----------------------|--------|
| `room_services` | ✅ Yes | `logger = logging.getLogger('room_services')` |
| `notifications` | ❌ No | Uses `print()` statements |
| `hotel` | ❌ No | Uses `print()` or silent except |
| `stock_tracker` | ❌ No | Uses `print()` in some places |
| `attendance` | ❌ No | Uses `print()` for face matching debug |
| All other apps | ❌ No | Mix of `print()` and silent exceptions |

---

## 3. Audit Trail Models (Persistent Logging)

The codebase compensates for weak logging with **database-backed audit models**:

### 3.1 `RoomStatusLog` — Room State Audit

| Field | Type | Purpose |
|-------|------|---------|
| `room` | FK → Room | Which room changed |
| `old_status` | CharField | Previous status |
| `new_status` | CharField | New status |
| `changed_by` | FK → User | Who made the change |
| `changed_at` | DateTimeField | When it happened |
| `source` | CharField | What triggered it (e.g., `"housekeeping"`, `"checkout"`) |
| `hotel` | FK → Hotel | Hotel scoping |

**Source:** `rooms/models.py`
**Written by:** `housekeeping/services.py → set_room_status()`

### 3.2 `FaceAuditLog` — Facial Recognition Audit

| Field | Type | Purpose |
|-------|------|---------|
| `staff` | FK → Staff | Staff member involved |
| `action` | CharField | `register`, `match_success`, `match_failure` |
| `confidence` | FloatField | Match confidence score |
| `timestamp` | DateTimeField | When it happened |
| `image` | ImageField | Snapshot used for matching (optional) |
| `hotel` | FK → Hotel | Hotel scoping |

**Source:** `attendance/models.py`

### 3.3 `RosterBulkOperation` — Bulk Roster Changes

| Field | Type | Purpose |
|-------|------|---------|
| `operation_type` | CharField | Type of bulk operation |
| `affected_count` | IntegerField | Number of records affected |
| `performed_by` | FK → User | Who triggered it |
| `performed_at` | DateTimeField | Timestamp |
| `details` | JSONField | Operation parameters |
| `hotel` | FK → Hotel | Hotel scoping |

**Source:** `attendance/models.py`

### 3.4 `StripeWebhookEvent` — Payment Event Log

| Field | Type | Purpose |
|-------|------|---------|
| `stripe_event_id` | CharField (unique) | Stripe's event ID for idempotency |
| `event_type` | CharField | E.g., `payment_intent.succeeded` |
| `processed` | BooleanField | Whether event was handled |
| `created_at` | DateTimeField | When received |

**Source:** `hotel/models.py`

### 3.5 `BookingExtension` — Overstay/Extension Audit

| Field | Type | Purpose |
|-------|------|---------|
| `booking` | FK → RoomBooking | Which booking was extended |
| `original_checkout` | DateField | Original checkout date |
| `new_checkout` | DateField | Extended checkout date |
| `reason` | TextField | Why extension was granted |
| `approved_by` | FK → User | Staff who approved |
| `created_at` | DateTimeField | When extension was created |

**Source:** `hotel/models.py`

### 3.6 `OverstayIncident` — Overstay Tracking

| Field | Type | Purpose |
|-------|------|---------|
| `booking` | FK → RoomBooking | Overstaying booking |
| `detected_at` | DateTimeField | When overstay was detected |
| `acknowledged_by` | FK → User | Staff who acknowledged |
| `acknowledged_at` | DateTimeField | When acknowledged |
| `resolved` | BooleanField | Whether resolved |
| `resolution` | CharField | `extended`, `checked_out`, `waived` |

**Source:** `hotel/models.py`

---

## 4. Request/Response Observability

### 4.1 Middleware Stack

**Source:** `HotelMateBackend/settings.py`

| Middleware | Observability Value |
|------------|-------------------|
| `SecurityMiddleware` | Standard Django security headers |
| `WhiteNoiseMiddleware` | Static file serving (logs in whitenoise) |
| `CorsMiddleware` | CORS headers — no logging |
| `SessionMiddleware` | Session management — no logging |
| `CommonMiddleware` | Standard request handling |
| `CsrfViewMiddleware` | CSRF validation — silent rejections |
| `AuthenticationMiddleware` | Auth — no logging |
| `MessageMiddleware` | Django messages — no logging |
| `SubdomainMiddleware` | Custom — sets `request.hotel` from subdomain |

**No request logging middleware** (e.g., no django-request-logging, no custom access log middleware).

### 4.2 Custom SubdomainMiddleware

**Source:** `hotel/middleware.py`

- Extracts hotel from subdomain or `hotel_slug` URL kwarg
- Sets `request.hotel` on every request
- **UNCLEAR IN CODE:** Whether failed hotel resolution is logged or silently returns 404

---

## 5. Error Tracking & APM

| Service | Status |
|---------|--------|
| **Sentry** | ❌ Not installed — not in `requirements.txt`, no `SENTRY_DSN` |
| **New Relic** | ❌ Not installed |
| **Datadog** | ❌ Not installed |
| **Rollbar** | ❌ Not installed |
| **Custom error tracking** | ❌ None found |
| **Django Debug Toolbar** | ❌ Not installed |

**⚠️ No error tracking service is configured.** Unhandled exceptions in production will only appear in Heroku logs (stdout/stderr), which have limited retention (typically 1500 lines on Heroku).

---

## 6. Metrics & Monitoring

| Metric Type | Status | Detail |
|-------------|--------|--------|
| **Application metrics** | ❌ None | No Prometheus, StatsD, or custom metrics |
| **Business metrics** | Partial | Analytics views in `attendance/analytics.py`, `attendance/analytics_roster.py` compute on-demand |
| **Health checks** | ❌ None | No `/health/` or `/readiness/` endpoints |
| **Uptime monitoring** | External only | Must use Heroku or third-party (UptimeRobot, etc.) |

### 6.1 Analytics Views (On-Demand Computation)

These are not continuous metrics but on-demand report endpoints:

| View | File | Computes |
|------|------|----------|
| `AttendanceAnalyticsView` | `attendance/views_analytics.py` | Clock-in/out trends, punctuality |
| `RosterAnalyticsView` | `attendance/views_analytics.py` | Shift coverage, gaps |
| `OccupancyAnalyticsView` | `hotel/staff_views.py` | Room occupancy rates |
| `RevenueReportView` | `hotel/staff_views.py` | Revenue by period |
| `StockReportView` | `stock_tracker/views.py` | Inventory levels, consumption |
| `ComparisonReportView` | `stock_tracker/views.py` | Stock comparison across periods |

---

## 7. Notification Delivery Tracking

### 7.1 Pusher Events

- **No delivery confirmation** — Pusher is fire-and-forget
- Events are triggered but success/failure is only caught via try/except in `notification_manager.py`
- **No event log table** for Pusher events

### 7.2 FCM Push Notifications

- `notification_manager.py` catches FCM send errors
- Invalid tokens are deactivated (`DeviceToken.is_active = False`)
- **No persistent delivery log** — only print statements for failures

### 7.3 Email

- Django's `send_mail()` raises on SMTP errors
- `notification_manager.py` catches and prints errors
- **No email delivery tracking** — no sent/bounced/opened tracking

---

## 8. Heroku Log Streams

Since the app deploys to Heroku, the primary log destination is **Heroku Logplex**:

| Log Source | Content |
|------------|---------|
| `heroku[web.1]` | Dyno start/stop, crashes, memory |
| `heroku[router]` | HTTP request logs (method, path, status, duration) |
| `app[web.1]` | Application stdout/stderr (print statements, logger output) |
| `heroku[scheduler]` | Scheduled job execution logs |

### 8.1 Log Retention

- **Heroku Free/Hobby**: ~1500 lines, no persistence
- **Heroku with log drain**: Can stream to Papertrail, Logentries, etc.
- **UNCLEAR IN CODE:** Whether any log drain addon is configured (this is a Heroku config, not in code)

---

## 9. Observability Gaps Summary

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| No error tracking (Sentry/etc.) | 🔴 Critical | Add Sentry with Django integration |
| No health check endpoints | 🔴 Critical | Add `/health/` for load balancer and monitoring |
| Only 3/19 apps use `logging` module | 🟡 High | Replace `print()` with proper loggers |
| No request logging middleware | 🟡 High | Add access log middleware or structured logging |
| Broad `except Exception` patterns | 🟡 High | Narrow exception types, log full tracebacks |
| No application metrics | 🟡 Medium | Add Prometheus or StatsD for key business metrics |
| No Pusher/FCM delivery logs | 🟡 Medium | Create NotificationLog model |
| `DEBUG = True` in settings | 🔴 Critical | Django shows full tracebacks to users in production |
| No email delivery tracking | 🟢 Low | Add email log model or use transactional email service |
