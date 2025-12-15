# PHASE 4B: Guest Zone hotel_slug Normalization

**Status:** ✅ COMPLETED  
**Date:** December 15, 2025  
**Scope:** `/api/guest/` zone ONLY

## Overview

Phase 4B implements surgical normalization of the guest URL layer to enforce consistent `{hotel_slug}` usage across all guest-facing endpoints. This phase establishes the canonical pattern that will serve as the template for future URL zone normalizations.

## Normalization Rules

### ✅ Canonical Pattern
```python
# REQUIRED: Use <str:hotel_slug> converter
path('hotels/<str:hotel_slug>/endpoint/', view_function, name='url-name')

# REQUIRED: Views accept hotel_slug parameter
def view_function(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    # Use kwargs["hotel_slug"] in class-based views
```

### 🚫 Forbidden Patterns

**URL Converters:**
```python
# FORBIDDEN in guest zone
path('hotels/<slug:hotel_slug>/endpoint/', ...)  # Wrong converter type
path('hotels/<slug:slug>/endpoint/', ...)        # Wrong parameter name
```

**View Parameters:**
```python
# FORBIDDEN in guest zone
def view_function(request, slug):                # Wrong parameter name
    hotel = get_object_or_404(Hotel, slug=kwargs["slug"])  # Wrong kwarg key
```

## Scope Boundary

### ✅ In Scope (Phase 4B)
- `guest_urls.py` - Primary guest URL configuration
- Guest zone views that handle hotel_slug parameter
- Guest zone URL patterns under `/api/guest/`
- Regression tests for guest URL compliance

### 🚫 Out of Scope (Other Phases)
- `staff_urls.py` - Staff zone normalization (separate phase)
- `public_urls.py` - Public API normalization (separate phase)  
- `hotel/urls.py` - Hotel app URLs (separate phase)
- End-to-end integration tests
- Frontend API integration updates
- Documentation updates (unless paths changed)

## Implementation Results

### Audit Findings
```bash
# Guest zone compliance check
grep -r "<slug:" guest_urls.py          # ✅ ZERO matches
grep -r "kwargs\[.slug.\]" guests/      # ✅ ZERO matches  
```

### URL Patterns Verified
All guest zone URLs use consistent `<str:hotel_slug>` converter:

```python
urlpatterns = [
    path('hotels/<str:hotel_slug>/site/home/', guest_home, name='guest-home'),
    path('hotels/<str:hotel_slug>/site/rooms/', guest_rooms, name='guest-rooms'),
    path('hotels/<str:hotel_slug>/availability/', check_availability, name='check-availability'),
    path('hotels/<str:hotel_slug>/pricing/quote/', get_pricing_quote, name='pricing-quote'),
    path('hotels/<str:hotel_slug>/bookings/', create_booking, name='create-booking'),
]
```

### View Functions Verified
All guest zone views accept `hotel_slug` parameter:

- `guest_home(request, hotel_slug)` ✅
- `guest_rooms(request, hotel_slug)` ✅  
- `check_availability(request, hotel_slug)` ✅
- `get_pricing_quote(request, hotel_slug)` ✅
- `create_booking(request, hotel_slug)` ✅

### Endpoints Preserved
All guest endpoint paths remain unchanged:

- `/api/guest/hotels/{hotel_slug}/site/home/` ✅
- `/api/guest/hotels/{hotel_slug}/site/rooms/` ✅
- `/api/guest/hotels/{hotel_slug}/availability/` ✅
- `/api/guest/hotels/{hotel_slug}/pricing/quote/` ✅
- `/api/guest/hotels/{hotel_slug}/bookings/` ✅

## Verification Commands

### Check for Forbidden Patterns
```bash
# Must return ZERO matches in guest zone
grep -r "<slug:" guest_urls.py
grep -r "kwargs\[.slug.\]" guests/
```

### Test URL Resolution
```python
# All guest URLs must resolve correctly
from django.urls import reverse
reverse('guest-home', kwargs={'hotel_slug': 'test-hotel'})
reverse('check-availability', kwargs={'hotel_slug': 'test-hotel'})
```

### Validate show_urls Output
```bash
python manage.py show_urls | grep "/api/guest/"
# Should show only <str:hotel_slug> patterns
```

## Regression Tests Added

Location: `guests/tests.py`

1. **Pattern Compliance Test** - Verifies zero `<slug:` patterns in guest URLs
2. **URL Resolution Test** - Confirms reverse/resolve works for key guest endpoints  
3. **View Parameter Test** - Ensures no guest views depend on `kwargs["slug"]`

## Success Criteria

- ✅ Zero `<slug:` patterns in guest zone URLs
- ✅ All guest views use `hotel_slug` parameter consistently  
- ✅ All guest URLs resolve/reverse correctly with `hotel_slug` kwarg
- ✅ No guest zone views reference `kwargs["slug"]`
- ✅ All endpoint paths remain unchanged
- ✅ Regression tests prevent future violations

## Next Steps

- **Phase 4C:** Frontend API integration updates (remove calls to deprecated endpoints)
- **Phase 5A:** Staff zone normalization using guest zone as template
- **Phase 5B:** Public API zone normalization  

---

**This document serves as the authoritative reference for guest zone URL normalization standards and must be consulted before making any changes to guest zone URL patterns.**