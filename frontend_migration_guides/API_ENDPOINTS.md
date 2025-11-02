# Navigation API Endpoints for Frontend

## 🔌 Correct API Endpoints

### 1. **Get All Navigation Items for a Hotel**

```
GET /api/staff/navigation-items/?hotel_slug=hotel-killarney
```

**Headers:**
```
Authorization: Token YOUR_AUTH_TOKEN
```

**Response:**
```json
[
  {
    "id": 1,
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
    "name": "Chat",
    "slug": "chat",
    "path": "/chat",
    "description": "Staff communication",
    "display_order": 2,
    "is_active": true,
    "created_at": "2025-11-02T10:00:00Z",
    "updated_at": "2025-11-02T10:00:00Z"
  }
  // ... 15 more items (17 total)
]
```

**JavaScript Example:**
```javascript
const fetchNavigationItems = async (hotelSlug) => {
  const response = await fetch(
    `/api/staff/navigation-items/?hotel_slug=${hotelSlug}`,
    {
      headers: {
        'Authorization': `Token ${localStorage.getItem('token')}`
      }
    }
  );
  const data = await response.json();
  return data;
};

// Usage
const navItems = await fetchNavigationItems('hotel-killarney');
console.log(`Found ${navItems.length} navigation items`); // 17
```

---

### 2. **Get Staff's Assigned Navigation (in Staff Details)**

```
GET /api/staff/hotel-killarney/{staff_id}/
```

**Headers:**
```
Authorization: Token YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@hotel.com",
  "access_level": "regular_staff",
  "hotel_name": "Hotel Killarney",
  "allowed_navs": ["home", "chat", "staff"],
  "department_detail": {...},
  "role_detail": {...}
}
```

**JavaScript Example:**
```javascript
const fetchStaffDetails = async (hotelSlug, staffId) => {
  const response = await fetch(
    `/api/staff/${hotelSlug}/${staffId}/`,
    {
      headers: {
        'Authorization': `Token ${localStorage.getItem('token')}`
      }
    }
  );
  const data = await response.json();
  return data;
};

// Usage
const staff = await fetchStaffDetails('hotel-killarney', 123);
console.log(staff.allowed_navs); // ["home", "chat", "staff"]
```

---

### 3. **Get Staff's Navigation Permissions (for editing)**

```
GET /api/staff/staff/{staff_id}/navigation-permissions/
```

**Who can access:** Only `super_staff_admin`

**Headers:**
```
Authorization: Token YOUR_AUTH_TOKEN
```

**Response:**
```json
{
  "staff_id": 123,
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
    },
    {
      "id": 7,
      "slug": "staff",
      "name": "Staff"
    }
  ]
}
```

**JavaScript Example:**
```javascript
const fetchStaffNavPermissions = async (staffId) => {
  const response = await fetch(
    `/api/staff/staff/${staffId}/navigation-permissions/`,
    {
      headers: {
        'Authorization': `Token ${localStorage.getItem('token')}`
      }
    }
  );
  const data = await response.json();
  return data;
};

// Usage
const permissions = await fetchStaffNavPermissions(123);
console.log(permissions.allowed_navigation_items); // Array of assigned items
```

---

### 4. **Update Staff's Navigation Permissions**

```
PUT /api/staff/staff/{staff_id}/navigation-permissions/
```

**Who can access:** Only `super_staff_admin`

**Headers:**
```
Authorization: Token YOUR_AUTH_TOKEN
Content-Type: application/json
```

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
  "staff_id": 123,
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

**JavaScript Example:**
```javascript
const updateStaffNavPermissions = async (staffId, navItemIds) => {
  const response = await fetch(
    `/api/staff/staff/${staffId}/navigation-permissions/`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Token ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        navigation_item_ids: navItemIds
      })
    }
  );
  const data = await response.json();
  return data;
};

// Usage: Assign Home, Chat, Staff, Settings to staff member
await updateStaffNavPermissions(123, [1, 2, 7, 15]);
```

---

### 5. **Login (includes allowed_navs)**

```
POST /api/staff/login/
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "john.doe",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "abc123def456...",
  "user_id": 789,
  "staff_id": 123,
  "username": "john.doe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@hotel.com",
  "access_level": "regular_staff",
  "hotel_slug": "hotel-killarney",
  "hotel_name": "Hotel Killarney",
  "allowed_navs": ["home", "chat", "staff"],
  "department": {...},
  "role": {...}
}
```

**JavaScript Example:**
```javascript
const login = async (username, password) => {
  const response = await fetch('/api/staff/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  
  // Store for later use
  localStorage.setItem('token', data.token);
  localStorage.setItem('allowedNavs', JSON.stringify(data.allowed_navs));
  localStorage.setItem('hotelSlug', data.hotel_slug);
  
  return data;
};
```

---

## 🎯 Complete Frontend Flow

### Step 1: Build Checkbox UI Component

```javascript
import React, { useState, useEffect } from 'react';

const NavigationPermissionEditor = ({ staffId, hotelSlug }) => {
  const [allNavItems, setAllNavItems] = useState([]);
  const [assignedIds, setAssignedIds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [staffId, hotelSlug]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // 1. Fetch ALL navigation items for this hotel
      const allItemsResponse = await fetch(
        `/api/staff/navigation-items/?hotel_slug=${hotelSlug}`,
        {
          headers: { 'Authorization': `Token ${token}` }
        }
      );
      const allItems = await allItemsResponse.json();
      setAllNavItems(allItems);
      
      // 2. Fetch THIS staff's current assignments
      const permissionsResponse = await fetch(
        `/api/staff/staff/${staffId}/navigation-permissions/`,
        {
          headers: { 'Authorization': `Token ${token}` }
        }
      );
      const permissions = await permissionsResponse.json();
      setAssignedIds(
        permissions.allowed_navigation_items.map(item => item.id)
      );
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading navigation data:', error);
      setLoading(false);
    }
  };

  const handleToggle = (itemId) => {
    setAssignedIds(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/staff/staff/${staffId}/navigation-permissions/`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            navigation_item_ids: assignedIds
          })
        }
      );

      if (response.ok) {
        alert('Navigation permissions updated!');
        loadData(); // Refresh
      } else {
        alert('Failed to update permissions');
      }
    } catch (error) {
      console.error('Error saving:', error);
      alert('Error saving permissions');
    }
  };

  if (loading) return <div>Loading navigation items...</div>;

  return (
    <div className="navigation-editor">
      <h3>Assign Navigation Items</h3>
      <p>Select which navigation items this staff member can see</p>
      
      <div className="checkbox-grid">
        {allNavItems.map(item => (
          <label key={item.id} className="checkbox-item">
            <input
              type="checkbox"
              checked={assignedIds.includes(item.id)}
              onChange={() => handleToggle(item.id)}
            />
            <div>
              <strong>{item.name}</strong>
              <small>{item.description}</small>
            </div>
          </label>
        ))}
      </div>

      <div className="summary">
        {assignedIds.length} of {allNavItems.length} items selected
      </div>

      <button onClick={handleSave} className="save-btn">
        Save Navigation Permissions
      </button>
    </div>
  );
};

export default NavigationPermissionEditor;
```

---

## ⚠️ Important Notes

1. **MUST include hotel_slug parameter** when fetching navigation items:
   ```
   ✅ /api/staff/navigation-items/?hotel_slug=hotel-killarney
   ❌ /api/staff/navigation-items/  (returns 0 items or wrong items)
   ```

2. **Use staff ID** from the URL or staff object, not user ID

3. **Only super_staff_admin** can access the permissions endpoints

4. **Check allowed_navs** from login response to filter navigation menu

---

## 🧪 Test the Endpoints

### Test 1: Fetch all navigation items
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/staff/navigation-items/?hotel_slug=hotel-killarney"
```
**Expected:** 17 navigation items

### Test 2: Fetch staff permissions
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/staff/staff/123/navigation-permissions/"
```
**Expected:** List of assigned navigation items

### Test 3: Update staff permissions
```bash
curl -X PUT \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"navigation_item_ids": [1, 2, 7]}' \
  "http://localhost:8000/api/staff/staff/123/navigation-permissions/"
```
**Expected:** Success message with updated list

---

## ✅ Summary

| Endpoint | Method | Purpose | Query Params |
|----------|--------|---------|--------------|
| `/api/staff/navigation-items/` | GET | Get all navigation items | `?hotel_slug=hotel-killarney` |
| `/api/staff/{hotel_slug}/{staff_id}/` | GET | Get staff details | None |
| `/api/staff/staff/{staff_id}/navigation-permissions/` | GET | Get staff nav permissions | None |
| `/api/staff/staff/{staff_id}/navigation-permissions/` | PUT | Update staff nav permissions | None |
| `/api/staff/login/` | POST | Login (returns allowed_navs) | None |

**Key Point:** Always include `?hotel_slug=hotel-killarney` when fetching navigation items!
