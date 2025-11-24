# Phase 1 – Frontend API Integration Guide

This document provides comprehensive API documentation for integrating the Phase 1 backend features into the frontend application.

## Table of Contents
1. [Authentication & Permissions](#authentication--permissions)
2. [Hotel Public Settings API](#hotel-public-settings-api)
3. [Staff Bookings Management API](#staff-bookings-management-api)
4. [Implementation Checklist](#implementation-checklist)

---

## Authentication & Permissions

### Staff Authentication
All staff endpoints require authentication and use the following permission pattern:
- `IsAuthenticated` - User must be logged in
- `IsStaffMember` - User must have a `staff_profile`
- `IsSameHotel` - Staff must belong to the hotel in the URL (`hotel_slug`)

### Staff Profile Data (`/me` endpoint)

The staff profile endpoint has been extended to include fields needed for frontend permission checks.

**Endpoint:** `GET /api/staff/{hotel_slug}/me/`

**Response includes:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@hotel.com",
  "hotel": 1,
  "hotel_name": "Grand Hotel",
  "hotel_slug": "grand-hotel",
  "access_level": "staff_admin",
  "role": 2,
  "role_slug": "manager",
  "is_staff_member": true,
  "department_detail": { /* ... */ },
  "role_detail": { /* ... */ },
  "allowed_navs": ["home", "bookings", "settings"]
}
```

**Frontend Permission Derivation:**
```javascript
function canEditPublicPage(staff) {
  // Check if user is staff admin or super staff admin
  const hasAdminAccess = ['staff_admin', 'super_staff_admin'].includes(staff.access_level);
  
  // Check if user has manager/admin role
  const hasManagerRole = staff.role_slug && ['manager', 'admin'].includes(staff.role_slug);
  
  return hasAdminAccess || hasManagerRole;
}

function canConfirmBookings(staff) {
  // Same logic - can be customized based on requirements
  const hasAdminAccess = ['staff_admin', 'super_staff_admin'].includes(staff.access_level);
  const hasManagerRole = staff.role_slug && ['manager', 'admin'].includes(staff.role_slug);
  
  return hasAdminAccess || hasManagerRole;
}
```

---

## Hotel Public Settings API

### 1. Get Hotel Theme/Branding (Public - Quick Access)

Retrieve only hotel theme and branding colors. Lightweight endpoint for quick theme loading.

**Endpoint:** `GET /api/common/{hotel_slug}/theme/`

**Authentication:** None (public endpoint)

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel slug identifier

**Response:** `200 OK`
```json
{
  "hotel_slug": "hotel-killarney",
  "hotel_name": "Grand Hotel Killarney",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "accent_color": "#F59E0B",
  "background_color": "#FFFFFF",
  "button_color": "#3B82F6",
  "theme_mode": "light"
}
```

**Error Responses:**
- `404 Not Found` - Hotel with given slug doesn't exist or is inactive

**Frontend Usage:**
```javascript
async function getHotelTheme(hotelSlug) {
  const response = await fetch(`/api/common/${hotelSlug}/theme/`);
  if (!response.ok) {
    throw new Error('Hotel theme not found');
  }
  const theme = await response.json();
  
  // Apply theme to document
  document.documentElement.style.setProperty('--primary-color', theme.primary_color);
  document.documentElement.style.setProperty('--secondary-color', theme.secondary_color);
  document.documentElement.style.setProperty('--accent-color', theme.accent_color);
  document.documentElement.style.setProperty('--bg-color', theme.background_color);
  document.documentElement.style.setProperty('--btn-color', theme.button_color);
  
  return theme;
}
```

---

### 2. Get Full Public Hotel Settings (Public)

Retrieve complete hotel public settings including content, contact, and theme for rendering the public hotel page.

**Endpoint:** `GET /api/public/hotels/{hotel_slug}/settings/`

**Authentication:** None (public endpoint)

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel slug identifier

**Response:** `200 OK`
```json
{
  "short_description": "Luxury hotel in the heart of the city",
  "long_description": "Experience unparalleled comfort...",
  "welcome_message": "Welcome to our hotel!",
  "hero_image": "https://cloudinary.com/...",
  "gallery": [
    "https://cloudinary.com/img1.jpg",
    "https://cloudinary.com/img2.jpg"
  ],
  "amenities": [
    "Free WiFi",
    "Swimming Pool",
    "Spa",
    "Restaurant",
    "Gym"
  ],
  "contact_email": "info@hotel.com",
  "contact_phone": "+1234567890",
  "contact_address": "123 Main St, City, Country",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "accent_color": "#F59E0B",
  "background_color": "#FFFFFF",
  "button_color": "#3B82F6",
  "theme_mode": "light"
}
```

**Error Responses:**
- `404 Not Found` - Hotel with given slug doesn't exist

**Frontend Usage:**
```javascript
async function getHotelSettings(hotelSlug) {
  const response = await fetch(`/api/public/hotels/${hotelSlug}/settings/`);
  if (!response.ok) {
    throw new Error('Hotel not found');
  }
  return await response.json();
}

// Apply theme colors
function applyHotelTheme(settings) {
  document.documentElement.style.setProperty('--primary-color', settings.primary_color);
  document.documentElement.style.setProperty('--secondary-color', settings.secondary_color);
  document.documentElement.style.setProperty('--accent-color', settings.accent_color);
  document.documentElement.style.setProperty('--bg-color', settings.background_color);
  document.documentElement.style.setProperty('--btn-color', settings.button_color);
  
  if (settings.theme_mode === 'dark') {
    document.body.classList.add('dark-mode');
  }
}
```

---

### 3. Retrieve & Update Hotel Settings (Staff Only)

Retrieve and update hotel public settings. Only authenticated staff belonging to the hotel can access.

**Endpoints:**
- `GET /api/staff/hotels/{hotel_slug}/settings/` - Retrieve current settings
- `PUT /api/staff/hotels/{hotel_slug}/settings/` - Full update
- `PATCH /api/staff/hotels/{hotel_slug}/settings/` - Partial update

**Authentication:** Required (Token)

**Headers:**
```
Authorization: Token {your_auth_token}
Content-Type: application/json  (not needed for GET)
```

**URL Parameters:**
- `hotel_slug` (string, required) - Must match staff's hotel

#### GET - Retrieve Settings

**Response:** `200 OK`
```json
{
  "short_description": "Experience luxury...",
  "long_description": "Full description...",
  "welcome_message": "Welcome!",
  "hero_image": "https://cloudinary.com/hero.jpg",
  "gallery": ["https://cloudinary.com/img1.jpg", "https://cloudinary.com/img2.jpg"],
  "amenities": ["WiFi", "Pool", "Spa"],
  "contact_email": "contact@hotel.com",
  "contact_phone": "+1234567890",
  "contact_address": "123 Main St, City, Country",
  "primary_color": "#2C3E50",
  "secondary_color": "#3498DB",
  "accent_color": "#E74C3C",
  "background_color": "#ECF0F1",
  "button_color": "#E67E22",
  "theme_mode": "light",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

#### PUT/PATCH - Update Settings

**Request Body:** (All fields optional for PATCH)
```json
{
  "short_description": "Updated description",
  "long_description": "Updated long description",
  "welcome_message": "Welcome!",
  "hero_image": "https://cloudinary.com/hero.jpg",
  "gallery": ["https://cloudinary.com/img1.jpg"],
  "amenities": ["WiFi", "Pool"],
  "contact_email": "contact@hotel.com",
  "contact_phone": "+1234567890",
  "contact_address": "123 Main St",
  "primary_color": "#FF0000",
  "secondary_color": "#00FF00",
  "accent_color": "#0000FF",
  "background_color": "#FFFFFF",
  "button_color": "#FF0000",
  "theme_mode": "dark"
}
```

**Response:** `200 OK`
```json
{
  "short_description": "Updated description",
  "long_description": "Updated long description",
  // ... all other fields
  "updated_at": "2025-11-24T10:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - No authentication token provided
- `403 Forbidden` - User is not staff or doesn't belong to this hotel
- `400 Bad Request` - Invalid data (e.g., invalid color format) [PUT/PATCH only]
- `404 Not Found` - Hotel not found

**Frontend Usage:**
```javascript
// GET - Retrieve current settings
async function getHotelSettings(hotelSlug, authToken) {
  const response = await fetch(`/api/staff/hotels/${hotelSlug}/settings/`, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${authToken}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch settings');
  }
  
  return await response.json();
}

// PUT - Full update
async function updateHotelSettings(hotelSlug, settings, authToken) {
  const response = await fetch(`/api/staff/hotels/${hotelSlug}/settings/`, {
    method: 'PUT',
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(settings)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to update settings');
  }
  
  return await response.json();
}

// Example: Update only colors
async function updateColors(hotelSlug, colors, authToken) {
  const response = await fetch(`/api/staff/hotels/${hotelSlug}/settings/`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      primary_color: colors.primary,
      secondary_color: colors.secondary,
      accent_color: colors.accent
    })
  });
  
  return await response.json();
}
```

---

## Staff Bookings Management API

### 3. List Hotel Bookings (Staff Only)

Retrieve list of bookings for the staff's hotel with optional filtering.

**Endpoint:** `GET /api/staff/hotels/{hotel_slug}/bookings/`

**Authentication:** Required (Token)

**Headers:**
```
Authorization: Token {your_auth_token}
```

**URL Parameters:**
- `hotel_slug` (string, required) - Must match staff's hotel

**Query Parameters:**
- `status` (string, optional) - Filter by booking status
  - Possible values: `PENDING_PAYMENT`, `CONFIRMED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`
- `start_date` (date, optional) - Filter bookings with check-in >= this date (YYYY-MM-DD)
- `end_date` (date, optional) - Filter bookings with check-out <= this date (YYYY-MM-DD)

**Example URLs:**
```
/api/staff/hotels/grand-hotel/bookings/
/api/staff/hotels/grand-hotel/bookings/?status=PENDING_PAYMENT
/api/staff/hotels/grand-hotel/bookings/?start_date=2025-12-01&end_date=2025-12-31
/api/staff/hotels/grand-hotel/bookings/?status=CONFIRMED&start_date=2025-12-01
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "booking_id": "BK-2025-ABC123",
    "confirmation_number": "GRA-2025-XY12",
    "hotel_name": "Grand Hotel",
    "room_type_name": "Deluxe Suite",
    "guest_name": "John Smith",
    "guest_email": "john@example.com",
    "guest_phone": "+1234567890",
    "check_in": "2025-12-15",
    "check_out": "2025-12-20",
    "nights": 5,
    "adults": 2,
    "children": 1,
    "total_amount": "599.99",
    "currency": "EUR",
    "status": "CONFIRMED",
    "created_at": "2025-11-20T10:30:00Z",
    "paid_at": "2025-11-20T10:35:00Z"
  }
  // ... more bookings
]
```

**Error Responses:**
- `401 Unauthorized` - No authentication token
- `403 Forbidden` - User is not staff or doesn't belong to this hotel
- `400 Bad Request` - Invalid date format

**Frontend Usage:**
```javascript
async function getHotelBookings(hotelSlug, filters, authToken) {
  const params = new URLSearchParams();
  
  if (filters.status) {
    params.append('status', filters.status);
  }
  if (filters.startDate) {
    params.append('start_date', filters.startDate); // YYYY-MM-DD
  }
  if (filters.endDate) {
    params.append('end_date', filters.endDate); // YYYY-MM-DD
  }
  
  const url = `/api/staff/hotels/${hotelSlug}/bookings/?${params.toString()}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Token ${authToken}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch bookings');
  }
  
  return await response.json();
}

// Example: Get pending bookings
const pendingBookings = await getHotelBookings('grand-hotel', {
  status: 'PENDING_PAYMENT'
}, authToken);

// Example: Get bookings for December
const decemberBookings = await getHotelBookings('grand-hotel', {
  startDate: '2025-12-01',
  endDate: '2025-12-31'
}, authToken);
```

---

### 5. Confirm Booking (Staff Only)

Confirm a pending booking and trigger confirmation email to guest.

**Endpoint:** `POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/confirm/`

**Authentication:** Required (Token)

**Headers:**
```
Authorization: Token {your_auth_token}
Content-Type: application/json
```

**URL Parameters:**
- `hotel_slug` (string, required) - Must match staff's hotel
- `booking_id` (string, required) - Booking ID (e.g., "BK-2025-ABC123")

**Request Body:** Empty `{}`

**Response:** `200 OK`
```json
{
  "message": "Booking confirmed successfully",
  "booking": {
    "id": 1,
    "booking_id": "BK-2025-ABC123",
    "confirmation_number": "GRA-2025-XY12",
    "hotel_name": "Grand Hotel",
    "room_type_name": "Deluxe Suite",
    "guest_name": "John Smith",
    "guest_first_name": "John",
    "guest_last_name": "Smith",
    "guest_email": "john@example.com",
    "guest_phone": "+1234567890",
    "check_in": "2025-12-15",
    "check_out": "2025-12-20",
    "nights": 5,
    "adults": 2,
    "children": 1,
    "total_amount": "599.99",
    "currency": "EUR",
    "status": "CONFIRMED",
    "special_requests": "Late check-in",
    "promo_code": "",
    "payment_reference": "stripe_xyz123",
    "payment_provider": "stripe",
    "paid_at": "2025-11-20T10:35:00Z",
    "created_at": "2025-11-20T10:30:00Z",
    "updated_at": "2025-11-24T14:22:00Z",
    "internal_notes": ""
  }
}
```

**Error Responses:**
- `401 Unauthorized` - No authentication token
- `403 Forbidden` - User is not staff or doesn't belong to this hotel
- `404 Not Found` - Booking not found
- `400 Bad Request` - Booking cannot be confirmed (e.g., already cancelled)

**Special Behaviors:**
- If booking is already `CONFIRMED`, returns 200 with message "Booking is already confirmed"
- Automatically sends confirmation email to guest (failures logged but don't prevent confirmation)
- Updates booking status from any valid state to `CONFIRMED`

**Frontend Usage:**
```javascript
async function confirmBooking(hotelSlug, bookingId, authToken) {
  const response = await fetch(
    `/api/staff/hotels/${hotelSlug}/bookings/${bookingId}/confirm/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to confirm booking');
  }
  
  return await response.json();
}

// Example usage with UI feedback
async function handleConfirmBooking(bookingId) {
  try {
    showLoader();
    const result = await confirmBooking('grand-hotel', bookingId, authToken);
    showSuccess(result.message);
    
    // Update UI with confirmed booking
    updateBookingInList(result.booking);
    
    // Notify that email was sent
    showNotification('Confirmation email sent to guest');
  } catch (error) {
    showError(error.message);
  } finally {
    hideLoader();
  }
}
```

---

## Implementation Checklist

### Public Hotel Page
- [ ] Fetch hotel settings on page load
- [ ] Apply theme colors dynamically
- [ ] Display hero image and gallery
- [ ] Show amenities list
- [ ] Display contact information
- [ ] Handle missing/default values gracefully

### Staff Settings Editor
- [ ] Check staff permissions (`canEditPublicPage`)
- [ ] Load current settings
- [ ] Implement form with all fields
- [ ] Add color picker for brand colors
- [ ] Add image uploader for hero/gallery
- [ ] Implement amenities list editor
- [ ] Save with PUT (full update) or PATCH (partial)
- [ ] Show success/error feedback
- [ ] Handle validation errors

### Staff Bookings Dashboard
- [ ] Check staff authentication
- [ ] Fetch bookings list on load
- [ ] Implement status filter dropdown
- [ ] Implement date range filters
- [ ] Display booking cards/table
- [ ] Show booking details modal
- [ ] Add confirm button (with permission check)
- [ ] Handle confirmation with feedback
- [ ] Refresh list after confirmation

### Error Handling
- [ ] Handle 401 (redirect to login)
- [ ] Handle 403 (show permission denied)
- [ ] Handle 404 (show not found)
- [ ] Handle 400 (show validation errors)
- [ ] Handle network errors
- [ ] Show user-friendly error messages

### Best Practices
- [ ] Store auth token securely
- [ ] Add loading states
- [ ] Implement optimistic updates where appropriate
- [ ] Add confirmation dialogs for destructive actions
- [ ] Implement proper form validation
- [ ] Cache settings data appropriately
- [ ] Add retry logic for failed requests
- [ ] Log errors for debugging

---

## Field Validation Rules

### Hotel Settings
- **Colors**: Must be valid HEX format (e.g., `#FF0000`, `#3B82F6`)
- **Theme Mode**: Must be one of: `light`, `dark`, `custom`
- **Gallery**: Array of valid URLs
- **Amenities**: Array of strings
- **Email**: Must be valid email format
- **Phone**: Any string (no specific format enforced)
- **URLs**: Must be valid URL format when provided

### Booking Filters
- **Dates**: Must be in `YYYY-MM-DD` format
- **Status**: Must match exact values: `PENDING_PAYMENT`, `CONFIRMED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`

---

## Support & Troubleshooting

### Common Issues

**403 Forbidden on staff endpoints:**
- Ensure user is authenticated
- Verify user has staff profile
- Check hotel_slug matches staff's hotel

**Settings not loading:**
- Check hotel_slug is correct
- Verify hotel exists and is active
- Settings are auto-created if missing (returns defaults)

**Booking confirmation fails:**
- Check booking exists and belongs to hotel
- Verify booking is not cancelled
- Ensure staff has proper permissions

**Email not received:**
- Email failures are logged but don't prevent confirmation
- Check spam folder
- Verify guest email address is correct
- Check Django email backend configuration

---

## Additional Notes

### Email Behavior
- Confirmation emails are sent automatically when booking is confirmed
- Email failures are logged but don't prevent the confirmation from succeeding
- Email includes booking details, hotel contact info, and confirmation number

### Performance Considerations
- Settings are cached at model level (auto-created on first access)
- Bookings list is ordered by creation date (newest first)
- Consider pagination for large booking lists (not yet implemented)

### Future Enhancements (Not Yet Implemented)
- Pagination for bookings list
- Booking search by guest name/email
- Bulk booking operations
- Export bookings to CSV
- Advanced reporting and analytics
- `confirmed_by` and `confirmed_at` fields in booking model
- Role-based restrictions (currently commented out in code)

---

**Document Version:** 1.0  
**Last Updated:** November 24, 2025  
**Backend Version:** Phase 1 Complete
