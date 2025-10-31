# Staff, Department, and Role Endpoints

## Staff Creation Permissions

**Who can create staff?**

- Any authenticated user who is a staff member of the hotel (matched by `hotel_slug` in the URL) can create new staff for that hotel.
- The user's role or access level does **not** matter; as long as the user is a staff member of the hotel, they can create staff.

If a user is not authenticated, or is not a staff member of the hotel, a 401 or 403 error is returned.

---

## Frontend Integration Guide

### Creating Staff (React Example)

```js
// Assume you have a valid JWT token in localStorage and hotelSlug from context/route
const token = localStorage.getItem('token');
const hotelSlug = 'your-hotel-slug';
const url = `/api/hotels/${hotelSlug}/staff/`;

async function createStaff(staffData) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(staffData),
  });
  if (res.status === 401) {
    throw new Error('Authentication required. Please log in.');
  }
  if (res.status === 403) {
    throw new Error('You must be a staff member of this hotel to create staff.');
  }
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Unknown error');
  }
  return await res.json();
}
```

### Defensive Error Handling

- Always check for 401/403 errors and prompt the user to log in or contact an admin if they lack hotel membership.
- Do **not** rely on role or access level for frontend permission logic; backend enforces hotel membership only.

---
