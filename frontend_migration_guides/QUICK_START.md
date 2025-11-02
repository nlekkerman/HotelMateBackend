# Quick Start: Frontend Navigation System

**TL;DR:** Use `allowed_navs` from login response to filter navigation menu.

---

## 🚀 Quick Implementation (3 Steps)

### 1. Update Login (1 minute)
```javascript
// After successful login, save allowed_navs
const data = await loginAPI(username, password);
localStorage.setItem('allowedNavs', JSON.stringify(data.allowed_navs || []));
```

### 2. Update Navigation Component (2 minutes)
```javascript
const Navigation = () => {
  const allowedNavs = JSON.parse(localStorage.getItem('allowedNavs') || '[]');
  const isAuth = !!localStorage.getItem('token');
  
  // Hide for non-authenticated users
  if (!isAuth || allowedNavs.length === 0) return null;
  
  // Filter navigation items
  const visibleItems = ALL_NAV_ITEMS.filter(item => 
    allowedNavs.includes(item.slug)
  );
  
  return <nav>{visibleItems.map(item => <Link to={item.path}>{item.name}</Link>)}</nav>;
};
```

### 3. Create Permission Manager for Super Admin (5 minutes)
```javascript
// Fetch all navigation items
GET /api/staff/navigation-items/

// Update staff permissions
PUT /api/staff/staff/{staffId}/navigation-permissions/
Body: { "navigation_item_ids": [1, 2, 7, 15] }
```

---

## 📋 Navigation Items Available

All 17 items are in the database for `hotel-killarney`:

```
home, chat, reception, rooms, guests, roster, staff, 
restaurants, bookings, maintenance, hotel_info, 
good_to_know, stock_tracker, games, settings, 
room_service, breakfast
```

---

## 🔑 API Endpoints

| Method | Endpoint | Who | Purpose |
|--------|----------|-----|---------|
| POST | `/api/staff/login/` | Anyone | Returns `allowed_navs` array |
| GET | `/api/staff/navigation-items/` | Authenticated | List all nav items |
| GET | `/api/staff/staff/{id}/navigation-permissions/` | Super Admin | Get staff permissions |
| PUT | `/api/staff/staff/{id}/navigation-permissions/` | Super Admin | Update permissions |

---

## ✅ Checklist

- [ ] Save `allowed_navs` from login response
- [ ] Filter navigation menu by `allowed_navs`
- [ ] Hide navigation for non-authenticated users
- [ ] Build checkbox UI for super admin to assign permissions
- [ ] Test: non-auth user sees NO navigation
- [ ] Test: regular staff sees filtered navigation
- [ ] Test: super admin can assign permissions

---

## 📖 Full Documentation

See `FRONTEND_NAVIGATION_IMPLEMENTATION.md` for:
- Complete code examples
- All API endpoint details
- React component implementations
- Testing procedures
- Security rules

---

**Status:** ✅ Backend Ready | ⏳ Frontend Pending  
**Database:** ✅ 17 navigation items seeded for hotel-killarney
