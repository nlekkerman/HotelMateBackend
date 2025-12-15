# Backend Legacy Endpoint Audit Report

**Date:** December 15, 2025  
**Audit Type:** Backend Legacy Routes Verification (Proof Mode)  
**Status:** ⚠️ LEGACY FOUND - Action Required  

## Executive Summary

The audit identified **2 active legacy routes** that still resolve and should return 404, plus **4 canonical routes** that are broken. The backend requires specific cleanup to fully eliminate legacy endpoint access.

### Key Findings

- ✅ **Most legacy patterns disabled**: 11/13 legacy routes properly return 404
- ⚠️ **2 critical legacy routes still active**: `/api/hotel/` endpoints still resolve
- ⚠️ **4 canonical routes broken**: Payment and guest zone routes need fixes
- ✅ **Staff room booking routes working**: All new staff endpoints operational
- ⚠️ **1 legacy slug pattern found**: `<slug:slug>` still present in hotel/urls.py

## PHASE 1 — Repository Grep Results

### A) Old Namespaces

#### `/api/hotel/` patterns found in:
**Documentation files only (no active code):**
- REFACTORING_PLAN.md (multiple references to old patterns)
- PHASE3_PUBLIC_CLEANUP_PLAN.md 
- PHASE3_FRONTEND_PUBLIC_API_MIGRATION.md
- PHASE_4A_STAFF_SERVICE_BOOKINGS.md
- PHASE_4B_GUEST_ZONE_HOTEL_SLUG_NORMALIZATION.md

**No active route definitions found in Python files.**

#### `api/hotel` patterns found in:
- Same documentation files as above
- **rooms/views.py** line 130: Comment reference only
- **README.md** lines 195, 198: Different context (`/api/hotel-info/`, `/api/hotels/`)

#### `hotel/staff` patterns found in:
**Documentation and legacy references only - no active routes.**

#### `/bookings/assign-room`, `/bookings/checkout`, `/bookings/party` patterns:
**No active route definitions found** - only found in documentation and refactoring plans.

### B) Slug Kwargs Legacy

#### `<slug:slug>` patterns found in:
- **hotel/urls.py** line 176: ⚠️ **ACTIVE LEGACY PATTERN**
  ```python
  path(
      "<slug:slug>/",
      HotelBySlugView.as_view(), 
      name="hotel-by-slug"
  )
  ```
- Documentation files (expected legacy references)

#### `kwargs["slug"]` or `kwargs['slug']` patterns:
- PHASE_4A_STAFF_SERVICE_BOOKINGS.md (guidelines - no code)
- PHASE_4B_GUEST_ZONE_HOTEL_SLUG_NORMALIZATION.md (guidelines - no code)  
- PHASE3_PUBLIC_CLEANUP_PLAN.md (documentation)
- **guests/tests.py** lines 53, 58: Test verification code only

#### `lookup_field = "slug"` patterns:
- **hotel_info/views.py** line 162: ✅ Different context (hotel_info app)
- **hotel/views.py** line 29: ⚠️ **LEGACY PATTERN** in main hotel app
- issues/documentation/create_public_hotel_issues.py: Documentation only

### C) Legacy Aliases and Fallbacks

#### "legacy" patterns found:
- **staff_urls.py** line 196: Comment "App-wrapped routes for legacy compatibility"
- **staff_chat/urls.py** lines 147-153: Legacy endpoints (kept for compatibility)
- **staff_chat/pusher_utils.py** line 35: Legacy function warning
- **voice_recognition/** files: Compatibility wrappers (expected)
- **stock_tracker/** files: Legacy support comments (expected)
- Static files: Expected legacy references

#### "alias", "redirect", "compat", "deprecated" patterns:
- Mostly found in static files and documentation
- **stock_tracker/**, **voice_recognition/** apps: Expected compatibility code
- **staticfiles/**: Framework files (expected)

## PHASE 2 — URLConf Ground Truth

### Currently Registered URL Patterns

#### Main URLConf (HotelMateBackend/urls.py):
```python
# New canonical patterns ✅
path('api/staff/', include('staff_urls')),        # Staff zone
path('api/guest/', include('guest_urls')),        # Guest zone  
path('api/public/', include('public_urls')),      # Public zone

# Legacy routes still active ⚠️
urlpatterns += [path(f'api/{app}/', include(f'{app}.urls')) for app in legacy_apps]
```

#### Active Legacy Endpoints Found:
1. **`/api/hotel/`** → hotel/urls.py (⚠️ ACTIVE)
2. **`/api/hotel/<slug:slug>/`** → HotelBySlugView (⚠️ ACTIVE)

#### Working Canonical Endpoints:
1. **`/api/public/hotel/<hotel_slug>/page/`** ✅
2. **`/api/public/hotel/<hotel_slug>/availability/`** ✅
3. **`/api/public/hotel/<hotel_slug>/pricing/quote/`** ✅
4. **`/api/public/hotel/<hotel_slug>/bookings/`** ✅
5. **`/api/staff/hotel/<hotel_slug>/room-bookings/`** ✅
6. **`/api/staff/hotel/<hotel_slug>/room-bookings/<id>/assign-room/`** ✅
7. **`/api/staff/hotel/<hotel_slug>/room-bookings/<id>/checkout/`** ✅
8. **`/api/staff/hotel/<hotel_slug>/service-bookings/`** ✅

## PHASE 3 — Runtime Verification Results

### Legacy Routes Test (Expected: NO MATCH)
```
✅ /api/hotel/demo-hotel/page/                    → NO MATCH (404) ✅
✅ /api/hotel/demo-hotel/availability/            → NO MATCH (404) ✅
✅ /api/hotel/demo-hotel/pricing/quote/           → NO MATCH (404) ✅
✅ /api/hotel/demo-hotel/bookings/                → NO MATCH (404) ✅
✅ /api/hotel/demo-hotel/bookings/.../payment/... → NO MATCH (404) ✅
✅ /api/hotel/bookings/stripe-webhook/            → NO MATCH (404) ✅
✅ /api/staff/hotel/.../bookings/...              → NO MATCH (404) ✅

⚠️ /api/hotel/                                   → RESOLVES (api-root) ⚠️
⚠️ /api/hotel/demo-hotel/                        → RESOLVES (hotel-by-slug) ⚠️
```

### Canonical Routes Test (Expected: RESOLVES)
```
✅ /api/public/hotel/demo-hotel/page/             → RESOLVES ✅
✅ /api/public/hotel/demo-hotel/availability/     → RESOLVES ✅  
✅ /api/public/hotel/demo-hotel/pricing/quote/    → RESOLVES ✅
✅ /api/public/hotel/demo-hotel/bookings/         → RESOLVES ✅
✅ /api/staff/hotel/.../room-bookings/...         → RESOLVES ✅

⚠️ /api/public/hotel/.../bookings/.../payment/session/ → NO MATCH ⚠️
⚠️ /api/public/hotel/.../bookings/.../payment/verify/  → NO MATCH ⚠️
⚠️ /api/public/bookings/stripe-webhook/                → NO MATCH ⚠️
⚠️ /api/guest/hotels/demo-hotel/                       → NO MATCH ⚠️
```

### Summary Statistics
- **Legacy Routes (should 404):** 11/13 ✅ (85% success)
- **Canonical Routes (should resolve):** 8/12 ✅ (67% success)
- **Overall Status:** ⚠️ AUDIT FAILED

## Proposed Removal Patch

The following changes are required to achieve full legacy route cleanup:

### 1. Remove Legacy Hotel Routes

**File:** `hotel/urls.py`

```diff
# Remove the legacy <slug:slug> pattern
urlpatterns = [
    # ... existing patterns ...
    
-   # Internal/admin endpoints  
-   path("", include(router.urls)),
-   path(
-       "<slug:slug>/",
-       HotelBySlugView.as_view(),
-       name="hotel-by-slug"
-   ),
]
```

### 2. Remove Legacy App Include

**File:** `HotelMateBackend/urls.py`

```diff
-# Legacy routes - kept for backward compatibility  
-# Exclude 'attendance' to avoid namespace conflict with staff zone
-legacy_apps = [app for app in apps if app != 'attendance']
-urlpatterns += [path(f'api/{app}/', include(f'{app}.urls')) for app in legacy_apps]
```

### 3. Fix Missing Payment Routes

**File:** `public_urls.py` (add missing payment endpoints)

```diff
urlpatterns = [
    # ... existing patterns ...
    
+   # Payment endpoints
+   path(
+       "hotel/<str:hotel_slug>/bookings/<str:booking_id>/payment/session/",
+       CreatePaymentSessionView.as_view(),
+       name="create-payment-session"
+   ),
+   path(
+       "hotel/<str:hotel_slug>/bookings/<str:booking_id>/payment/verify/",
+       VerifyPaymentView.as_view(), 
+       name="verify-payment"
+   ),
+   path(
+       "bookings/stripe-webhook/",
+       StripeWebhookView.as_view(),
+       name="stripe-webhook"
+   ),
]
```

### 4. Fix Guest Zone Route

**File:** `guest_urls.py` (verify guest hotel endpoint exists)

```diff
urlpatterns = [
+   path(
+       "hotels/<str:hotel_slug>/",
+       GuestHotelDetailView.as_view(),  # This view needs to exist
+       name="guest-hotel-detail"
+   ),
    # ... other guest patterns
]
```

### 5. Update Legacy lookup_field

**File:** `hotel/views.py`

```diff
class HotelBySlugView(generics.RetrieveAPIView):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
-   lookup_field = "slug"
+   lookup_field = "slug"  # This can be kept if the view is still needed
```

**Note:** The `HotelBySlugView` itself may need to be removed entirely if it's no longer used in the new architecture.

## Post-Patch Verification

After applying the patch, the expected audit results should be:

```
Legacy Routes (should 404): 13/13 ✅ (100%)
Canonical Routes (should resolve): 12/12 ✅ (100%)
Overall Status: 🎉 AUDIT PASSED
```

## Recommendations

1. **Apply the proposed patch immediately** to eliminate legacy route access
2. **Test frontend compatibility** after applying changes
3. **Update API documentation** to reflect only canonical endpoints
4. **Run the audit command regularly** during development: `python manage.py audit_legacy_routes`
5. **Consider adding the audit to CI/CD pipeline** to prevent regression

## Next Steps

1. **Review and approve** the proposed removal patch
2. **Apply changes** in development environment
3. **Test all affected frontend components**
4. **Deploy to staging** and verify with full integration tests
5. **Update any remaining hardcoded legacy URLs** in frontend code

---

**Generated by:** Legacy Routes Auditor  
**Command:** `python manage.py audit_legacy_routes`  
**Audit Script:** `common/management/commands/audit_legacy_routes.py`