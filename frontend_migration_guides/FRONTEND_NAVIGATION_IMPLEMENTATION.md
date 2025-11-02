# Frontend Navigation Implementation Guide

**Date:** November 2, 2025  
**Backend Status:** ✅ Navigation items seeded for hotel-killarney  
**API:** Database-driven navigation system now active

---

## 🎯 Overview

The backend now provides **hotel-specific navigation items** stored in the database. Each hotel (e.g., hotel-killarney) has 17 navigation items that can be assigned to staff members by super staff admins.

---

## 📊 Available Navigation Items (hotel-killarney)

All 17 navigation items have been added to the database:

| Slug | Name | Path | Display Order |
|------|------|------|---------------|
| `home` | Home | `/` | 1 |
| `chat` | Chat | `/chat` | 2 |
| `reception` | Reception | `/reception` | 3 |
| `rooms` | Rooms | `/rooms` | 4 |
| `guests` | Guests | `/guests` | 5 |
| `roster` | Roster | `/roster` | 6 |
| `staff` | Staff | `/staff` | 7 |
| `restaurants` | Restaurants | `/restaurants` | 8 |
| `bookings` | Bookings | `/bookings` | 9 |
| `maintenance` | Maintenance | `/maintenance` | 10 |
| `hotel_info` | Hotel Info | `/hotel-info` | 11 |
| `good_to_know` | Good to Know | `/good-to-know` | 12 |
| `stock_tracker` | Stock Tracker | `/stock-tracker` | 13 |
| `games` | Games | `/games` | 14 |
| `settings` | Settings | `/settings` | 15 |
| `room_service` | Room Service | `/room-service` | 16 |
| `breakfast` | Breakfast | `/breakfast` | 17 |

---

## 🔌 API Endpoints

### 1. **Get Staff Navigation Items** (Login Response)

**Endpoint:** `POST /api/staff/login/`

**Response includes:**
```json
{
  "user_id": 123,
  "staff_id": 456,
  "username": "john.doe",
  "access_level": "staff_admin",
  "hotel_slug": "hotel-killarney",
  "allowed_navs": ["home", "chat", "staff", "settings"]
}
```

**Frontend Usage:**
- Store `allowed_navs` array in your auth context/store
- Filter navigation menu to only show items with slugs in `allowed_navs`
- **Non-authenticated users**: No `allowed_navs` = hide all navigation

---

### 2. **List All Navigation Items** (For Super Staff Admin)

**Endpoint:** `GET /api/staff/navigation-items/`

**Authentication:** Required (Django superuser or any authenticated user can view)

**Response:**
```json
[
  {
    "id": 1,
    "hotel": {
      "id": 1,
      "slug": "hotel-killarney",
      "name": "Hotel Killarney"
    },
    "name": "Home",
    "slug": "home",
    "path": "/",
    "description": "Dashboard and overview",
    "display_order": 1,
    "is_active": true,
    "created_at": "2025-11-02T10:00:00Z",
    "updated_at": "2025-11-02T10:00:00Z"
  },
  {
    "id": 2,
    "hotel": {
      "id": 1,
      "slug": "hotel-killarney",
      "name": "Hotel Killarney"
    },
    "name": "Chat",
    "slug": "chat",
    "path": "/chat",
    "description": "Staff communication",
    "display_order": 2,
    "is_active": true,
    "created_at": "2025-11-02T10:00:00Z",
    "updated_at": "2025-11-02T10:00:00Z"
  }
  // ... 15 more items
]
```

**Frontend Usage:**
- Super staff admin can see all available navigation items
- Use this to build the permission assignment interface

---

### 3. **Get Staff Navigation Permissions**

**Endpoint:** `GET /api/staff/staff/<staff_id>/navigation-permissions/`

**Authentication:** Required (super_staff_admin only)

**Response:**
```json
{
  "staff_id": 456,
  "staff_name": "John Doe",
  "allowed_navigation_items": [
    {
      "id": 1,
      "slug": "home",
      "name": "Home"
    },
    {
      "id": 2,
      "slug": "chat",
      "name": "Chat"
    }
  ]
}
```

---

### 4. **Update Staff Navigation Permissions**

**Endpoint:** `PUT /api/staff/staff/<staff_id>/navigation-permissions/`

**Authentication:** Required (super_staff_admin only)

**Request Body:**
```json
{
  "navigation_item_ids": [1, 2, 7, 15]
}
```

**Response:**
```json
{
  "message": "Navigation permissions updated successfully",
  "staff_id": 456,
  "allowed_navigation_items": [
    {
      "id": 1,
      "slug": "home",
      "name": "Home"
    },
    {
      "id": 2,
      "slug": "chat",
      "name": "Chat"
    },
    {
      "id": 7,
      "slug": "staff",
      "name": "Staff"
    },
    {
      "id": 15,
      "slug": "settings",
      "name": "Settings"
    }
  ]
}
```

---

## 💻 Frontend Implementation

### 1. **Update Login Flow**

```javascript
// Login API call
const loginUser = async (username, password) => {
  const response = await fetch('/api/staff/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  // Store allowed navigation slugs
  localStorage.setItem('allowedNavs', JSON.stringify(data.allowed_navs || []));
  localStorage.setItem('accessLevel', data.access_level);
  localStorage.setItem('hotelSlug', data.hotel_slug);
  
  return data;
};
```

---

### 2. **Navigation Component (Updated)**

```javascript
import React from 'react';
import { Link } from 'react-router-dom';

const Navigation = () => {
  // Get allowed navigation from storage
  const allowedNavs = JSON.parse(localStorage.getItem('allowedNavs') || '[]');
  const isAuthenticated = !!localStorage.getItem('token');
  
  // Hide navigation completely for non-authenticated users
  if (!isAuthenticated || allowedNavs.length === 0) {
    return null;
  }
  
  // All possible navigation items with their icons
  const allNavItems = [
    { slug: 'home', name: 'Home', path: '/', icon: 'FaHome' },
    { slug: 'chat', name: 'Chat', path: '/chat', icon: 'FaComments' },
    { slug: 'reception', name: 'Reception', path: '/reception', icon: 'FaConciergeBell' },
    { slug: 'rooms', name: 'Rooms', path: '/rooms', icon: 'FaBed' },
    { slug: 'guests', name: 'Guests', path: '/guests', icon: 'FaUsers' },
    { slug: 'roster', name: 'Roster', path: '/roster', icon: 'FaCalendarAlt' },
    { slug: 'staff', name: 'Staff', path: '/staff', icon: 'FaUserTie' },
    { slug: 'restaurants', name: 'Restaurants', path: '/restaurants', icon: 'FaUtensils' },
    { slug: 'bookings', name: 'Bookings', path: '/bookings', icon: 'FaBook' },
    { slug: 'maintenance', name: 'Maintenance', path: '/maintenance', icon: 'FaTools' },
    { slug: 'hotel_info', name: 'Hotel Info', path: '/hotel-info', icon: 'FaInfoCircle' },
    { slug: 'good_to_know', name: 'Good to Know', path: '/good-to-know', icon: 'FaLightbulb' },
    { slug: 'stock_tracker', name: 'Stock Tracker', path: '/stock-tracker', icon: 'FaBoxes' },
    { slug: 'games', name: 'Games', path: '/games', icon: 'FaGamepad' },
    { slug: 'settings', name: 'Settings', path: '/settings', icon: 'FaCog' },
    { slug: 'room_service', name: 'Room Service', path: '/room-service', icon: 'FaRoomService' },
    { slug: 'breakfast', name: 'Breakfast', path: '/breakfast', icon: 'FaCoffee' }
  ];
  
  // Filter to only show allowed navigation items
  const visibleNavItems = allNavItems.filter(item => 
    allowedNavs.includes(item.slug)
  );
  
  return (
    <nav className="navigation">
      {visibleNavItems.map(item => (
        <Link key={item.slug} to={item.path} className="nav-item">
          <i className={item.icon} />
          <span>{item.name}</span>
        </Link>
      ))}
    </nav>
  );
};

export default Navigation;
```

---

### 3. **Navigation Permission Manager (Super Staff Admin)**

```javascript
import React, { useState, useEffect } from 'react';

const NavigationPermissionManager = ({ staffId }) => {
  const [availableNavItems, setAvailableNavItems] = useState([]);
  const [staffNavItems, setStaffNavItems] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  
  useEffect(() => {
    fetchAvailableNavItems();
    fetchStaffPermissions();
  }, [staffId]);
  
  const fetchAvailableNavItems = async () => {
    const response = await fetch('/api/staff/navigation-items/', {
      headers: { 'Authorization': `Token ${localStorage.getItem('token')}` }
    });
    const data = await response.json();
    setAvailableNavItems(data);
  };
  
  const fetchStaffPermissions = async () => {
    const response = await fetch(
      `/api/staff/staff/${staffId}/navigation-permissions/`,
      { headers: { 'Authorization': `Token ${localStorage.getItem('token')}` }}
    );
    const data = await response.json();
    setStaffNavItems(data.allowed_navigation_items);
    setSelectedIds(data.allowed_navigation_items.map(item => item.id));
  };
  
  const handleToggle = (navItemId) => {
    setSelectedIds(prev => 
      prev.includes(navItemId)
        ? prev.filter(id => id !== navItemId)
        : [...prev, navItemId]
    );
  };
  
  const handleSave = async () => {
    const response = await fetch(
      `/api/staff/staff/${staffId}/navigation-permissions/`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ navigation_item_ids: selectedIds })
      }
    );
    
    if (response.ok) {
      alert('Navigation permissions updated successfully!');
      fetchStaffPermissions();
    }
  };
  
  return (
    <div className="nav-permission-manager">
      <h3>Assign Navigation Items</h3>
      <div className="checkbox-list">
        {availableNavItems.map(item => (
          <label key={item.id} className="checkbox-item">
            <input
              type="checkbox"
              checked={selectedIds.includes(item.id)}
              onChange={() => handleToggle(item.id)}
            />
            <span>{item.name}</span>
            <small>{item.description}</small>
          </label>
        ))}
      </div>
      <button onClick={handleSave} className="save-btn">
        Save Permissions
      </button>
    </div>
  );
};

export default NavigationPermissionManager;
```

---

## 🔒 Security Rules

### **Non-Authenticated Users**
- ❌ **NO navigation visible at all**
- ❌ Cannot see any menu items
- ✅ Only see login page or QR code scanner

### **Authenticated Staff**
- ✅ See only navigation items assigned to them
- ✅ `allowed_navs` array determines visibility
- ❌ Cannot access routes they don't have navigation for

### **Super Staff Admin**
- ✅ Can assign navigation items to staff members
- ✅ Can view all available navigation items
- ✅ Manages permissions via checkbox interface

### **Django Superuser**
- ✅ Can create/edit/delete navigation items via Django Admin
- ✅ Full control over navigation system
- ✅ Can activate/deactivate navigation items

---

## 🧪 Testing Checklist

### Test as Non-Authenticated User:
- [ ] Navigation is completely hidden
- [ ] Login page is accessible
- [ ] No navigation menu appears anywhere

### Test as Regular Staff:
- [ ] Login shows only assigned navigation items
- [ ] `allowed_navs` array contains expected slugs
- [ ] Navigation menu only shows allowed items
- [ ] Cannot access routes not in `allowed_navs`

### Test as Super Staff Admin:
- [ ] Can view list of all navigation items
- [ ] Can access navigation permission manager
- [ ] Can assign/remove navigation items from staff
- [ ] Changes save successfully
- [ ] Staff member sees updated navigation after re-login

### Test as Django Superuser:
- [ ] Can create new navigation items in admin
- [ ] Can edit existing navigation items
- [ ] Can deactivate navigation items
- [ ] Deactivated items don't appear for staff

---

## 🔄 Migration from Old System

### Old Way (Hardcoded):
```javascript
// ❌ DON'T DO THIS ANYMORE
const getNavigationByRole = (role, department) => {
  if (role === 'admin') return allNavItems;
  if (department === 'kitchen') return kitchenNavItems;
  // ... complex logic
};
```

### New Way (Database-Driven):
```javascript
// ✅ DO THIS INSTEAD
const allowedNavs = JSON.parse(localStorage.getItem('allowedNavs') || '[]');
const visibleNavs = allNavItems.filter(item => allowedNavs.includes(item.slug));
```

---

## 📋 Implementation Steps

1. **Update Login Component**
   - Store `allowed_navs` from login response
   - Store `access_level` and `hotel_slug`

2. **Update Navigation Component**
   - Check if user is authenticated
   - Filter navigation items by `allowed_navs`
   - Hide completely for non-authenticated users

3. **Create Permission Manager Component**
   - Only visible to super_staff_admin
   - Fetch available navigation items
   - Checkbox interface for assignment
   - Save changes to backend

4. **Update Route Protection**
   - Check `allowed_navs` before allowing route access
   - Redirect to home if unauthorized

5. **Test All User Types**
   - Non-authenticated: no navigation
   - Regular staff: filtered navigation
   - Super staff admin: can manage permissions
   - Django superuser: full admin access

---

## 🎨 UI/UX Recommendations

### Navigation Menu:
- Display items in `display_order` sequence
- Show icons for visual recognition
- Highlight active route
- Responsive mobile menu

### Permission Manager:
- Group navigation items by category
- Show description tooltips
- "Select All" / "Deselect All" buttons
- Search/filter functionality for large lists
- Save confirmation message

### Login Page:
- Clear message: "Navigation available after login"
- QR code option for registration
- Smooth transition to dashboard after login

---

## 🚨 Common Issues & Solutions

### Issue: Navigation not updating after permission change
**Solution:** Staff member must re-login to get updated `allowed_navs`

### Issue: Navigation shows for non-authenticated users
**Solution:** Check `isAuthenticated` flag before rendering Navigation component

### Issue: 404 errors when staff accesses routes
**Solution:** Implement route protection that checks `allowed_navs` before rendering

### Issue: Super admin can't assign permissions
**Solution:** Verify `access_level === 'super_staff_admin'` in backend

---

## 📞 Backend Support

**Questions?** The backend team can help with:
- API endpoint issues
- Permission logic questions
- Adding new navigation items to database
- Seeding navigation for other hotels

**Django Admin Access:**
- Navigate to: `/admin/staff/navigationitem/`
- Create, edit, or deactivate navigation items
- Assign items to staff via: `/admin/staff/staff/`

---

## ✅ Summary

### Key Points:
1. **17 navigation items** available for hotel-killarney
2. **Database-driven** - no more hardcoded permissions
3. **`allowed_navs` array** controls what each staff member sees
4. **Super staff admin** assigns navigation via checkbox UI
5. **Non-authenticated users** see NO navigation at all
6. **Hotel-specific** - each hotel can have different items

### Next Steps:
1. Implement updated Navigation component
2. Add Permission Manager for super admins
3. Hide navigation for non-authenticated users
4. Test with different user types
5. Remove old hardcoded permission logic

---

**Document Version:** 1.0  
**Status:** ✅ Ready for Frontend Implementation  
**Backend Status:** ✅ Database seeded with 17 navigation items

**Happy Coding! 🚀**
