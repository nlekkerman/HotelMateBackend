# Frontend API Integration: Fetching Hotels

## Overview
This guide shows how to fetch hotel data from the HotelMateBackend API in your frontend application.

## API Endpoints

### Base URL
```
Development: http://127.0.0.1:8000
Production: https://your-production-domain.com
```

## Understanding Different Homepage Types

Your application has **three different homepage scenarios**:

### 1. 🌐 General Landing Homepage (Public)
**The main marketing page where users choose a hotel**
- **URL Pattern**: `yoursite.com/` or `yoursite.com/home`
- **Endpoint**: `GET /api/hotel/public/`
- **Purpose**: Show all active hotels in a grid/list
- **User Action**: Click a hotel to enter that hotel's guest portal

### 2. 🏨 Hotel-Specific Guest Homepage
**After user selects a hotel from landing page**
- **URL Pattern**: `/guest/hotels/hotel-killarney/` (uses `guest_base_path`)
- **Endpoint**: `GET /api/hotel/public/hotel-killarney/` (get single hotel by slug)
- **Purpose**: Show that specific hotel's guest portal homepage with rooms, services, etc.
- **User Context**: Already inside a specific hotel's guest portal

### 3. 👔 Staff Portal Homepage
**For hotel staff login and management**
- **URL Pattern**: `/staff/hotels/hotel-killarney/` (uses `staff_base_path`)
- **Endpoint**: `GET /api/hotel/public/hotel-killarney/` (get single hotel by slug)
- **Purpose**: Staff dashboard for managing bookings, attendance, etc.
- **User Context**: Staff member logged into a specific hotel

---

## Staff Authentication & URLs

### 🔐 Staff Login (Authentication)

**Staff login is NOT hotel-specific**. Authentication happens at the root level:

```
POST /api/staff/login/
```

**Request Body:**
```json
{
  "username": "staff@hotel.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "staff@hotel.com",
    "email": "staff@hotel.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "staff": {
    "id": 1,
    "hotel": 2,
    "hotel_name": "Hotel Killarney",
    "hotel_slug": "hotel-killarney",
    "department": "Reception",
    "role": "Manager",
    "is_active": true
  }
}
```

**After login, the response includes:**
- `token` - Use this in `Authorization: Token abc123...` header for all subsequent requests
- `staff.hotel_slug` - Use this to navigate to the correct hotel's staff portal
- `staff.hotel_name` - Display in UI

### Staff URL Patterns

**All staff endpoints follow this pattern:**

```
/api/staff/hotels/<hotel_slug>/<app>/
```

**Example URLs for "hotel-killarney":**

#### Authentication (No hotel slug needed)
```
POST /api/staff/login/
POST /api/staff/register/
POST /api/staff/password-reset/
POST /api/staff/password-reset-confirm/
POST /api/staff/save-fcm-token/
```

#### Hotel-Specific Staff Management
```
GET    /api/staff/hotels/hotel-killarney/staff/
POST   /api/staff/hotels/hotel-killarney/staff/
GET    /api/staff/hotels/hotel-killarney/staff/{id}/
PUT    /api/staff/hotels/hotel-killarney/staff/{id}/
DELETE /api/staff/hotels/hotel-killarney/staff/{id}/

GET    /api/staff/hotels/hotel-killarney/staff/metadata/
GET    /api/staff/hotels/hotel-killarney/staff/pending-registrations/
POST   /api/staff/hotels/hotel-killarney/staff/create-staff/
```

#### Attendance Management
```
GET  /api/staff/hotels/hotel-killarney/attendance/
POST /api/staff/hotels/hotel-killarney/attendance/
GET  /api/staff/hotels/hotel-killarney/attendance/{id}/
```

#### Bookings Management
```
GET  /api/staff/hotels/hotel-killarney/bookings/
POST /api/staff/hotels/hotel-killarney/bookings/
GET  /api/staff/hotels/hotel-killarney/bookings/{id}/
```

#### Chat (Staff-to-Staff)
```
GET  /api/staff/hotels/hotel-killarney/staff_chat/
POST /api/staff/hotels/hotel-killarney/staff_chat/messages/
```

#### Hotel Theme/Settings (Common App)
```
GET   /api/staff/hotels/hotel-killarney/common/theme/
POST  /api/staff/hotels/hotel-killarney/common/theme/
PATCH /api/staff/hotels/hotel-killarney/common/theme/
```

**⚠️ Note**: Do NOT add hotel slug again after `/common/`. The URL is `/common/theme/` NOT `/common/hotel-killarney/theme/`

#### And similarly for all other apps:
- `/api/staff/hotels/hotel-killarney/guests/`
- `/api/staff/hotels/hotel-killarney/rooms/`
- `/api/staff/hotels/hotel-killarney/room_services/`
- `/api/staff/hotels/hotel-killarney/maintenance/`
- `/api/staff/hotels/hotel-killarney/entertainment/`
- `/api/staff/hotels/hotel-killarney/stock_tracker/`
- `/api/staff/hotels/hotel-killarney/notifications/`

### Staff Login Flow (Frontend)

```javascript
// 1. Login staff member
async function staffLogin(username, password) {
  const response = await fetch('http://127.0.0.1:8000/api/staff/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  // 2. Store token for future requests
  localStorage.setItem('staffToken', data.token);
  localStorage.setItem('hotelSlug', data.staff.hotel_slug);
  
  // 3. Redirect to staff portal for their hotel
  window.location.href = `/staff/hotels/${data.staff.hotel_slug}/`;
  
  return data;
}

// 4. Make authenticated requests with token
async function fetchStaffData(hotelSlug) {
  const token = localStorage.getItem('staffToken');
  
  const response = await fetch(
    `http://127.0.0.1:8000/api/staff/hotels/${hotelSlug}/staff/`,
    {
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  return await response.json();
}
```

### React Staff Login Example

```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function StaffLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleLogin(e) {
    e.preventDefault();
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/staff/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      if (!response.ok) throw new Error('Login failed');
      
      const data = await response.json();
      
      // Store auth data
      localStorage.setItem('staffToken', data.token);
      localStorage.setItem('staffData', JSON.stringify(data.staff));
      
      // Redirect to staff portal for their hotel
      navigate(`/staff/hotels/${data.staff.hotel_slug}/dashboard`);
      
    } catch (err) {
      setError('Invalid username or password');
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <h2>Staff Login</h2>
      {error && <div className="error">{error}</div>}
      
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      
      <button type="submit">Login</button>
    </form>
  );
}

export default StaffLogin;
```

### Protected Staff API Calls

All staff API calls (except login/register) require authentication token:

```javascript
// API helper with authentication
const staffAPI = {
  // Get auth token from storage
  getToken: () => localStorage.getItem('staffToken'),
  
  // Get hotel slug from storage
  getHotelSlug: () => {
    const staffData = JSON.parse(localStorage.getItem('staffData'));
    return staffData?.hotel_slug;
  },
  
  // Generic authenticated request
  async request(endpoint, options = {}) {
    const token = this.getToken();
    const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (response.status === 401) {
      // Token expired or invalid - redirect to login
      window.location.href = '/staff/login';
      throw new Error('Unauthorized');
    }
    
    return await response.json();
  },
  
  // Example: Get all staff for the hotel
  async getStaff() {
    const slug = this.getHotelSlug();
    return this.request(`/api/staff/hotels/${slug}/staff/`);
  },
  
  // Example: Get all bookings for the hotel
  async getBookings() {
    const slug = this.getHotelSlug();
    return this.request(`/api/staff/hotels/${slug}/bookings/`);
  },
  
  // Example: Create attendance record
  async createAttendance(data) {
    const slug = this.getHotelSlug();
    return this.request(`/api/staff/hotels/${slug}/attendance/`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
};

// Usage examples
async function loadStaffList() {
  const staff = await staffAPI.getStaff();
  console.log('Staff members:', staff);
}

async function loadHotelTheme() {
  const slug = staffAPI.getHotelSlug();
  const token = staffAPI.getToken();
  
  const response = await fetch(
    `http://127.0.0.1:8000/api/staff/hotels/${slug}/common/theme/`,
    {
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const theme = await response.json();
  console.log('Hotel theme:', theme);
  return theme;
}
```

### ✅ Summary: Staff URL Structure

| Purpose | URL Pattern | Requires Hotel Slug? | Requires Auth Token? |
|---------|-------------|---------------------|---------------------|
| Login | `/api/staff/login/` | ❌ No | ❌ No |
| Register | `/api/staff/register/` | ❌ No | ❌ No |
| Password Reset | `/api/staff/password-reset/` | ❌ No | ❌ No |
| Staff Management | `/api/staff/hotels/<slug>/staff/` | ✅ Yes | ✅ Yes |
| Attendance | `/api/staff/hotels/<slug>/attendance/` | ✅ Yes | ✅ Yes |
| Bookings | `/api/staff/hotels/<slug>/bookings/` | ✅ Yes | ✅ Yes |
| Rooms | `/api/staff/hotels/<slug>/rooms/` | ✅ Yes | ✅ Yes |
| Room Services | `/api/staff/hotels/<slug>/room_services/` | ✅ Yes | ✅ Yes |
| All other apps | `/api/staff/hotels/<slug>/<app>/` | ✅ Yes | ✅ Yes |

**Key Points:**
- ✅ Login/auth endpoints are at `/api/staff/` (no hotel slug)
- ✅ After login, response includes `staff.hotel_slug`
- ✅ All hotel-specific endpoints use `/api/staff/hotels/<slug>/<app>/`
- ✅ All authenticated requests need `Authorization: Token <token>` header
- ✅ Staff can only access data for their assigned hotel

---

## 🚨 Troubleshooting: 401 Unauthorized Errors

### Problem: "Invalid token" Error

```
Status: 401 Unauthorized
Response: {"detail": "Invalid token."}
```

**Example of the error you're seeing:**
```
Request URL: https://hotel-porter-d25ad83b12cf.herokuapp.com/api/room_services/hotel-killarney/breakfast-orders/
Status: 401 Unauthorized
Response: {"detail": "Invalid token."}
```

### ❌ Wrong URL Pattern

Your request URL is **INCORRECT**. You're using:
```
❌ /api/room_services/hotel-killarney/breakfast-orders/
```

This is the **LEGACY** pattern (not wrapped in staff zone).

### ✅ Correct URL Pattern

For **STAFF** access, use:
```
✅ /api/staff/hotels/hotel-killarney/room_services/breakfast-orders/
```

### Why This Matters

The Phase 1 routing refactor created **two separate zones**:

1. **STAFF Zone** (requires auth token):
   ```
   /api/staff/hotels/<hotel_slug>/<app>/
   ```

2. **LEGACY Zone** (may have different auth requirements):
   ```
   /api/<app>/<hotel_slug>/
   ```

Your frontend is calling the **LEGACY** endpoint, but you likely need the **STAFF** endpoint with proper authentication.

### Common Causes of 401 Errors

#### 1. Missing Authorization Header
```javascript
// ❌ WRONG - No auth header
fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotels/hotel-killarney/room_services/breakfast-orders/')

// ✅ CORRECT - With auth header
fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotels/hotel-killarney/room_services/breakfast-orders/', {
  headers: {
    'Authorization': 'Token abc123...'
  }
})
```

#### 2. Token Not Stored After Login
```javascript
// After login, MUST store token
const loginData = await staffLogin(username, password);
localStorage.setItem('staffToken', loginData.token);  // ← Critical!
```

#### 3. Token Missing "Token" Prefix
```javascript
// ❌ WRONG - Missing "Token" word
headers: {
  'Authorization': 'abc123...'
}

// ✅ CORRECT - With "Token" prefix
headers: {
  'Authorization': 'Token abc123...'
}
```

#### 4. Token Expired
Tokens can expire. If you get 401, try logging in again:
```javascript
if (response.status === 401) {
  // Clear old token
  localStorage.removeItem('staffToken');
  // Redirect to login
  window.location.href = '/staff/login';
}
```

### Complete Fix for Your Situation

**Update your frontend API calls:**

```javascript
// OLD (WRONG) - Legacy URL pattern
const wrongUrl = 'https://hotel-porter-d25ad83b12cf.herokuapp.com/api/room_services/hotel-killarney/breakfast-orders/';

// NEW (CORRECT) - Staff zone URL pattern
const correctUrl = 'https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotels/hotel-killarney/room_services/breakfast-orders/';

// Make the request with authentication
const token = localStorage.getItem('staffToken');
const response = await fetch(correctUrl, {
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### URL Pattern Comparison

| What You Need | Wrong (Legacy) | Correct (Staff Zone) |
|--------------|----------------|---------------------|
| **Theme Settings** | `/api/common/hotel-killarney/theme/` | `/api/staff/hotels/hotel-killarney/common/theme/` |
| Breakfast Orders | `/api/room_services/hotel-killarney/breakfast-orders/` | `/api/staff/hotels/hotel-killarney/room_services/breakfast-orders/` |
| Staff List | `/api/staff/hotel-killarney/` | `/api/staff/hotels/hotel-killarney/staff/` |
| Attendance | `/api/attendance/hotel-killarney/` | `/api/staff/hotels/hotel-killarney/attendance/` |
| Bookings | `/api/bookings/hotel-killarney/` | `/api/staff/hotels/hotel-killarney/bookings/` |

**⚠️ Important Note for `common` app:**
The `common` app URLs already include `<hotel_slug>` in their path structure. When wrapped in staff zone:
- ❌ **WRONG**: `/api/staff/hotels/hotel-killarney/common/hotel-killarney/theme/` (duplicates hotel slug)
- ✅ **CORRECT**: `/api/staff/hotels/hotel-killarney/common/theme/` (hotel slug only in wrapper)

The staff zone wrapper adds `/hotels/<hotel_slug>/` prefix, so the app's own `<hotel_slug>` parameter is **automatically filled** from the wrapper. Your frontend should NOT add the hotel slug again after `/common/`.

### Quick Diagnostic Checklist

When you get 401 errors, check:

1. ✅ **URL Pattern**: Using `/api/staff/hotels/<slug>/<app>/` format?
2. ✅ **Authorization Header**: Included in request?
3. ✅ **Token Format**: Starts with "Token " (with space)?
4. ✅ **Token Exists**: Check `localStorage.getItem('staffToken')`
5. ✅ **User Logged In**: Did login succeed before this request?
6. ✅ **CORS Headers**: Check browser console for CORS errors

### Testing Authentication in Browser Console

```javascript
// Check if token exists
console.log('Token:', localStorage.getItem('staffToken'));

// Test authenticated request
const token = localStorage.getItem('staffToken');
fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotels/hotel-killarney/room_services/breakfast-orders/', {
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

### If You Still Get 401 After Fixing URL

1. **Re-login to get fresh token:**
   ```javascript
   // Login again
   const response = await fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/login/', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ username: 'your-username', password: 'your-password' })
   });
   const data = await response.json();
   localStorage.setItem('staffToken', data.token);
   console.log('New token:', data.token);
   ```

2. **Verify token in backend:** Check Django admin to see if token exists for your user

3. **Check token model:** Ensure `rest_framework.authtoken` is in `INSTALLED_APPS`

---

## Quick Start: General Landing Homepage

### 🏠 Endpoint for General Landing Page

**Use this endpoint to fetch ALL hotels for your main landing/marketing page:**

```
GET /api/hotel/public/
```

**Full URL (Development):**
```
http://127.0.0.1:8000/api/hotel/public/
```

**Returns**: An **array** of all active hotels, sorted and ready to display.

**Use Case**: Users see all hotels and click one to enter that hotel's guest portal.

### Simple Fetch for Homepage

```javascript
// Fetch all hotels for homepage
fetch('http://127.0.0.1:8000/api/hotel/public/')
  .then(response => response.json())
  .then(hotels => {
    console.log('All hotels:', hotels);
    // hotels is an array of hotel objects
    // Display them on your homepage!
  });
```

### Complete Homepage Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>Hotels</title>
  <style>
    .hotel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
    .hotel-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
    .hotel-card img { width: 100%; height: 200px; object-fit: contain; }
  </style>
</head>
<body>
  <h1>Our Hotels</h1>
  <div id="hotels" class="hotel-grid"></div>

  <script>
    async function loadHotels() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/hotel/public/');
        const hotels = await response.json();
        
        const container = document.getElementById('hotels');
        container.innerHTML = hotels.map(hotel => `
          <div class="hotel-card">
            <img src="${hotel.logo_url}" alt="${hotel.name}">
            <h2>${hotel.name}</h2>
            <p>${hotel.city}${hotel.city && hotel.country ? ', ' : ''}${hotel.country}</p>
            <p>${hotel.short_description || 'Luxury accommodation'}</p>
            <div>
              ${hotel.guest_portal_enabled ? 
                `<a href="${hotel.guest_base_path}">View Guest Portal</a>` : ''}
              ${hotel.staff_portal_enabled ? 
                `<a href="${hotel.staff_base_path}">Staff Login</a>` : ''}
            </div>
          </div>
        `).join('');
      } catch (error) {
        document.getElementById('hotels').innerHTML = 
          '<p>Unable to load hotels. Please try again later.</p>';
        console.error('Error:', error);
      }
    }

    // Load hotels when page loads
    loadHotels();
  </script>
</body>
</html>
```

### React Homepage Component

```jsx
import React, { useState, useEffect } from 'react';

export default function HotelsHomepage() {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/hotel/public/')
      .then(res => res.json())
      .then(data => {
        setHotels(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading hotels...</div>;

  return (
    <div>
      <h1>Our Hotels</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {hotels.map(hotel => (
          <div key={hotel.id} style={{ border: '1px solid #ddd', padding: '20px', borderRadius: '8px' }}>
            <img src={hotel.logo_url} alt={hotel.name} style={{ width: '100%', height: '200px', objectFit: 'contain' }} />
            <h2>{hotel.name}</h2>
            <p>{hotel.city}{hotel.city && hotel.country ? ', ' : ''}{hotel.country}</p>
            <p>{hotel.short_description || 'Luxury accommodation'}</p>
            {hotel.guest_portal_enabled && (
              <a href={hotel.guest_base_path}>View Guest Portal →</a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### What You Get Back

When you call `GET /api/hotel/public/`, you receive an **array** of hotels:

```json
[
  {
    "id": 1,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "city": "Killarney",
    "country": "Ireland",
    "short_description": "Luxury hotel in the heart of Killarney",
    "logo_url": "http://res.cloudinary.com/dg0ssec7u/image/upload/v1761741546/...",
    "guest_base_path": "/guest/hotels/hotel-killarney/",
    "staff_base_path": "/staff/hotels/hotel-killarney/",
    "guest_portal_enabled": true,
    "staff_portal_enabled": true
  },
  {
    "id": 2,
    "name": "Another Hotel",
    ...
  }
]
```

**Key Points:**
- ✅ Only **active** hotels are returned (`is_active=True`)
- ✅ Results are **sorted** by `sort_order` then `name`
- ✅ All hotels have `guest_base_path` and `staff_base_path` computed
- ✅ Check `guest_portal_enabled` / `staff_portal_enabled` before showing portal links
- ✅ `logo_url` is a full Cloudinary URL ready to use in `<img>` tags

### Available Endpoints

#### 1. List All Active Hotels
```
GET /api/hotel/public/
```

**Response Format:**
```json
[
  {
    "id": 1,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "city": "Killarney",
    "country": "Ireland",
    "short_description": "Luxury hotel in the heart of Killarney",
    "logo_url": "http://res.cloudinary.com/dg0ssec7u/image/upload/...",
    "guest_base_path": "/guest/hotels/hotel-killarney/",
    "staff_base_path": "/staff/hotels/hotel-killarney/",
    "guest_portal_enabled": true,
    "staff_portal_enabled": true
  }
]
```

#### 2. Get Single Hotel by Slug
```
GET /api/hotel/public/<slug>/
```

**Example:**
```
GET /api/hotel/public/hotel-killarney/
```

**Response Format:**
```json
{
  "id": 1,
  "name": "Hotel Killarney",
  "slug": "hotel-killarney",
  "city": "Killarney",
  "country": "Ireland",
  "short_description": "Luxury hotel in the heart of Killarney",
  "logo_url": "http://res.cloudinary.com/dg0ssec7u/image/upload/...",
  "guest_base_path": "/guest/hotels/hotel-killarney/",
  "staff_base_path": "/staff/hotels/hotel-killarney/",
  "guest_portal_enabled": true,
  "staff_portal_enabled": true
}
```

## Implementation Examples

### JavaScript (Vanilla/Fetch API)

#### Fetch All Hotels
```javascript
async function fetchAllHotels() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/hotel/public/');
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const hotels = await response.json();
    console.log('Hotels:', hotels);
    return hotels;
  } catch (error) {
    console.error('Error fetching hotels:', error);
    throw error;
  }
}
```

#### Fetch Single Hotel
```javascript
async function fetchHotelBySlug(slug) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/hotel/public/${slug}/`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Hotel not found');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const hotel = await response.json();
    console.log('Hotel:', hotel);
    return hotel;
  } catch (error) {
    console.error('Error fetching hotel:', error);
    throw error;
  }
}
```

#### Display Hotels in UI
```javascript
async function displayHotels() {
  const hotels = await fetchAllHotels();
  const container = document.getElementById('hotels-container');
  
  container.innerHTML = hotels.map(hotel => `
    <div class="hotel-card">
      <img src="${hotel.logo_url}" alt="${hotel.name}" />
      <h3>${hotel.name}</h3>
      <p>${hotel.city}, ${hotel.country}</p>
      <p>${hotel.short_description}</p>
      ${hotel.guest_portal_enabled ? 
        `<a href="${hotel.guest_base_path}">Guest Portal</a>` : ''}
      ${hotel.staff_portal_enabled ? 
        `<a href="${hotel.staff_base_path}">Staff Portal</a>` : ''}
    </div>
  `).join('');
}
```

### React

#### Using Fetch with useState/useEffect
```jsx
import React, { useState, useEffect } from 'react';

function HotelList() {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadHotels() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/hotel/public/');
        if (!response.ok) throw new Error('Failed to fetch hotels');
        const data = await response.json();
        setHotels(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    loadHotels();
  }, []);

  if (loading) return <div>Loading hotels...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="hotel-list">
      {hotels.map(hotel => (
        <div key={hotel.id} className="hotel-card">
          <img src={hotel.logo_url} alt={hotel.name} />
          <h3>{hotel.name}</h3>
          <p>{hotel.city}, {hotel.country}</p>
          <p>{hotel.short_description}</p>
          {hotel.guest_portal_enabled && (
            <a href={hotel.guest_base_path}>Guest Portal</a>
          )}
          {hotel.staff_portal_enabled && (
            <a href={hotel.staff_base_path}>Staff Portal</a>
          )}
        </div>
      ))}
    </div>
  );
}

export default HotelList;
```

#### Custom Hook for Hotel Data
```jsx
import { useState, useEffect } from 'react';

function useHotels() {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/hotel/public/')
      .then(res => res.json())
      .then(data => {
        setHotels(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  return { hotels, loading, error };
}

function useHotel(slug) {
  const [hotel, setHotel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!slug) return;
    
    fetch(`http://127.0.0.1:8000/api/hotel/public/${slug}/`)
      .then(res => res.json())
      .then(data => {
        setHotel(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, [slug]);

  return { hotel, loading, error };
}

export { useHotels, useHotel };
```

#### Usage with Custom Hook
```jsx
import React from 'react';
import { useHotels } from './hooks/useHotels';

function HotelSelector() {
  const { hotels, loading, error } = useHotels();

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error loading hotels</p>;

  return (
    <select>
      {hotels.map(hotel => (
        <option key={hotel.id} value={hotel.slug}>
          {hotel.name}
        </option>
      ))}
    </select>
  );
}
```

### Vue.js

#### Using Composition API
```vue
<template>
  <div class="hotel-list">
    <div v-if="loading">Loading hotels...</div>
    <div v-else-if="error">Error: {{ error }}</div>
    <div v-else>
      <div v-for="hotel in hotels" :key="hotel.id" class="hotel-card">
        <img :src="hotel.logo_url" :alt="hotel.name" />
        <h3>{{ hotel.name }}</h3>
        <p>{{ hotel.city }}, {{ hotel.country }}</p>
        <p>{{ hotel.short_description }}</p>
        <a v-if="hotel.guest_portal_enabled" :href="hotel.guest_base_path">
          Guest Portal
        </a>
        <a v-if="hotel.staff_portal_enabled" :href="hotel.staff_base_path">
          Staff Portal
        </a>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  setup() {
    const hotels = ref([]);
    const loading = ref(true);
    const error = ref(null);

    async function fetchHotels() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/hotel/public/');
        hotels.value = await response.json();
      } catch (err) {
        error.value = err.message;
      } finally {
        loading.value = false;
      }
    }

    onMounted(fetchHotels);

    return { hotels, loading, error };
  }
};
</script>
```

### Angular

#### Hotel Service
```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Hotel {
  id: number;
  name: string;
  slug: string;
  city: string;
  country: string;
  short_description: string;
  logo_url: string;
  guest_base_path: string;
  staff_base_path: string;
  guest_portal_enabled: boolean;
  staff_portal_enabled: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class HotelService {
  private apiUrl = 'http://127.0.0.1:8000/api/hotel/public';

  constructor(private http: HttpClient) {}

  getHotels(): Observable<Hotel[]> {
    return this.http.get<Hotel[]>(`${this.apiUrl}/`);
  }

  getHotelBySlug(slug: string): Observable<Hotel> {
    return this.http.get<Hotel>(`${this.apiUrl}/${slug}/`);
  }
}
```

#### Component Usage
```typescript
import { Component, OnInit } from '@angular/core';
import { HotelService, Hotel } from './services/hotel.service';

@Component({
  selector: 'app-hotel-list',
  template: `
    <div *ngIf="loading">Loading...</div>
    <div *ngIf="error">{{ error }}</div>
    <div *ngIf="!loading && !error">
      <div *ngFor="let hotel of hotels" class="hotel-card">
        <img [src]="hotel.logo_url" [alt]="hotel.name" />
        <h3>{{ hotel.name }}</h3>
        <p>{{ hotel.city }}, {{ hotel.country }}</p>
        <p>{{ hotel.short_description }}</p>
        <a *ngIf="hotel.guest_portal_enabled" [href]="hotel.guest_base_path">
          Guest Portal
        </a>
      </div>
    </div>
  `
})
export class HotelListComponent implements OnInit {
  hotels: Hotel[] = [];
  loading = true;
  error: string | null = null;

  constructor(private hotelService: HotelService) {}

  ngOnInit() {
    this.hotelService.getHotels().subscribe({
      next: (data) => {
        this.hotels = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.message;
        this.loading = false;
      }
    });
  }
}
```

### Axios (Any Framework)

#### Setup Axios Instance
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const hotelAPI = {
  getAllHotels: () => api.get('/hotel/public/'),
  getHotelBySlug: (slug) => api.get(`/hotel/public/${slug}/`),
};
```

#### Usage
```javascript
import { hotelAPI } from './api';

async function loadHotels() {
  try {
    const response = await hotelAPI.getAllHotels();
    console.log('Hotels:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}
```

## CORS Configuration

If you encounter CORS errors, ensure the backend has proper CORS headers configured in `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your frontend URLs
]
```

## Environment Variables

Store API URLs in environment variables:

### React (.env)
```
REACT_APP_API_URL=http://127.0.0.1:8000/api
```

### Vue (.env)
```
VUE_APP_API_URL=http://127.0.0.1:8000/api
```

### Next.js (.env.local)
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

## Response Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique hotel identifier |
| `name` | string | Hotel name |
| `slug` | string | URL-friendly identifier |
| `city` | string | Hotel city location |
| `country` | string | Hotel country location |
| `short_description` | string | Brief hotel description |
| `logo_url` | string | Full Cloudinary URL for hotel logo |
| `guest_base_path` | string | Base path for guest portal routes |
| `staff_base_path` | string | Base path for staff portal routes |
| `guest_portal_enabled` | boolean | Whether guest portal is active |
| `staff_portal_enabled` | boolean | Whether staff portal is active |

## Filtering and Logic

### Only Active Hotels
The API automatically filters to return only `is_active=True` hotels, sorted by `sort_order` then `name`.

### Portal Access Check
```javascript
function canAccessGuestPortal(hotel) {
  return hotel.guest_portal_enabled;
}

function canAccessStaffPortal(hotel) {
  return hotel.staff_portal_enabled;
}

function getPortalUrl(hotel, isStaff = false) {
  if (isStaff && hotel.staff_portal_enabled) {
    return hotel.staff_base_path;
  }
  if (!isStaff && hotel.guest_portal_enabled) {
    return hotel.guest_base_path;
  }
  return null;
}
```

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Request successful
- `404 Not Found` - Hotel slug doesn't exist or hotel is inactive
- `500 Internal Server Error` - Backend error

### Example Error Handler
```javascript
async function fetchHotelWithErrorHandling(slug) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/hotel/public/${slug}/`);
    
    switch (response.status) {
      case 200:
        return await response.json();
      case 404:
        throw new Error('Hotel not found or inactive');
      case 500:
        throw new Error('Server error, please try again later');
      default:
        throw new Error(`Unexpected error: ${response.status}`);
    }
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Network error - check your connection');
    }
    throw error;
  }
}
```

## Testing the API

### Using Browser Console
```javascript
fetch('http://127.0.0.1:8000/api/hotel/public/')
  .then(r => r.json())
  .then(console.log);
```

### Using cURL
```bash
curl http://127.0.0.1:8000/api/hotel/public/
curl http://127.0.0.1:8000/api/hotel/public/hotel-killarney/
```

### Using Postman
1. Create GET request to `http://127.0.0.1:8000/api/hotel/public/`
2. Send request
3. View JSON response

## Best Practices

1. **Cache hotel data** - Hotels don't change frequently, consider caching for 5-10 minutes
2. **Handle loading states** - Always show loading indicators
3. **Error boundaries** - Implement proper error handling and user feedback
4. **Optimize images** - Use Cloudinary transformations on `logo_url` for responsive images
5. **Lazy load** - For hotel detail pages, fetch on-demand rather than preloading all
6. **TypeScript** - Use TypeScript interfaces for type safety
7. **Accessibility** - Include alt text for logos, proper ARIA labels
