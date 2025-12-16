# Staff Zone URL Routing Guide

## Issue Summary
After implementing the staff zone routing wrapper, existing app URLs that previously worked directly are now wrapped under `/api/staff/hotel/{hotel_slug}/` causing confusion about correct URL patterns.

## Root Cause
The staff zone routing system wraps existing Django app URLs under a staff-specific namespace. Apps that already included hotel slugs in their URL patterns now have **double hotel slugs** in the final URL.

## Current Routing Structure

### Staff Zone Wrapper
```python
# In staff_urls.py
urlpatterns += [
    path(
        f'hotel/<str:hotel_slug>/{app}/',
        include(f'{app}.urls'),
        name=f'staff-{app}'
    )
    for app in STAFF_APPS
]
```

### Apps Included in Staff Zone
```python
STAFF_APPS = [
    'attendance',
    'chat', 
    'common',
    'entertainment',
    'guests',
    'home',
    'hotel_info',
    'maintenance',
    'notifications',
    'room_services',  # ← This is where the issue occurred
    'rooms',
    'staff',
    'staff_chat',
    'stock_tracker',
]
```

## URL Pattern Examples

### Before Staff Zone (OLD - No longer works)
```
GET /api/room_services/hotel-killarney/breakfast-orders/
```

### After Staff Zone (NEW - Correct format)
```
GET /api/staff/hotel/hotel-killarney/room_services/hotel-killarney/breakfast-orders/
```

## Breaking Down the URL Structure

| Component | Source | Example |
|-----------|--------|---------|
| Base API | Main urls.py | `/api/` |
| Staff Zone | staff_urls.py | `staff/` |
| Hotel Scope | Staff wrapper | `hotel/{hotel_slug}/` |
| App Name | Staff wrapper | `room_services/` |
| App-specific Path | App's urls.py | `{hotel_slug}/breakfast-orders/` |

**Result:** `/api/staff/hotel/hotel-killarney/room_services/hotel-killarney/breakfast-orders/`

## Common Staff Zone Endpoints

### Staff Profile
```
GET /api/staff/hotel/{hotel_slug}/me/
```

### Room Services
```
GET /api/staff/hotel/{hotel_slug}/room_services/{hotel_slug}/breakfast-orders/
GET /api/staff/hotel/{hotel_slug}/room_services/{hotel_slug}/orders/
```

### Room Management
```
GET /api/staff/hotel/{hotel_slug}/rooms/{hotel_slug}/rooms/
```

### Stock Tracker
```
GET /api/staff/hotel/{hotel_slug}/stock_tracker/{hotel_slug}/ingredients/
```

## Common Errors

### ❌ Wrong: Using old direct app URLs
```
GET /api/room_services/hotel-killarney/breakfast-orders/
→ 404 Not Found
```

### ❌ Wrong: Forgetting staff zone
```
GET /api/hotel/hotel-killarney/room_services/breakfast-orders/
→ 404 Not Found
```

### ✅ Correct: Full staff zone path
```
GET /api/staff/hotel/hotel-killarney/room_services/hotel-killarney/breakfast-orders/
→ 200 OK
```

## Frontend Migration Checklist

When updating frontend API calls:

1. **Identify the app** - Check which Django app provides the endpoint
2. **Check if wrapped** - Verify if the app is in `STAFF_APPS` list
3. **Add staff prefix** - Prepend `/api/staff/hotel/{hotel_slug}/`
4. **Keep app structure** - Maintain the original app URL structure after the prefix
5. **Handle authentication** - Ensure proper staff authentication headers

## Quick Reference

| Old Pattern | New Pattern |
|-------------|-------------|
| `/api/{app}/...` | `/api/staff/hotel/{hotel_slug}/{app}/...` |
| `/api/room_services/{hotel_slug}/breakfast-orders/` | `/api/staff/hotel/{hotel_slug}/room_services/{hotel_slug}/breakfast-orders/` |
| `/api/rooms/{hotel_slug}/rooms/` | `/api/staff/hotel/{hotel_slug}/rooms/{hotel_slug}/rooms/` |

## Notes

- **Double hotel slugs are intentional** - This is how the current routing system works
- **Authentication required** - All staff zone endpoints require staff authentication
- **Hotel scope enforcement** - Staff can only access data for their assigned hotel
- **Legacy compatibility** - Old direct app URLs are no longer available for staff features

## Future Improvements

Consider refactoring app URL patterns to remove hotel slugs at the app level since the staff zone wrapper already provides hotel scoping. This would eliminate the double hotel slug pattern and create cleaner URLs.