
# HotelMate Routing Refactor – Phase 1 (Concept Only, No Code)

This file describes **exactly what needs to be done** for Phase 1 routing refactor,
**without showing any code**, so backend can implement it cleanly.

---

## 🎯 Goal

Introduce a new, clean structure for all API URLs:

### STAFF zone  
For internal tools (rooms, stock, bookings, etc.)
```
/api/staff/hotels/<hotel_slug>/...
```

### GUEST zone  
For hotel public pages (rooms, offers, events, menus, etc.)
```
/api/guest/hotels/<hotel_slug>/...
```

### LEGACY zone  
All existing endpoints stay alive:
```
/api/<app>/
```

This guarantees:
- nothing breaks,
- front-end keeps working,
- QR codes keep working,
- new features get a clean structure.

---

## ✅ What Phase 1 Actually Does

### 1. Add a new **STAFF** route group
All current Django apps (rooms, bookings, stock_tracker, etc.)
must also be reachable via:

```
/api/staff/hotels/<hotel_slug>/<app_name>/
```

No logic changes inside apps.
No serializer changes.
No model changes.

Just wrap them in a new prefix.

---

### 2. Add a new **GUEST** route group
Create a guest-facing API section with endpoints like:

```
/api/guest/hotels/<hotel_slug>/site/home/
/api/guest/hotels/<hotel_slug>/site/rooms/
/api/guest/hotels/<hotel_slug>/site/offers/
```

In Phase 1 these endpoints can return **stub JSON**.
Later they will be wired to real hotel data.

---

### 3. Keep **all old** `/api/<app>/` URLs
These do NOT change in Phase 1.

Why?
- Existing front-end uses them.
- Existing QR flows expect them.
- Existing staff features rely on them.

They will be gradually phased out later.

---

## 📌 Summary for Backend Team

Phase 1 tasks:

- Add new STAFF route namespace.
- Add new GUEST route namespace.
- Keep all current `/api/<app>/` endpoints untouched.
- Do NOT rewrite existing app URLs.
- Do NOT modify view logic.

Result after Phase 1:

```
/api/staff/hotels/<slug>/rooms/
/api/staff/hotels/<slug>/bookings/
/api/staff/hotels/<slug>/stock_tracker/
/api/staff/hotels/<slug>/attendance/

+ new guest:
/api/guest/hotels/<slug>/site/home/
/api/guest/hotels/<slug>/site/rooms/

/api/<app>/           (legacy but still active)
```

Nothing breaks.  
Structure becomes clean.  
Next phases can build on top.

---

## 💬 Notes for Future Phases (not part of Phase 1)

- Add hotel-slug-based filtering inside viewsets  
- Add guest portal serializers  
- Add permissions for staff zone  
- Add QR redirects  
- Remove legacy routes once migration is complete  

---

This document is the **official Phase 1 routing refactor spec**.
