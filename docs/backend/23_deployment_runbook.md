# 23 — Deployment Runbook

> Auto-generated from codebase audit. Every claim references a source file.

---

## 1. Platform Overview

| Item | Value | Source |
|------|-------|--------|
| **Platform** | Heroku | `Procfile` |
| **WSGI server** | Gunicorn | `Procfile`: `web: gunicorn HotelMateBackend.wsgi` |
| **Python version** | 3.12 (inferred from `.pyc` files) | `__pycache__/staff_urls.cpython-312.pyc` |
| **Framework** | Django 5.2.4 + DRF 3.16.0 | `requirements.txt` |
| **Database** | PostgreSQL (via Heroku addon) | `HotelMateBackend/settings.py` — `dj-database-url` |
| **Static files** | WhiteNoise | `HotelMateBackend/settings.py` — `WhiteNoiseMiddleware` |
| **Media storage** | Cloudinary (or local fallback) | `HotelMateBackend/settings.py` |
| **Background jobs** | Heroku Scheduler | `setup_heroku_scheduler.sh` |
| **Realtime** | Pusher (not Django Channels) | `notifications/notification_manager.py` |

---

## 2. Procfile

**Source:** `Procfile`

```
web: gunicorn HotelMateBackend.wsgi
```

| Key | Detail |
|-----|--------|
| **Process type** | `web` (single dyno type) |
| **No worker process** | No Celery, no `worker:` process |
| **No release phase** | No `release:` for auto-migrations |
| **WSGI only** | No ASGI/Daphne — Django Channels WebSockets will NOT work |

### 2.1 Recommended Procfile Enhancement

```
web: gunicorn HotelMateBackend.wsgi --workers 3 --timeout 120
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

---

## 3. Environment Variables

### 3.1 Required Variables (App Will Fail Without These)

| Variable | Purpose | Example | Source |
|----------|---------|---------|--------|
| `SECRET_KEY` | Django secret key | `your-secret-key-here` | `settings.py` |
| `DATABASE_URL` | PostgreSQL connection | `postgres://user:pass@host:5432/db` | `settings.py` (dj-database-url) |

**⚠️ WARNING:** `SECRET_KEY` has a hardcoded fallback (`django-insecure-...`). The app will "work" without it, but this is a critical security risk.

### 3.2 Integration Variables (Features Degraded Without These)

| Variable | Integration | Impact if Missing |
|----------|-------------|-------------------|
| `PUSHER_APP_ID` | Pusher | No realtime events |
| `PUSHER_KEY` | Pusher | No realtime events |
| `PUSHER_SECRET` | Pusher | No realtime events |
| `PUSHER_CLUSTER` | Pusher | No realtime events |
| `STRIPE_SECRET_KEY` | Stripe | No payment processing |
| `STRIPE_PUBLISHABLE_KEY` | Stripe | No client-side payment |
| `STRIPE_WEBHOOK_SECRET` | Stripe | Webhooks rejected |
| `CLOUDINARY_URL` | Cloudinary | Falls back to local (ephemeral on Heroku!) |
| `OPENAI_API_KEY` | OpenAI/Whisper | No voice recognition |
| `EMAIL_HOST_USER` | Gmail SMTP | Email sends fail |
| `EMAIL_HOST_PASSWORD` | Gmail SMTP | Email sends fail |
| `REDIS_URL` | Redis/Channels | Falls back to InMemoryChannelLayer |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | FCM | No push notifications |

### 3.3 Setting Variables on Heroku

```bash
# Set all required variables
heroku config:set SECRET_KEY="your-production-secret-key"
heroku config:set PUSHER_APP_ID="your-pusher-app-id"
heroku config:set PUSHER_KEY="your-pusher-key"
heroku config:set PUSHER_SECRET="your-pusher-secret"
heroku config:set PUSHER_CLUSTER="your-pusher-cluster"
heroku config:set STRIPE_SECRET_KEY="sk_live_..."
heroku config:set STRIPE_PUBLISHABLE_KEY="pk_live_..."
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_..."
heroku config:set CLOUDINARY_URL="cloudinary://..."
heroku config:set OPENAI_API_KEY="sk-..."
heroku config:set EMAIL_HOST_USER="hotel@gmail.com"
heroku config:set EMAIL_HOST_PASSWORD="app-specific-password"
heroku config:set FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# DATABASE_URL is auto-set by Heroku Postgres addon
# REDIS_URL is auto-set by Heroku Redis addon
```

---

## 4. Database Setup

### 4.1 Heroku Postgres

```bash
# Add Postgres addon
heroku addons:create heroku-postgresql:essential-0

# DATABASE_URL is auto-configured
heroku config:get DATABASE_URL
```

### 4.2 Database Configuration in Code

**Source:** `HotelMateBackend/settings.py`

```python
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}
```

- Falls back to SQLite if `DATABASE_URL` is not set (development only)
- Connection pooling: `conn_max_age=600` (10 minutes)

### 4.3 Run Migrations

```bash
# Run on Heroku
heroku run python manage.py migrate

# Or add to Procfile release phase (recommended)
# release: python manage.py migrate --noinput
```

### 4.4 Create Cache Table

**Source:** `HotelMateBackend/settings.py` — uses `DatabaseCache`

```bash
heroku run python manage.py createcachetable
```

---

## 5. Static Files

### 5.1 Configuration

**Source:** `HotelMateBackend/settings.py`

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# WhiteNoise serves static files
MIDDLEWARE = [
    ...
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 5.2 Collect Static Files

```bash
# Run during deployment (or in release phase)
heroku run python manage.py collectstatic --noinput
```

WhiteNoise will serve collected static files directly from the Gunicorn process — no nginx/CDN required.

---

## 6. Redis Setup (Optional)

### 6.1 Add Redis Addon

```bash
heroku addons:create heroku-redis:mini
# REDIS_URL is auto-configured
```

### 6.2 TLS Configuration

A `redis_cert.der` file exists in the project root, suggesting Redis TLS may be needed.

**UNCLEAR IN CODE:** Whether the channel layer configuration uses this cert file. Heroku Redis typically handles TLS via the `REDIS_URL` scheme (`rediss://`).

### 6.3 Fallback

If `REDIS_URL` is not set, the app uses `InMemoryChannelLayer` — suitable for single-dyno deployments but channel messages won't cross dyno boundaries.

---

## 7. Heroku Scheduler

### 7.1 Add Scheduler Addon

```bash
heroku addons:create scheduler:standard
```

### 7.2 Required Scheduled Jobs

**Source:** `setup_heroku_scheduler.sh` + management commands audit

| Command | Frequency | Purpose |
|---------|-----------|---------|
| `python manage.py auto_checkout_overdue_bookings` | Every 10 min | Check out overdue bookings, flag overstays |
| `python manage.py auto_no_show` | Daily (morning) | Flag no-show bookings past check-in window |
| `python manage.py auto_cancel_unconfirmed` | Every hour | Cancel bookings unconfirmed past deadline |
| `python manage.py send_reminder_notifications` | Daily | Send pre-arrival reminders |
| `python manage.py expire_precheckin_tokens` | Daily | Invalidate expired pre-check-in tokens |
| `python manage.py cleanup_orphaned_data` | Weekly | Remove orphaned records |
| `python manage.py generate_daily_reports` | Daily (end of day) | Generate daily hotel reports |

**⚠️ WARNING:** Only `auto_checkout_overdue_bookings` is registered in `setup_heroku_scheduler.sh`. The other 6 must be added manually via Heroku Dashboard → Scheduler.

### 7.3 Configure via Dashboard

1. Go to Heroku Dashboard → your app → Resources
2. Click Heroku Scheduler
3. Add each job with appropriate frequency

---

## 8. Firebase Configuration

### 8.1 Service Account Setup

**Option A: Environment Variable (Recommended for Heroku)**
```bash
# Set the full JSON as an env var
heroku config:set FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key":"...",...}'
```

**Option B: File-based (Not recommended for Heroku)**
- Place service account JSON file in project
- Set path in environment
- ⚠️ Heroku's ephemeral filesystem makes this unreliable

### 8.2 Verification

```bash
heroku run python -c "import firebase_admin; print('Firebase OK')"
```

---

## 9. Stripe Webhook Setup

### 9.1 Register Webhook Endpoint

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://your-app.herokuapp.com/api/staff/{hotel_slug}/payments/webhook/`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
4. Copy the webhook signing secret → set as `STRIPE_WEBHOOK_SECRET`

### 9.2 Verify Webhook

```bash
# Use Stripe CLI for testing
stripe listen --forward-to https://your-app.herokuapp.com/api/staff/test-hotel/payments/webhook/
```

---

## 10. Initial Data Seeding

### 10.1 Create Superuser

```bash
heroku run python manage.py createsuperuser
```

### 10.2 Seed Preset Data

**Source:** `seed_presets.py` (root), various management commands

```bash
# Seed room types, rate plans, departments, roles
heroku run python manage.py seed_departments
heroku run python manage.py seed_roles
heroku run python manage.py seed_room_types

# Seed entertainment presets
heroku run python manage.py seed_memory_match_presets
heroku run python manage.py seed_quiz_categories
```

### 10.3 Available Seed Commands

| Command | File | Seeds |
|---------|------|-------|
| `seed_departments` | `staff/management/commands/` | Default hotel departments |
| `seed_roles` | `staff/management/commands/` | Default staff roles |
| `seed_room_types` | `rooms/management/commands/` | Default room type categories |
| `seed_memory_match_presets` | `entertainment/management/commands/` | Memory match game presets |
| `seed_quiz_categories` | `entertainment/management/commands/` | Quiz category presets |
| `seed_stock_categories` | `stock_tracker/management/commands/` | Stock item categories |
| `setup_navigation` | `staff/management/commands/` | Staff app navigation items |

---

## 11. Deployment Checklist

### 11.1 First-Time Deployment

```
☐ Create Heroku app
☐ Add Heroku Postgres addon
☐ Add Heroku Redis addon (optional)
☐ Add Heroku Scheduler addon
☐ Set all environment variables (§3)
☐ Deploy code (git push heroku main)
☐ Run migrations (heroku run python manage.py migrate)
☐ Create cache table (heroku run python manage.py createcachetable)
☐ Collect static files (heroku run python manage.py collectstatic --noinput)
☐ Create superuser (heroku run python manage.py createsuperuser)
☐ Run seed commands (§10)
☐ Configure Heroku Scheduler jobs (§7)
☐ Register Stripe webhook (§9)
☐ Verify Firebase initialization
☐ Test Pusher connectivity
☐ Verify Cloudinary uploads
```

### 11.2 Subsequent Deployments

```
☐ Push code (git push heroku main)
☐ Migrations run automatically (if release phase configured)
☐ Verify app is healthy (heroku logs --tail)
☐ Check for new management commands that need scheduling
```

### 11.3 Post-Deployment Verification

```bash
# Check app is running
heroku ps

# Tail logs
heroku logs --tail

# Check database
heroku run python manage.py showmigrations | head -50

# Test API
curl https://your-app.herokuapp.com/api/public/hotels/

# Check config
heroku config
```

---

## 12. Scaling Considerations

### 12.1 Current Architecture Limits

| Component | Single Dyno Limit | Multi-Dyno Limit |
|-----------|-------------------|-------------------|
| Gunicorn workers | Limited by dyno RAM | Scale horizontally |
| InMemoryChannelLayer | Works fine | ❌ Won't work — need Redis |
| SQLite (dev) | Single process only | ❌ Won't work — need Postgres |
| File uploads (local) | Lost on restart | ❌ Must use Cloudinary |
| Scheduler | Runs on scheduler dyno | Works across scale |

### 12.2 Scaling Commands

```bash
# Scale web dynos
heroku ps:scale web=2

# Before scaling to 2+ dynos, ensure:
# 1. REDIS_URL is set (for channel layer)
# 2. CLOUDINARY_URL is set (for media)
# 3. DATABASE_URL points to Postgres (not SQLite)
# 4. No in-memory state relied upon
```

---

## 13. Rollback Procedure

```bash
# List releases
heroku releases

# Rollback to previous release
heroku rollback v42

# Rollback migrations (if needed)
heroku run python manage.py migrate app_name 0042_previous_migration
```

---

## 14. Troubleshooting

### 14.1 Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| H10 (App crashed) | Missing env var or import error | `heroku logs --tail`, check config |
| H12 (Request timeout) | Slow DB query or external API | Check for N+1 queries, add timeouts |
| H14 (No web dynos) | Dyno not started | `heroku ps:scale web=1` |
| R14 (Memory quota) | Large file processing or queryset | Optimize queries, use pagination |
| Static files 404 | `collectstatic` not run | Run collectstatic or add to release phase |
| Migrations error | Missing migration files | `heroku run python manage.py makemigrations` |
| Pusher events not received | Wrong credentials | Verify `PUSHER_*` env vars |
| Emails not sent | Gmail app password issue | Use Gmail App Password, not account password |
| Media uploads lost | Cloudinary not configured | Set `CLOUDINARY_URL` |

### 14.2 Debug Commands

```bash
# Django shell
heroku run python manage.py shell

# Check installed apps
heroku run python -c "import django; django.setup(); from django.conf import settings; print(settings.INSTALLED_APPS)"

# Check database connection
heroku run python manage.py dbshell

# Run specific management command
heroku run python manage.py <command_name> --verbosity 2
```

---

## 15. Security Hardening (Pre-Production)

**These items MUST be addressed before going live:**

| # | Item | Current State | Required State |
|---|------|---------------|----------------|
| 1 | `DEBUG` | `True` (hardcoded) | `False` via env var |
| 2 | `SECRET_KEY` | Insecure fallback | Required env var, no fallback |
| 3 | `ALLOWED_HOSTS` | `['*']` | Specific domains only |
| 4 | `CORS_ALLOW_ALL_ORIGINS` | `True` | `False` + `CORS_ALLOWED_ORIGINS` list |
| 5 | HTTPS | Not enforced in Django | `SECURE_SSL_REDIRECT = True` |
| 6 | HSTS | Not configured | `SECURE_HSTS_SECONDS = 31536000` |
| 7 | Secure cookies | Not configured | `SESSION_COOKIE_SECURE = True` |
| 8 | `staff_urls.py` | Source missing | Reconstruct from `.pyc` |
