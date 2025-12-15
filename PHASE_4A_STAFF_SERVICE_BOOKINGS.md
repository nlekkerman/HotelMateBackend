# Phase 4A: Staff Namespace for Service-Bookings

## Goal

Expose all staff-facing "service booking" operations under ONE canonical staff namespace:

**Canonical staff base:**
```
/api/staff/hotel/{hotel_slug}/service-bookings/...
```

This will cover restaurant bookings now, and later porter luggage / trips / spa / transfers.

## Hard Rules

- `{hotel_slug}` is the ONLY accepted hotel identifier kwarg
- Use `<str:hotel_slug>` in all new staff paths
- Never use `<slug:slug>` or `kwargs["slug"]`
- No business logic refactor. This phase is routing only.
- Keep the current bookings app as the implementation home
- Do not change public/guest routes in this phase
- After Phase 4A, staff service-booking endpoints must NOT be reachable under: `/api/staff/hotel/{hotel_slug}/bookings/...` (or any ambiguous staff "bookings" namespace)

## Required Changes

### Step 1 — Create bookings/staff_urls.py (routing-only module)

Create a new file: `bookings/staff_urls.py`

It must:
- contain only imports + urlpatterns
- import and reuse existing views/viewsets from bookings/views.py
- use `<str:hotel_slug>` everywhere
- include ONLY staff-service booking endpoints (exclude public/guest endpoints like guest-booking/...)

**What to include (based on existing bookings/urls.py):**
- Restaurant endpoints used by staff (restaurant list/create and viewset routes if used)
- Booking endpoints used by staff (BookingViewSet router routes)
- BookingCategory / BookingSubcategory endpoints if staff needs them
- Blueprint + tables + objects endpoints (these are staff/admin tooling)
- Staff actions endpoints: available-tables, mark-seen, assign, unseat, delete

**What NOT to include:**
- guest-booking/... and any anonymous/public booking submission routes
- Stripe/webhook/public payment routes (those are public zone, already handled)

### Step 2 — Mount the staff urls under service-bookings

In the canonical staff router (staff_urls.py in the staff zone), include:

```python
path("hotel/<str:hotel_slug>/service-bookings/", include("bookings.staff_urls"))
```

### Step 3 — Remove/disable old staff access paths

Audit staff routing to ensure these service-booking endpoints are not exposed anywhere else under staff.

Specifically remove/stop including any old route like:
- `hotel/<str:hotel_slug>/bookings/ → bookings.urls`
- any other staff mapping that points to bookings/urls.py for staff operations

**No staff routes may remain under `/api/staff/hotel/{hotel_slug}/bookings/` (or any non-service-bookings staff namespace).**

After this phase, staff must access these ONLY through:
```
/api/staff/hotel/{hotel_slug}/service-bookings/...
```

## Verification Checklist

- [ ] `python manage.py show_urls` (or equivalent) shows staff routes only under: `/api/staff/hotel/<hotel_slug>/service-bookings/...`
- [ ] Old staff routes (if they existed) no longer resolve (404 / no match)
- [ ] No `<slug:...>` converters exist in the new staff routes (must be `<str:hotel_slug>`)
- [ ] Try an old staff URL and confirm it returns 404
- [ ] Run minimal smoke calls:
  - [ ] list restaurants under service-bookings
  - [ ] list bookings under service-bookings
  - [ ] hit one staff action endpoint (mark-seen or available-tables)

## Deliverables

- [ ] New file: `bookings/staff_urls.py`
- [ ] Updated staff router include in `staff_urls.py`
- [ ] Removed old staff mapping(s) to bookings under staff (show exact diff)
- [ ] List of final canonical staff endpoints (paths only)

## Important Notes

**Phase 4A is URL routing only:** do not modify permissions, decorators, viewsets, or serializers; remove any legacy staff access paths immediately so they return 404; staff endpoints must be reachable only via `/api/staff/hotel/{hotel_slug}/service-bookings/`.

Keep changes surgical. No model/serializer changes. No refactor. Only routing.