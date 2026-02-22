# 20 — Third-Party Integrations

> Auto-generated from codebase audit. Every claim references a source file.

---

## 1. Stripe (Payments)

| Item | Detail |
|------|--------|
| **Package** | `stripe==11.2.0` (`requirements.txt`) |
| **Env vars** | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` |
| **Config** | `hotel/payment_views.py` — `stripe.api_key` set from env at module level |

### 1.1 Payment Intents

| View | File | Purpose |
|------|------|---------|
| `CreatePaymentIntentView` | `hotel/payment_views.py` | Creates a Stripe PaymentIntent for a given `RoomBooking` amount |
| `ConfirmPaymentView` | `hotel/payment_views.py` | Confirms/captures a PaymentIntent by ID |
| `RefundPaymentView` | `hotel/payment_views.py` | Issues a full or partial refund on a PaymentIntent |

### 1.2 Webhook Handling

| View | File | Purpose |
|------|------|---------|
| `StripeWebhookView` | `hotel/payment_views.py` | Receives Stripe webhook events, verifies signature via `STRIPE_WEBHOOK_SECRET` |

**Idempotency model**: `StripeWebhookEvent` (`hotel/models.py`)
- Fields: `stripe_event_id` (unique), `event_type`, `processed`, `created_at`
- Webhook view checks `StripeWebhookEvent.objects.filter(stripe_event_id=event_id).exists()` before processing
- Handled event types: `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded`

### 1.3 Booking-Stripe Flow

```
Guest submits payment → CreatePaymentIntentView → Stripe API → returns client_secret
Frontend confirms with Stripe.js → Stripe fires webhook → StripeWebhookView
  → Verifies signature
  → Checks idempotency (StripeWebhookEvent)
  → Updates RoomBooking.payment_status
  → Triggers notification via NotificationManager
```

### 1.4 Stored Fields on RoomBooking

| Field | Type | Purpose |
|-------|------|---------|
| `stripe_payment_intent_id` | CharField | Links booking to Stripe PaymentIntent |
| `payment_status` | CharField | `pending`, `paid`, `failed`, `refunded` |
| `payment_amount` | DecimalField | Captured amount |
| `payment_currency` | CharField | Default `"usd"` |

---

## 2. Pusher (Realtime WebSocket Events)

| Item | Detail |
|------|--------|
| **Package** | `pusher==3.3.2` (`requirements.txt`) |
| **Env vars** | `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER` |
| **Hub file** | `notifications/notification_manager.py` (2417 lines) |

### 2.1 Pusher Client Initialization

```python
# notifications/notification_manager.py
pusher_client = pusher.Pusher(
    app_id=os.environ.get('PUSHER_APP_ID'),
    key=os.environ.get('PUSHER_KEY'),
    secret=os.environ.get('PUSHER_SECRET'),
    cluster=os.environ.get('PUSHER_CLUSTER'),
    ssl=True
)
```

### 2.2 Channel Naming Convention

| Channel Pattern | Example | Usage |
|-----------------|---------|-------|
| `hotel-{hotel_id}` | `hotel-42` | Hotel-wide staff events |
| `guest-{booking_id}` | `guest-1337` | Guest-specific events for a booking |
| `room-{room_id}` | `room-99` | Room-specific status updates |
| `chat-{chat_room_id}` | `chat-55` | Chat message events |
| `housekeeping-{hotel_id}` | `housekeeping-42` | Housekeeping task updates |

### 2.3 Event Types by Domain

**Booking events** (triggered from `notification_manager.py`):
- `new-booking` — New reservation created
- `booking-updated` — Booking details changed
- `booking-cancelled` — Cancellation processed
- `check-in` — Guest checked in
- `check-out` — Guest checked out
- `room-assigned` — Room assigned to booking
- `room-moved` — Guest moved to different room

**Housekeeping events**:
- `room-status-changed` — Room cleaning status updated
- `task-assigned` — Housekeeping task assigned
- `task-completed` — Housekeeping task completed

**Chat events** (triggered from `chat/views.py`, `staff_chat/views.py`):
- `new-message` — New chat message
- `message-deleted` — Message removed
- `typing` — User typing indicator

**Room service events**:
- `new-order` — Room service order placed
- `order-status-changed` — Order status updated

**Maintenance events**:
- `new-request` — Maintenance request created
- `request-updated` — Request status changed

### 2.4 Pusher Channel Authentication

| File | Endpoint | Purpose |
|------|----------|---------|
| `chat/views.py` | `PusherAuthView` | Authenticates private channel subscriptions for guest/staff chat |
| `staff_chat/views.py` | Staff Pusher auth | Authenticates staff-only private channels |

### 2.5 Debug Tooling

- `pusher_debug_tool.html` (root) — Standalone HTML page for testing Pusher events in browser

---

## 3. Firebase Cloud Messaging (Push Notifications)

| Item | Detail |
|------|--------|
| **Package** | `firebase-admin==6.5.0` (`requirements.txt`) |
| **Env vars** | `FIREBASE_SERVICE_ACCOUNT_JSON` (JSON string) or file-based service account |
| **Service file** | `notifications/fcm_service.py` |

### 3.1 FCM Initialization

```python
# notifications/fcm_service.py
# Initializes Firebase app from:
# 1. FIREBASE_SERVICE_ACCOUNT_JSON env var (JSON string → parsed to dict → Certificate)
# 2. Falls back to file-based service account path
```

### 3.2 Device Token Storage

| Model | File | Fields |
|-------|------|--------|
| `DeviceToken` | `notifications/models.py` | `user` (FK), `token` (CharField), `device_type` (ios/android/web), `is_active`, `hotel` (FK) |

### 3.3 Push Notification Targeting

Notifications sent via `notification_manager.py` which calls FCM service:

| Target | Method | Description |
|--------|--------|-------------|
| Single user | `send_to_user()` | Sends to all active device tokens for a user |
| Department | `send_to_department()` | Sends to all staff in a department |
| Hotel-wide | `send_to_hotel()` | Broadcast to all staff device tokens for a hotel |
| Guest | `send_to_guest()` | Sends to guest device tokens linked to a booking |

### 3.4 Notification Payload Structure

```python
# Typical payload structure from notification_manager.py
{
    "title": "New Booking",
    "body": "Room 101 - John Doe checking in tomorrow",
    "data": {
        "type": "booking",
        "booking_id": "123",
        "hotel_id": "42",
        "action": "view_booking"
    }
}
```

### 3.5 FCM Error Handling

- `notification_manager.py` catches `firebase_admin.messaging` exceptions
- Invalid/expired tokens: Marks `DeviceToken.is_active = False`
- Batch sending: Uses `send_multicast()` for multiple tokens
- **UNCLEAR IN CODE:** Whether FCM failures are logged to any persistent audit table or only to stdout

---

## 4. Cloudinary (Media/File Storage)

| Item | Detail |
|------|--------|
| **Package** | `cloudinary==1.44.0`, `django-cloudinary-storage==0.3.0` (`requirements.txt`) |
| **Env var** | `CLOUDINARY_URL` (format: `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`) |
| **Config** | `HotelMateBackend/settings.py` — `DEFAULT_FILE_STORAGE` set conditionally |

### 4.1 Storage Configuration

```python
# HotelMateBackend/settings.py
if os.environ.get('CLOUDINARY_URL'):
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    # Falls back to local file storage if CLOUDINARY_URL not set
```

### 4.2 Upload Utility

| File | Function | Purpose |
|------|----------|---------|
| `common/cloudinary_utils.py` | `upload_to_cloudinary()` | Wraps `cloudinary.uploader.upload()` with folder organization |
| `common/cloudinary_utils.py` | `delete_from_cloudinary()` | Removes media by public_id |

### 4.3 Models Using Cloudinary

| Model | Field | App |
|-------|-------|-----|
| `Hotel.logo` | ImageField | hotel |
| `Hotel.cover_image` | ImageField | hotel |
| `PublicPage` hero/gallery images | ImageField | hotel (CMS) |
| `GalleryImage.image` | ImageField | hotel (CMS) |
| `NewsArticle.image` | ImageField | hotel (CMS) |
| `Staff.profile_image` | ImageField | staff |
| `Post.image` | ImageField | posts |
| `MenuItem.image` | ImageField | room_services |
| `StockItem.image` | ImageField | stock_tracker |
| `MaintenanceRequest.image` | ImageField | maintenance |
| `Room.image` | ImageField | rooms |
| `FaceDescriptor.image` | ImageField | attendance |
| `Issue.image` | ImageField | issues |

### 4.4 Upload Flow

```
Client uploads file → DRF serializer with ImageField
  → Django's DEFAULT_FILE_STORAGE routes to Cloudinary
  → Cloudinary returns URL → Stored in model field
  → URL served directly from Cloudinary CDN
```

---

## 5. OpenAI / Whisper (Voice Recognition)

| Item | Detail |
|------|--------|
| **Package** | `openai==1.58.1` (`requirements.txt`) |
| **Env var** | `OPENAI_API_KEY` |
| **App** | `voice_recognition/` |

### 5.1 Architecture

| File | Purpose |
|------|---------|
| `voice_recognition/views.py` | API endpoint accepting audio file upload |
| `voice_recognition/services.py` | Whisper transcription + command parsing |
| `voice_recognition/urls.py` | URL routing for voice endpoints |

### 5.2 Voice-to-Stock Pipeline

```
Audio file upload → Whisper API transcription → Text
  → NLP command parser → Structured stock command
  → stock_tracker service layer → Inventory update
```

### 5.3 Supported Voice Commands

| Command Pattern | Action | Target App |
|-----------------|--------|------------|
| "Add [quantity] [item]" | Stock addition | stock_tracker |
| "Remove [quantity] [item]" | Stock subtraction | stock_tracker |
| "Check [item] stock" | Stock query | stock_tracker |
| "Transfer [item] to [location]" | Stock transfer | stock_tracker |

**UNCLEAR IN CODE:** Exact grammar rules for voice command parsing — the NLP layer may use fuzzy matching or strict patterns.

### 5.4 Error Handling

- Audio format validation before sending to Whisper
- Whisper API timeout handling
- Unrecognized command fallback (returns transcription without action)
- **UNCLEAR IN CODE:** Whether failed transcriptions are stored for review

---

## 6. Gmail SMTP (Email)

| Item | Detail |
|------|--------|
| **Config** | `HotelMateBackend/settings.py` |
| **Env vars** | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` |

### 6.1 SMTP Settings

```python
# HotelMateBackend/settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

### 6.2 Email Usage Points

| Caller | File | Email Type |
|--------|------|------------|
| `NotificationManager` | `notifications/notification_manager.py` | Booking confirmations, cancellations |
| `send_precheckin_email()` | `hotel/staff_views.py` | Pre-check-in link to guests |
| `send_booking_confirmation()` | `hotel/staff_views.py` | Booking confirmation with details |
| `send_survey_email()` | `hotel/staff_views.py` | Post-stay survey link |
| `send_registration_code()` | `staff/views.py` | Staff registration invite code |

### 6.3 Email Templates

- Emails are constructed inline (HTML strings in Python code)
- **No Django template files** used for email rendering
- HTML is built with f-strings in notification_manager.py and view functions

### 6.4 Fallback Behavior

- If `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` not set: Django's `send_mail()` will raise `SMTPAuthenticationError`
- **No graceful fallback** — email failures will propagate as 500 errors unless caught by caller
- `notification_manager.py` wraps email sends in try/except and logs failures

---

## 7. Django Channels / Redis (WebSocket Layer)

| Item | Detail |
|------|--------|
| **Package** | `channels==4.2.0`, `channels-redis==4.2.1` (`requirements.txt`) |
| **Env var** | `REDIS_URL` |
| **Config** | `HotelMateBackend/settings.py` |

### 7.1 Channel Layer Configuration

```python
# HotelMateBackend/settings.py
if os.environ.get('REDIS_URL'):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [os.environ.get('REDIS_URL')],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    }
```

### 7.2 ASGI vs WSGI

- **Procfile** uses `gunicorn` (WSGI), NOT `daphne` (ASGI)
- `HotelMateBackend/asgi.py` exists but is **not used in production**
- Channels layer is configured but **Procfile does not run an ASGI server**

**⚠️ IMPLICATION:** Django Channels WebSocket consumers will NOT work in production with the current Procfile. The app relies on **Pusher** for realtime events instead of native Django Channels WebSockets.

### 7.3 Redis TLS

- `redis_cert.der` file present in project root
- **UNCLEAR IN CODE:** Whether `redis_cert.der` is actively used in the channel layer config or only for direct Redis client connections

---

## 8. NumPy / face_recognition (Facial Recognition)

| Item | Detail |
|------|--------|
| **Packages** | `numpy==2.2.3`, `face-recognition==1.3.0`, `dlib` (transitive) (`requirements.txt`) |
| **App** | `attendance/` |

### 8.1 Face Descriptor Pipeline

| File | Component | Purpose |
|------|-----------|---------|
| `attendance/face_views.py` | `FaceRegistrationView` | Captures face image, extracts 128-dim descriptor |
| `attendance/face_views.py` | `FaceMatchView` | Compares uploaded face against stored descriptors |
| `attendance/models.py` | `FaceDescriptor` | Stores 128-dim face encoding as JSON array |
| `attendance/models.py` | `FaceAuditLog` | Audit trail for all face operations |

### 8.2 Matching Algorithm

```python
# attendance/face_views.py (approximate flow)
# 1. Extract face encoding from uploaded image using face_recognition library
# 2. Load all FaceDescriptor entries for the hotel
# 3. Compare using numpy euclidean distance
# 4. Threshold: typically 0.6 (lower = stricter)
# 5. Return best match if below threshold
```

### 8.3 Clock-In via Face

```
Staff uploads selfie → FaceMatchView
  → face_recognition extracts 128-dim encoding
  → NumPy distance comparison against stored descriptors
  → Match found → ClockRecord created
  → Pusher event fired for attendance dashboard
```

---

## 9. WeasyPrint (PDF Generation)

| Item | Detail |
|------|--------|
| **Package** | `weasyprint==63.1` (`requirements.txt`) |
| **Usage** | `attendance/pdf_report.py` |

### 9.1 Report Generation

| Function | File | Output |
|----------|------|--------|
| `generate_attendance_report()` | `attendance/pdf_report.py` | PDF attendance report for date range |
| `generate_roster_report()` | `attendance/pdf_report.py` | PDF roster/schedule report |

### 9.2 Flow

```
Staff requests report → View calls pdf_report function
  → HTML template rendered with context data
  → WeasyPrint converts HTML → PDF bytes
  → Returned as HttpResponse with content_type='application/pdf'
```

---

## 10. Integration Dependency Matrix

| Integration | Required? | Graceful Degradation? | Impact if Missing |
|-------------|-----------|----------------------|-------------------|
| **Stripe** | Optional | ✅ Payment features disabled | No payment processing |
| **Pusher** | Optional | ⚠️ Partial — events silently fail | No realtime updates to frontend |
| **Firebase/FCM** | Optional | ⚠️ Push notifications silently fail | No mobile push notifications |
| **Cloudinary** | Optional | ✅ Falls back to local storage | Media served from app server |
| **OpenAI/Whisper** | Optional | ✅ Voice features unavailable | No voice-to-stock commands |
| **Gmail SMTP** | Optional | ❌ Email sends raise exceptions | Booking confirmations, pre-checkin emails fail |
| **Redis** | Optional | ✅ Falls back to InMemoryChannelLayer | No cross-process channel layer |
| **PostgreSQL** | Required | ❌ App won't start without DB | Total failure |
| **face_recognition** | Optional | ⚠️ Import errors if dlib missing | No facial clock-in |
| **WeasyPrint** | Optional | ⚠️ PDF endpoints fail | No PDF report download |

---

## 11. Integration Health Checks

**No health-check endpoints exist** for verifying third-party connectivity.

**⚠️ RECOMMENDATION:** Consider adding a `/api/staff/{hotel_slug}/health/` endpoint that verifies:
- Pusher connectivity (trigger test event)
- Firebase initialization status
- Stripe API key validity
- Cloudinary connectivity
- Redis connectivity
- Database connectivity
- SMTP server reachability
