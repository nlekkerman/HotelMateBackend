# 02 — Quick Start

> Auto-generated from codebase audit. Every claim references a source file.

---

## 1. Prerequisites

| Dependency | Required | Notes |
|------------|----------|-------|
| Python 3.12+ | ✅ | Inferred from `__pycache__/staff_urls.cpython-312.pyc` |
| PostgreSQL | ✅ (prod) | SQLite used automatically for `python manage.py test` |
| Git | ✅ | Version control |
| pip | ✅ | Package management |
| Redis | Optional | Falls back to `InMemoryChannelLayer` if missing |
| System libs for dlib/face-recognition | Optional | Only needed for facial clock-in feature |

---

## 2. Clone & Install

```bash
# Clone the repository
git clone <repo-url> HotelMateBackend
cd HotelMateBackend

# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate
# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Source:** `requirements.txt` — 100+ packages. Notable system-level dependencies:
- `psycopg2-binary` — PostgreSQL adapter (no system PostgreSQL headers needed)
- `face-recognition` — requires `dlib` which needs CMake + C++ compiler. Skip if not using facial clock-in.

---

## 3. Environment Configuration

The project uses `django-environ` to load variables from a `.env` file.

**Source:** `HotelMateBackend/settings.py`
```python
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
```

### 3.1 Create `.env` File

Create a `.env` file in the project root (`HotelMateBackend/.env`):

```env
# ─── REQUIRED ───────────────────────────────────────
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=postgres://user:password@localhost:5432/hotelmate
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Pusher (required for realtime events)
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=your-pusher-cluster

# OpenAI (required by settings.py, but only used for voice recognition)
OPENAI_API_KEY=your-openai-key

# ─── OPTIONAL ───────────────────────────────────────
# Stripe (payment processing)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Cloudinary (media storage — falls back to local)
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Redis (falls back to InMemoryChannelLayer)
REDIS_URL=redis://localhost:6379/0

# Allowed hosts (defaults to localhost)
ALLOWED_HOSTS=127.0.0.1,localhost
```

**⚠️ Note:** `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `OPENAI_API_KEY` are called via `env('VAR_NAME')` **without defaults** in `settings.py`, so they will raise `ImproperlyConfigured` if missing. You can set them to dummy values for local dev if you don't need those features.

### 3.2 Local Dev Without External Services

For minimal local development, you can use dummy values:

```env
SECRET_KEY=dev-secret-key-not-for-production
DATABASE_URL=postgres://localhost:5432/hotelmate
EMAIL_HOST_USER=test@test.com
EMAIL_HOST_PASSWORD=dummy
PUSHER_APP_ID=0
PUSHER_KEY=dummy
PUSHER_SECRET=dummy
PUSHER_CLUSTER=mt1
OPENAI_API_KEY=sk-dummy
```

Pusher events will fail silently (caught by try/except in `notifications/notification_manager.py`). Email sends will fail. Voice recognition won't work. Everything else will function.

---

## 4. Database Setup

### 4.1 PostgreSQL (Recommended)

```bash
# Create the database
createdb hotelmate

# Run migrations
python manage.py migrate

# Create cache table (used for payment caching)
python manage.py createcachetable
```

**Source:** `HotelMateBackend/settings.py` — cache backend uses `DatabaseCache` with table name `payment_cache_table`.

### 4.2 SQLite (Tests Only)

When running `python manage.py test`, the settings automatically switch to SQLite in-memory:

```python
# HotelMateBackend/settings.py
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
```

---

## 5. Seed Data

After migrations, populate reference data:

```bash
# Core seeding (recommended order)
python manage.py seed_departments       # Default hotel departments
python manage.py seed_roles             # Default staff roles
python manage.py setup_navigation       # Staff app navigation items

# Optional seeding
python manage.py seed_room_types        # Default room type categories
python manage.py seed_stock_categories  # Stock item categories
python manage.py seed_memory_match_presets  # Entertainment game presets
python manage.py seed_quiz_categories   # Quiz category presets
```

**Source:** Management commands found in `staff/management/commands/`, `rooms/management/commands/`, `stock_tracker/management/commands/`, `entertainment/management/commands/`.

---

## 6. Create Superuser

```bash
python manage.py createsuperuser
```

Access Django admin at `http://localhost:8000/admin/`.

---

## 7. Run the Development Server

```bash
python manage.py runserver
```

The server starts at `http://localhost:8000/`. Visit the root URL to see a listing of all available API endpoints (generated by the `home()` view in `HotelMateBackend/urls.py`).

### 7.1 Key URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | API endpoint listing |
| `http://localhost:8000/admin/` | Django admin interface |
| `http://localhost:8000/api/staff/` | Staff API zone (Token auth) |
| `http://localhost:8000/api/guest/` | Guest API zone (Guest token) |
| `http://localhost:8000/api/public/` | Public API zone (no auth) |

---

## 8. Run Tests

### 8.1 Full Test Suite

```bash
python manage.py test
```

This runs all `tests.py` and `test_*.py` files across all apps using Django's test runner with SQLite in-memory database.

### 8.2 Run Tests for a Specific App

```bash
python manage.py test hotel
python manage.py test attendance
python manage.py test housekeeping
python manage.py test stock_tracker
```

### 8.3 Run a Specific Test File

```bash
python manage.py test tests.test_staff_checkin_validation
python manage.py test hotel.test_booking_integrity
python manage.py test attendance.test_clock_roster_linking
```

### 8.4 Run with Verbosity

```bash
python manage.py test --verbosity 2
```

---

## 9. Project Scripts

**Source:** `scripts/` directory

| Script | Purpose | How to Run |
|--------|---------|-----------|
| `audit_routes.py` | Audit URL routing patterns | `python manage.py runscript audit_routes` |
| `reset_quiz_tables.py` | Drop and recreate quiz tables | `python manage.py runscript reset_quiz_tables` |
| `scripts/archive/` | 34 legacy stock tracker scripts | Various utility scripts |

Requires `django-extensions` for `runscript` command.

---

## 10. Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `ImproperlyConfigured: Set the X environment variable` | Missing env var | Add to `.env` file (see §3) |
| `ModuleNotFoundError: No module named 'dlib'` | face-recognition dependency | Install CMake + C++ build tools, or skip face-recognition |
| `OperationalError: no such table` | Migrations not run | `python manage.py migrate` |
| `OperationalError: FATAL: database "hotelmate" does not exist` | PostgreSQL DB not created | `createdb hotelmate` |
| `ConnectionRefusedError: [Errno 111] Connection refused` (Redis) | Redis not running | Start Redis or remove `REDIS_URL` from `.env` |
| Static files 404 in dev | Normal in development | Django serves static files automatically with `DEBUG=True` |
