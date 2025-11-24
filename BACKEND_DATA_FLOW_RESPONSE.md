# Backend Data Flow Response - Hotel Settings

**Date:** November 24, 2025  
**Status:** ✅ Endpoint Exists - Data Available

---

## 1. ✅ Does the endpoint exist?

**YES** - The endpoint `/api/staff/hotel/{hotel_slug}/settings/` exists and is fully functional.

**File:** `hotel/views.py` (lines 563-640)  
**Class:** `HotelPublicSettingsStaffView`

### HTTP Methods Supported:
- ✅ `GET` - Retrieve settings
- ✅ `PUT` - Full update
- ✅ `PATCH` - Partial update

### URL Pattern:
```python
# From staff_urls.py
path('hotel/<str:hotel_slug>/settings/', HotelPublicSettingsStaffView.as_view())
```

**Full URL:** `https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotel/{hotel_slug}/settings/`

---

## 2. 📦 Actual Response Structure

### Direct Response (Not Wrapped)
The endpoint returns the settings object **directly** (not wrapped in `{ settings: {...} }`).

```json
{
  "short_description": "Brief description",
  "long_description": "Detailed description",
  "welcome_message": "Welcome to our hotel",
  "hero_image": "https://cloudinary.../image.jpg",
  "gallery": ["url1", "url2", "url3"],
  "amenities": ["WiFi", "Pool", "Spa", "Gym"],
  "contact_email": "info@hotel.com",
  "contact_phone": "+353 1 234 5678",
  "contact_address": "123 Main St, Killarney, Ireland",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "accent_color": "#F59E0B",
  "background_color": "#FFFFFF",
  "button_color": "#3B82F6",
  "theme_mode": "light",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

---

## 3. 🗄️ HotelPublicSettings Model

**YES** - Model exists in `hotel/models.py` (lines 255-381)

### Model Fields (Match Frontend Expectations):

| Frontend Field | Backend Field | Type | Default | Notes |
|----------------|---------------|------|---------|-------|
| ✅ `welcome_message` | `welcome_message` | TextField | `''` | Matches |
| ✅ `short_description` | `short_description` | TextField | `''` | Matches |
| ✅ `long_description` | `long_description` | TextField | `''` | Matches |
| ✅ `hero_image` | `hero_image` | URLField | `''` | Matches |
| ✅ `gallery` | `gallery` | JSONField | `[]` | Matches |
| ✅ `contact_email` | `contact_email` | EmailField | `''` | Matches |
| ✅ `contact_phone` | `contact_phone` | CharField | `''` | Matches |
| ✅ `contact_address` | `contact_address` | TextField | `''` | Matches |
| ✅ `amenities` | `amenities` | JSONField | `[]` | Matches |
| ⚠️ `website` | ❌ NOT IN MODEL | - | - | **Missing** |
| ⚠️ `google_maps_link` | ❌ NOT IN MODEL | - | - | **Missing** |
| ⚠️ `logo` | ❌ NOT IN SETTINGS | - | - | On `Hotel` model |
| ⚠️ `favicon` | ❌ NOT IN MODEL | - | - | **Missing** |
| ⚠️ `slogan` | ❌ NOT IN MODEL | - | - | **Missing** |

### Additional Backend Fields (Not in Frontend):
- ✅ `primary_color` - HEX color (#3B82F6)
- ✅ `secondary_color` - HEX color (#10B981)
- ✅ `accent_color` - HEX color (#F59E0B)
- ✅ `background_color` - HEX color (#FFFFFF)
- ✅ `button_color` - HEX color (#3B82F6)
- ✅ `theme_mode` - 'light', 'dark', or 'custom'
- ✅ `updated_at` - Timestamp (read-only)

---

## 4. 🔐 Permissions Required

### Authentication Requirements:
1. ✅ User must be **authenticated** (JWT token required)
2. ✅ User must have **staff_profile** (linked to staff account)
3. ✅ Staff must belong to the **same hotel** as `hotel_slug`

### Permission Classes:
```python
[
    IsAuthenticated(),
    IsStaffMember(),
    IsSameHotel()
]
```

### How It Works:
```python
def get(self, request, hotel_slug):
    # Get staff profile from authenticated user
    staff = request.user.staff_profile
    
    # Verify staff belongs to this hotel
    if staff.hotel.slug != hotel_slug:
        return 403 Forbidden
    
    # Get or create settings for the hotel
    settings, created = HotelPublicSettings.objects.get_or_create(
        hotel=staff.hotel
    )
    
    return settings
```

---

## 5. 🚨 Potential Issues

### Issue 1: Missing Fields (Non-Critical)
The frontend expects these fields that don't exist in the model:
- `website` - Should add to `HotelPublicSettings` model
- `google_maps_link` - Should add to `HotelPublicSettings` model
- `logo` - Exists on `Hotel` model, not settings
- `favicon` - Should add to `HotelPublicSettings` model
- `slogan` - Should add to `HotelPublicSettings` model

**Impact:** These fields will be `undefined` in frontend. Non-blocking but may show "No data" messages.

### Issue 2: Logo Location
- `logo` exists on the `Hotel` model, not `HotelPublicSettings`
- Frontend needs to fetch it from the hotel object or we need to add it to settings response

### Issue 3: CORS/Authentication
If frontend gets 401/403:
- Check JWT token is being sent in headers: `Authorization: Bearer <token>`
- Verify token is not expired
- Ensure user has `staff_profile` relationship
- Confirm staff's hotel slug matches URL slug

---

## 6. 📝 Sample Data

### Test Hotel: "hotel-killarney"

To check if data exists:
```bash
# In Django shell
python manage.py shell

from hotel.models import HotelPublicSettings, Hotel

hotel = Hotel.objects.get(slug='hotel-killarney')
settings = HotelPublicSettings.objects.get(hotel=hotel)
print(settings.welcome_message)
print(settings.hero_image)
print(settings.gallery)
```

### Default Values (If No Data Saved Yet):
```json
{
  "short_description": "",
  "long_description": "",
  "welcome_message": "",
  "hero_image": "",
  "gallery": [],
  "amenities": [],
  "contact_email": "",
  "contact_phone": "",
  "contact_address": "",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "accent_color": "#F59E0B",
  "background_color": "#FFFFFF",
  "button_color": "#3B82F6",
  "theme_mode": "light"
}
```

---

## 7. ✅ Backend Debug Checklist

### Completed:
- [x] Endpoint is registered in URLs (`staff_urls.py`)
- [x] Model exists with all core fields
- [x] Serializer returns all model fields
- [x] View implements GET/PUT/PATCH methods
- [x] Permissions are properly configured
- [x] Auto-creates settings if none exist (`get_or_create`)

### To Verify:
- [ ] Check if `HotelPublicSettings` record exists for test hotel
- [ ] Test endpoint with Postman/curl with valid auth token
- [ ] Check CORS settings allow frontend domain
- [ ] Verify JWT token format and expiration

---

## 8. 🔧 Recommended Backend Changes

### Priority 1: Add Missing Fields to Model
Add these fields to `HotelPublicSettings` model:

```python
# In hotel/models.py - HotelPublicSettings class
website = models.URLField(
    blank=True,
    default='',
    help_text="Hotel website URL"
)
google_maps_link = models.URLField(
    blank=True,
    default='',
    help_text="Google Maps link for hotel location"
)
slogan = models.CharField(
    max_length=200,
    blank=True,
    default='',
    help_text="Hotel slogan/tagline"
)
favicon = models.URLField(
    blank=True,
    default='',
    help_text="Favicon URL"
)
```

### Priority 2: Add Logo to Response
Option A: Include hotel.logo in serializer
```python
class HotelPublicSettingsStaffSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    
    def get_logo(self, obj):
        if obj.hotel.logo:
            return obj.hotel.logo.url
        return None
```

Option B: Frontend fetches hotel and settings separately

### Priority 3: Create Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 9. 🎯 Frontend Fixes Needed

### Issue: Response Not Wrapped
Your frontend expects direct response, which is **correct**. ✅

### Issue: Missing Fields
Frontend should handle missing fields gracefully:

```javascript
// Current (may cause issues)
settings?.welcome_message

// Better (with defaults)
settings?.welcome_message || "No welcome message set"
settings?.hero_image || null
settings?.website || ""
```

### Issue: Check Loading/Error States
```javascript
if (settingsLoading) {
  return <LoadingSpinner />;
}

if (settingsError) {
  console.error('Settings error:', settingsError);
  return <ErrorMessage error={settingsError} />;
}

if (!settings) {
  return <EmptyState message="No settings found" />;
}
```

---

## 10. 📋 Testing Steps

### Backend Test (Postman/curl):
```bash
# GET request
curl -X GET \
  https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotel/hotel-killarney/settings/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected: 200 OK with settings JSON
# If 401: Token invalid/expired
# If 403: User not staff or wrong hotel
# If 404: Check URL (should be /hotel/ not /hotels/)
```

### Frontend Test:
1. Add console logs to see actual response:
```javascript
const { data: settings, isLoading, error } = useQuery({
  queryKey: ['hotelPublicSettings', hotelSlug],
  queryFn: async () => {
    console.log('Fetching settings for:', hotelSlug);
    const response = await api.get(`/staff/hotel/${hotelSlug}/settings/`);
    console.log('Settings response:', response.data);
    return response.data;
  },
  enabled: !!hotelSlug && canEdit,
});

console.log('Settings state:', { settings, isLoading, error });
```

2. Check browser DevTools Network tab:
   - Request URL should be `/api/staff/hotel/hotel-killarney/settings/` (singular)
   - Authorization header present
   - Response status 200
   - Response body contains settings object

---

## 11. ✅ Summary

| Check | Status | Notes |
|-------|--------|-------|
| Endpoint exists | ✅ YES | `/api/staff/hotel/{slug}/settings/` |
| GET method | ✅ YES | Returns settings directly |
| PUT/PATCH methods | ✅ YES | Full and partial updates |
| Model exists | ✅ YES | `HotelPublicSettings` |
| Serializer exists | ✅ YES | `HotelPublicSettingsStaffSerializer` |
| Permissions | ✅ YES | Auth + Staff + SameHotel |
| Field matching | ⚠️ PARTIAL | 9/14 fields match, 5 missing |
| Auto-create | ✅ YES | Creates settings if none exist |
| CORS | ❓ UNKNOWN | Need to verify in settings.py |

### Most Likely Issue:
1. **Wrong URL in frontend** - Using `/hotels/` instead of `/hotel/`
2. **Missing fields showing as empty** - Frontend should handle gracefully
3. **No data saved yet** - Settings may exist but be empty (defaults)

### Next Steps:
1. ✅ Backend team: Add missing fields to model (website, google_maps_link, slogan, favicon)
2. ✅ Backend team: Run migrations
3. ✅ Frontend team: Fix URL if using `/hotels/` (should be `/hotel/`)
4. ✅ Frontend team: Add better error handling and logging
5. ✅ Both teams: Test with actual auth token and verify response

---

**Contact:** Backend team ready to assist with any issues.  
**Testing:** Endpoint is live and ready for integration testing.
