# Background Jobs & Schedulers

> All management commands, scheduled tasks, and automation.  
> **No Celery** — the project uses Heroku Scheduler + Django management commands.

---

## Scheduler Configuration

**Source:** `setup_heroku_scheduler.sh`

Currently **only one command** is registered in Heroku Scheduler:

| Command | Frequency | Dyno |
|---------|-----------|------|
| `python manage.py auto_clock_out_excessive` | Every 30 minutes | Standard-1X |

### ⚠️ Missing from Scheduler

These commands are designed for scheduled execution but are **NOT registered**:

| Command | Recommended Frequency | Risk If Not Running |
|---------|----------------------|---------------------|
| `auto_expire_overdue_bookings` | Every 5–15 min | Overdue bookings pile up; no Stripe refunds issued |
| `flag_overstay_bookings` | Every 15–30 min | Overstays go undetected by staff |
| `send_scheduled_surveys` | Every 10–30 min | Post-checkout surveys never sent |
| `cleanup_survey_tokens` | Daily | Token table bloats indefinitely |
| `check_attendance_alerts` | Every 5–10 min | Break/overtime alerts never fire |
| `update_tournament_statuses` | Hourly | Tournaments stuck in wrong status |

---

## Complete Command Inventory

### Scheduled / Should-Be-Scheduled

| # | App | Command | Purpose | Idempotency | Failure Behavior |
|---|-----|---------|---------|-------------|-----------------|
| 1 | attendance | `auto_clock_out_excessive` | Force clock-out for staff exceeding `max_shift_hours` (default 12h). Processes ALL open sessions. | ✅ Safe to re-run (skips already clocked-out) | Logs errors, continues to next record |
| 2 | attendance | `check_attendance_alerts` | Send break/overtime Pusher alerts for open clock logs. | ✅ Alerts are stateless | Logs errors, continues |
| 3 | hotel | `auto_expire_overdue_bookings` | Expire PENDING_APPROVAL bookings past `approval_deadline`. Processes Stripe refunds. | ✅ Skips already-expired bookings | Logs per-booking errors, continues |
| 4 | hotel | `flag_overstay_bookings` | Detect IN_HOUSE bookings past checkout deadline. Creates `OverstayIncident` records. | ✅ Uses `get_or_create` — safe to re-run | Logs errors, continues |
| 5 | hotel | `send_scheduled_surveys` | Send survey emails whose `survey_send_scheduled_at` has arrived. | ✅ Updates `survey_sent_at` on success — won't re-send | Logs per-email errors |
| 6 | hotel | `cleanup_survey_tokens` | Delete expired, used, and old tokens (preserves SurveyResponse records). | ✅ Deletes by criteria — safe to re-run | Standard Django ORM deletion |
| 7 | entertainment | `update_tournament_statuses` | Transition tournament statuses based on start/end dates (UPCOMING→ACTIVE→COMPLETED). | ✅ Date-based, idempotent | Logs errors |

### Manual — Data Integrity & Healing

| # | App | Command | Purpose | Notes |
|---|-----|---------|---------|-------|
| 8 | hotel | `heal_booking_integrity` | Detect/fix booking party issues (missing/duplicate PRIMARY). | Supports `--dry-run`. Per-hotel or all. |
| 9 | hotel | `cleanup_orphaned_guests` | Fix guests in rooms with no booking ("ghost bug"). | One-time fix |
| 10 | hotel | `fix_cloudinary_urls` | Replace backslashes with forward slashes in Cloudinary URLs. | One-time fix |

### Manual — Seed / Test Data

| # | App | Command | Purpose | Notes |
|---|-----|---------|---------|-------|
| 11 | hotel | `seed_hotels` | Seed sample hotels for dev/testing. | Has `--clear` flag (⚠️ destructive) |
| 12 | hotel | `seed_default_cancellation_policies` | Seed cancellation policy templates. | Per-hotel |
| 13 | hotel | `seed_killarney_public_page` | Seed Hotel Killarney public page content. | Idempotent; hotel_id=2 hardcoded |
| 14 | hotel | `populate_killarney_pms` | Seed rate plans, promotions, daily rates, inventory for Killarney. | hotel_id=2 hardcoded |
| 15 | hotel | `simulate_killarney_bookings` | Simulate full booking flow for all Killarney room types. | Test script |
| 16 | hotel | `check_killarney_rooms` | Inspect room type/rate plan data for Killarney. | Read-only diagnostic |
| 17 | hotel | `upload_killarney_images` | Upload Killarney images to Cloudinary. | One-time |
| 18 | hotel | `delete_all_images` | Delete ALL Cloudinary images + clear DB refs. | ⚠️ Requires `--confirm`. Destructive! |
| 19 | room_bookings | `seed_no_way_bookings` | Create deterministic test bookings across all lifecycle stages. | "no-way-hotel" specific |
| 20 | staff | `seed_navigation_items` | Seed sidebar navigation items for a hotel. | Accepts `--hotel-slug` |
| 21 | bookings | `generate_restaurant_bookings` | Generate 10 restaurant bookings/day for 30 days. | Randomized test data |
| 22 | stock_tracker | `create_stock_categories` | Create stock categories (D/B/S/W/M). | Seed |
| 23 | stock_tracker | `create_cocktails` | Create cocktail recipes with ingredients. | Requires `--hotel-slug` |
| 24 | stock_tracker | `create_missing_cocktails` | Create missing cocktails. | Requires `--hotel-slug` |
| 25 | stock_tracker | `update_cocktail_prices` | Bulk-update cocktail selling prices. | Data fix |
| 26 | stock_tracker | `generate_analytics_data` | Generate test data for analytics dashboard. | Seed |
| 27 | stock_tracker | `create_october_2025` | Create October 2025 period (closed) with snapshots. | Seed |
| 28 | stock_tracker | `create_october_stocktake` | Create and close October 2025 stocktake. | Requires `--hotel-slug` |
| 29 | stock_tracker | `recreate_october_period` | Delete + recreate October 2025 period. | Destructive |
| 30 | stock_tracker | `close_october_period` | Close October 2025 period with snapshots. | Requires `--hotel-slug` |

### Manual — Debug / Read-Only

| # | App | Command | Purpose |
|---|-----|---------|---------|
| 31 | stock_tracker | `check_october_period` | Inspect October 2025 period status. |
| 32 | stock_tracker | `fetch_october_2025` | Display October 2025 stocktake data. |
| 33 | common | `audit_legacy_routes` | Verify legacy routes return 404, canonical routes resolve. |

---

## Signal-Based Automation (Not Management Commands)

| Signal | Sender | File | Behavior |
|--------|--------|------|----------|
| `post_save` | `Hotel` | `hotel/signals.py` | Auto-create `HotelAccessConfig` + default `NavigationItem` set |
| `post_save` | `User` | `staff/signals.py` | Auto-create DRF Token + Staff profile from RegistrationCode |
| `post_save` | `Order` | `room_services/signals.py` | Trigger room service notification via `NotificationManager` |
| `post_save` | `BreakfastOrder` | `room_services/signals.py` | Trigger breakfast notification via `NotificationManager` |
| `post_save` | `HotelInfoCategory` | `hotel_info/signals.py` | Auto-generate QR code URL |
| `post_save` | `StaffMessage` | `staff_chat/signals.py` | Update unread count via Pusher |

---

## No Background Workers

- **No Celery** — not in `requirements.txt`, no `celery.py` found
- **No Django-Q** — not installed
- **No APScheduler** — not installed
- **No cron integration** — only Heroku Scheduler
- All "background" work runs as synchronous management commands invoked by external scheduler
