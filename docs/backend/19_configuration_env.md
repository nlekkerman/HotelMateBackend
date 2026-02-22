# Configuration & Environment Variables

> All environment variables used by the application, with defaults and purpose.  
> **Source:** `HotelMateBackend/settings.py`, `environ.Env()` calls.

---

## Required Variables (No Default — App Will Crash)

| Variable | Type | Purpose | Used In |
|----------|------|---------|---------|
| `SECRET_KEY` | string | Django secret key for cryptographic signing | `settings.py` |
| `DATABASE_URL` | string | PostgreSQL connection string (e.g., `postgres://user:pass@host:5432/db`) | `settings.py` via `dj_database_url` |
| `EMAIL_HOST_USER` | string | Gmail SMTP sender email address | `settings.py` |
| `EMAIL_HOST_PASSWORD` | string | Gmail app password for SMTP | `settings.py` |
| `PUSHER_APP_ID` | string | Pusher application ID | `settings.py` |
| `PUSHER_KEY` | string | Pusher public key | `settings.py` |
| `PUSHER_SECRET` | string | Pusher secret key | `settings.py` |
| `PUSHER_CLUSTER` | string | Pusher cluster region (e.g., `eu`) | `settings.py` |
| `OPENAI_API_KEY` | string | OpenAI API key for Whisper voice transcription | `settings.py` |

---

## Optional Variables (Have Defaults)

| Variable | Type | Default | Purpose | Used In |
|----------|------|---------|---------|---------|
| `DEBUG` | bool | `False` | Django debug mode (⚠️ hardcoded to `True` in settings) | `settings.py` |
| `DISABLE_COLLECTSTATIC` | bool | `False` | Skip static file collection on Heroku | `settings.py` |
| `REDIS_URL` | string | `""` | Redis for Django Channels; empty = InMemoryChannelLayer | `settings.py` |
| `ALLOWED_HOSTS` | list | `['127.0.0.1','localhost']` | Django ALLOWED_HOSTS | `settings.py` |
| `STRIPE_SECRET_KEY` | string | `""` | Stripe backend API key for payment processing | `settings.py` |
| `STRIPE_PUBLISHABLE_KEY` | string | `""` | Stripe frontend key (passed to Checkout sessions) | `settings.py` |
| `STRIPE_WEBHOOK_SECRET` | string | `""` | Stripe webhook signature verification secret | `settings.py` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | string | `""` | Firebase service account JSON (Heroku fallback) | `settings.py` |
| `CLOUDINARY_URL` | string | `""` | Cloudinary connection URL; empty = local file storage | `settings.py` |
| `HEROKU_HOST` | string | `""` | Optional Heroku hostname | `settings.py` |

---

## Firebase Configuration

Firebase service account is loaded from **two sources** in priority order:

1. **File:** `firebase-service-account.json` in project root (local development)
2. **Env var:** `FIREBASE_SERVICE_ACCOUNT_JSON` (Heroku deployment)

**Source:** `settings.py` lines 173-182

---

## Hardcoded Configuration Values

| Setting | Value | Location | Notes |
|---------|-------|----------|-------|
| `DEBUG` | `True` | `settings.py` line 31 | ⚠️ Overrides env var — always True |
| Email backend | Gmail SMTP (port 587, TLS) | `settings.py` | Hardcoded to Gmail |
| VAT Rate | 9% | `hotel/services/pricing_service.py` | Ireland accommodation rate |
| Default rate plan code | `"STD"` | `hotel/services/pricing_service.py` | Lazy-created per hotel |
| Approval deadline default | 30 minutes | `apps/booking/services/booking_deadlines.py` | From `HotelAccessConfig` |
| Checkout time default | 11:00 AM | `apps/booking/services/stay_time_rules.py` | From `HotelAccessConfig` |
| Checkout grace default | 30 minutes | `apps/booking/services/stay_time_rules.py` | From `HotelAccessConfig` |
| Max shift hours | 12 hours | `attendance/management/commands/auto_clock_out_excessive.py` | From `HotelAccessConfig` |
| Token expiry | checkout + 30 days | `hotel/models.py` | GuestBookingToken |
| File upload max | 50 MB | `settings.py` | `DATA_UPLOAD_MAX_MEMORY_SIZE` |
| Chat attachment max | 50 MB | `chat/models.py` | Per attachment |
| Cloudinary image max | 10 MB | `common/cloudinary_utils.py` | Per image |
| Bulk gallery upload max | 20 images | `hotel/staff_serializers.py` | Per request |
| Page size (pagination) | 10 | `settings.py` REST_FRAMEWORK | Default |
| Cache timeout | 30 minutes (1800s) | `settings.py` CACHES | Payment idempotency |
| Cache max entries | 10000 | `settings.py` CACHES | — |
| CORS_ALLOW_ALL_ORIGINS | False | `settings.py` | Specific origins only |
| Admin field limit | 10000 | `settings.py` | `DATA_UPLOAD_MAX_NUMBER_FIELDS` |

---

## DRF Configuration

**Source:** `settings.py` REST_FRAMEWORK

```
DEFAULT_PAGINATION_CLASS: PageNumberPagination (page_size=10)
DEFAULT_FILTER_BACKENDS: DjangoFilterBackend, SearchFilter
DEFAULT_AUTHENTICATION_CLASSES: TokenAuthentication
DEFAULT_PERMISSION_CLASSES: IsAuthenticated
```

---

## CORS Configuration

**Source:** `settings.py`

### Allowed Origins
| Origin | Purpose |
|--------|---------|
| `https://dashing-klepon-d9f0c6.netlify.app` | Netlify frontend |
| `https://hotel-porter-d25ad83b12cf.herokuapp.com` | Heroku frontend |
| `http://localhost:5173`, `:5174` | Vite dev server |
| `http://localhost:3000` | React dev server |
| `https://hotelsmates.com` | Production domain |
| `https://www.hotelsmates.com` | Production www |

### Custom Headers Allowed
| Header | Purpose |
|--------|---------|
| `Idempotency-Key` | Payment idempotency |
| `X-Hotel-Id` | Hotel identification |
| `X-Hotel-Slug` | Hotel identification |
| `X-Hotel-Identifier` | Hotel identification |
| `Authorization` | Auth token |
| `Content-Type` | Request body type |

### Methods Allowed
`DELETE`, `GET`, `OPTIONS`, `PATCH`, `POST`, `PUT`

Debug mode adds regex for any `localhost:*` and `127.0.0.1:*` origin.

---

## Database Configuration

| Aspect | Value | Source |
|--------|-------|-------|
| Engine | PostgreSQL | `DATABASE_URL` env var |
| Connection max age | 600 seconds (10 min) | `settings.py` |
| Health checks | Enabled | `settings.py` |
| Test DB | SQLite in-memory | `settings.py` (when `'test' in sys.argv`) |
| Cache backend | `django.core.cache.backends.db.DatabaseCache` | `settings.py` |
| Cache table | `payment_cache_table` | `settings.py` |

---

## Channel Layers

| Condition | Backend | Notes |
|-----------|---------|-------|
| `REDIS_URL` set | `channels_redis.core.RedisChannelLayer` | SSL required (cert from certifi) |
| `REDIS_URL` empty | `channels.layers.InMemoryChannelLayer` | Single-process only |

---

## Static & Media Files

| Setting | Value |
|---------|-------|
| `STATIC_URL` | `/static/` |
| `STATIC_ROOT` | `<BASE_DIR>/staticfiles` |
| `STATICFILES_STORAGE` | `whitenoise.storage.CompressedManifestStaticFilesStorage` |
| Media storage (Cloudinary) | `cloudinary_storage.storage.MediaCloudinaryStorage` |
| Media storage (local) | `<BASE_DIR>/media` |
| `MEDIA_URL` | `/media/` |

---

## Logging

**Source:** `settings.py` LOGGING dict

| Logger | Level | Handler | Notes |
|--------|-------|---------|-------|
| `room_services` | INFO | console (stdout) | App-specific |
| `channels` | INFO | console | WebSocket internals |
| `redis` | WARNING | console | Connection errors only |
| root | INFO | console | Catch-all |

Format: `[%(asctime)s] %(levelname)s %(name)s %(message)s`
