# Complete List of Existing Navigation Icons

**Date:** November 2, 2025  
**Purpose:** Inventory of all navigation items to be saved and migrated to NavigationItem model

---

## 📋 All Discovered Navigation Icons

### Category 1: Core Navigation (from serializers.py)

| Slug | Name | Source | Description |
|------|------|--------|-------------|
| `home` | Home | role_nav_map, access_level_nav_map | Dashboard/Home page |
| `room_service` | Room Service | role_nav_map (porter) | Room service requests |
| `stock_dashboard` | Stock Dashboard | role_nav_map (chef, manager) | Inventory management |
| `staff` | Staff | role_nav_map, access_level_nav_map | Staff management |
| `roster` | Roster | role_nav_map, access_level_nav_map | Staff scheduling |
| `settings` | Settings | role_nav_map, access_level_nav_map | Application settings |
| `reception` | Reception | role_nav_map (receptionist) | Front desk operations |
| `rooms` | Rooms | role_nav_map (receptionist) | Room management |
| `guests` | Guests | role_nav_map (receptionist) | Guest information |
| `good_to_know` | Good to Know | access_level_nav_map | Important information |

---

### Category 2: Department Panels (from permissions.py)

| Slug | Name | Department | Admin Only |
|------|------|------------|------------|
| `accommodation_panel` | Accommodation Panel | accommodation | No |
| `delivery_panel` | Delivery Panel | delivery | No |
| `food_and_beverage_panel` | Food & Beverage Panel | food_and_beverage | No |
| `front_office_panel` | Front Office Panel | front_office | No |
| `kitchen_panel` | Kitchen Panel | kitchen | No |
| `leisure_panel` | Leisure Panel | leisure | No |
| `maintenance_panel` | Maintenance Panel | maintenance | No |
| `management_panel` | Management Panel | management | **Yes** (staff_admin+) |
| `security_panel` | Security Panel | security | **Yes** (staff_admin+) |

---

### Category 3: App Modules (from workspace structure)

| Slug | Name | Django App | Description |
|------|------|-----------|-------------|
| `attendance` | Attendance | attendance | Attendance tracking and analytics |
| `bookings` | Bookings | bookings | Hotel bookings management |
| `chat` | Chat | chat | Staff messaging and communication |
| `entertainment` | Entertainment | entertainment | Entertainment services |
| `hotel_info` | Hotel Info | hotel_info | Hotel information and settings |
| `notifications` | Notifications | notifications | Notifications center |
| `posts` | Posts | posts | Announcements and posts |
| `stock_tracker` | Stock Tracker | stock_tracker | Stock/inventory management |

---

## 📊 Complete Consolidated List

### All 27 Navigation Items to Save:

```javascript
const ALL_NAVIGATION_ITEMS = [
  // Core Navigation (10 items)
  { slug: 'home', name: 'Home', category: 'core', icon: 'home-icon' },
  { slug: 'room_service', name: 'Room Service', category: 'core', icon: 'room-service-icon' },
  { slug: 'stock_dashboard', name: 'Stock Dashboard', category: 'core', icon: 'stock-icon' },
  { slug: 'staff', name: 'Staff', category: 'core', icon: 'staff-icon' },
  { slug: 'roster', name: 'Roster', category: 'core', icon: 'roster-icon' },
  { slug: 'settings', name: 'Settings', category: 'core', icon: 'settings-icon' },
  { slug: 'reception', name: 'Reception', category: 'core', icon: 'reception-icon' },
  { slug: 'rooms', name: 'Rooms', category: 'core', icon: 'rooms-icon' },
  { slug: 'guests', name: 'Guests', category: 'core', icon: 'guests-icon' },
  { slug: 'good_to_know', name: 'Good to Know', category: 'core', icon: 'info-icon' },

  // Department Panels (9 items)
  { slug: 'accommodation_panel', name: 'Accommodation Panel', category: 'panel', icon: 'accommodation-icon' },
  { slug: 'delivery_panel', name: 'Delivery Panel', category: 'panel', icon: 'delivery-icon' },
  { slug: 'food_and_beverage_panel', name: 'Food & Beverage Panel', category: 'panel', icon: 'food-beverage-icon' },
  { slug: 'front_office_panel', name: 'Front Office Panel', category: 'panel', icon: 'front-office-icon' },
  { slug: 'kitchen_panel', name: 'Kitchen Panel', category: 'panel', icon: 'kitchen-icon' },
  { slug: 'leisure_panel', name: 'Leisure Panel', category: 'panel', icon: 'leisure-icon' },
  { slug: 'maintenance_panel', name: 'Maintenance Panel', category: 'panel', icon: 'maintenance-icon' },
  { slug: 'management_panel', name: 'Management Panel', category: 'panel', icon: 'management-icon' },
  { slug: 'security_panel', name: 'Security Panel', category: 'panel', icon: 'security-icon' },

  // App Modules (8 items)
  { slug: 'attendance', name: 'Attendance', category: 'module', icon: 'attendance-icon' },
  { slug: 'bookings', name: 'Bookings', category: 'module', icon: 'bookings-icon' },
  { slug: 'chat', name: 'Chat', category: 'module', icon: 'chat-icon' },
  { slug: 'entertainment', name: 'Entertainment', category: 'module', icon: 'entertainment-icon' },
  { slug: 'hotel_info', name: 'Hotel Info', category: 'module', icon: 'hotel-info-icon' },
  { slug: 'notifications', name: 'Notifications', category: 'module', icon: 'notifications-icon' },
  { slug: 'posts', name: 'Posts', category: 'module', icon: 'posts-icon' },
  { slug: 'stock_tracker', name: 'Stock Tracker', category: 'module', icon: 'stock-tracker-icon' },
];
```

---

## 🎨 Frontend Icon Classes to Define

Based on the navigation items, you'll need CSS classes or icon components for:

```css
/* Core Navigation Icons */
.home-icon { /* ... */ }
.room-service-icon { /* ... */ }
.stock-icon { /* ... */ }
.staff-icon { /* ... */ }
.roster-icon { /* ... */ }
.settings-icon { /* ... */ }
.reception-icon { /* ... */ }
.rooms-icon { /* ... */ }
.guests-icon { /* ... */ }
.info-icon { /* ... */ }

/* Department Panel Icons */
.accommodation-icon { /* ... */ }
.delivery-icon { /* ... */ }
.food-beverage-icon { /* ... */ }
.front-office-icon { /* ... */ }
.kitchen-icon { /* ... */ }
.leisure-icon { /* ... */ }
.maintenance-icon { /* ... */ }
.management-icon { /* ... */ }
.security-icon { /* ... */ }

/* App Module Icons */
.attendance-icon { /* ... */ }
.bookings-icon { /* ... */ }
.chat-icon { /* ... */ }
.entertainment-icon { /* ... */ }
.hotel-info-icon { /* ... */ }
.notifications-icon { /* ... */ }
.posts-icon { /* ... */ }
.stock-tracker-icon { /* ... */ }
```

---

## 🗄️ Database Seeding Data

For the backend management command `seed_navigation_items.py`:

```python
NAVIGATION_ITEMS_TO_SEED = [
    # Display order 1-10: Core Navigation
    {'name': 'Home', 'slug': 'home', 'icon_class': 'home-icon', 'display_order': 1},
    {'name': 'Staff', 'slug': 'staff', 'icon_class': 'staff-icon', 'display_order': 2},
    {'name': 'Roster', 'slug': 'roster', 'icon_class': 'roster-icon', 'display_order': 3},
    {'name': 'Settings', 'slug': 'settings', 'icon_class': 'settings-icon', 'display_order': 4},
    {'name': 'Reception', 'slug': 'reception', 'icon_class': 'reception-icon', 'display_order': 5},
    {'name': 'Rooms', 'slug': 'rooms', 'icon_class': 'rooms-icon', 'display_order': 6},
    {'name': 'Guests', 'slug': 'guests', 'icon_class': 'guests-icon', 'display_order': 7},
    {'name': 'Room Service', 'slug': 'room_service', 'icon_class': 'room-service-icon', 'display_order': 8},
    {'name': 'Good to Know', 'slug': 'good_to_know', 'icon_class': 'info-icon', 'display_order': 9},
    {'name': 'Stock Dashboard', 'slug': 'stock_dashboard', 'icon_class': 'stock-icon', 'display_order': 10},

    # Display order 11-20: App Modules
    {'name': 'Attendance', 'slug': 'attendance', 'icon_class': 'attendance-icon', 'display_order': 11},
    {'name': 'Bookings', 'slug': 'bookings', 'icon_class': 'bookings-icon', 'display_order': 12},
    {'name': 'Chat', 'slug': 'chat', 'icon_class': 'chat-icon', 'display_order': 13},
    {'name': 'Entertainment', 'slug': 'entertainment', 'icon_class': 'entertainment-icon', 'display_order': 14},
    {'name': 'Hotel Info', 'slug': 'hotel_info', 'icon_class': 'hotel-info-icon', 'display_order': 15},
    {'name': 'Notifications', 'slug': 'notifications', 'icon_class': 'notifications-icon', 'display_order': 16},
    {'name': 'Posts', 'slug': 'posts', 'icon_class': 'posts-icon', 'display_order': 17},
    {'name': 'Stock Tracker', 'slug': 'stock_tracker', 'icon_class': 'stock-tracker-icon', 'display_order': 18},

    # Display order 21-30: Department Panels
    {'name': 'Accommodation Panel', 'slug': 'accommodation_panel', 'icon_class': 'accommodation-icon', 'display_order': 21},
    {'name': 'Delivery Panel', 'slug': 'delivery_panel', 'icon_class': 'delivery-icon', 'display_order': 22},
    {'name': 'Food & Beverage Panel', 'slug': 'food_and_beverage_panel', 'icon_class': 'food-beverage-icon', 'display_order': 23},
    {'name': 'Front Office Panel', 'slug': 'front_office_panel', 'icon_class': 'front-office-icon', 'display_order': 24},
    {'name': 'Kitchen Panel', 'slug': 'kitchen_panel', 'icon_class': 'kitchen-icon', 'display_order': 25},
    {'name': 'Leisure Panel', 'slug': 'leisure_panel', 'icon_class': 'leisure-icon', 'display_order': 26},
    {'name': 'Maintenance Panel', 'slug': 'maintenance_panel', 'icon_class': 'maintenance-icon', 'display_order': 27},
    {'name': 'Management Panel', 'slug': 'management_panel', 'icon_class': 'management-icon', 'display_order': 28},
    {'name': 'Security Panel', 'slug': 'security_panel', 'icon_class': 'security-icon', 'display_order': 29},
]
```

---

## ✅ Verification Checklist

Use this to verify all icons are saved:

- [ ] **Core Navigation (10):** home, room_service, stock_dashboard, staff, roster, settings, reception, rooms, guests, good_to_know
- [ ] **Department Panels (9):** accommodation_panel, delivery_panel, food_and_beverage_panel, front_office_panel, kitchen_panel, leisure_panel, maintenance_panel, management_panel, security_panel
- [ ] **App Modules (8):** attendance, bookings, chat, entertainment, hotel_info, notifications, posts, stock_tracker

**Total:** 27 navigation items

---

## 🎯 Questions to Answer

Before finalizing, please confirm:

1. **Are there any navigation items we missed?**
   - Check your current frontend navigation
   - Any admin-only pages?
   - Any special features?

2. **Do you want to group items differently?**
   - By module/app?
   - By user role?
   - By frequency of use?

3. **Which icons should be default for new staff?**
   - Suggest: `home` for everyone
   - Super admin assigns others

4. **Icon naming convention:**
   - Current: kebab-case (`home-icon`, `staff-icon`)
   - Prefer different format?

---

## 📝 Next Steps

1. **Review this list** - Confirm all icons are captured
2. **Add any missing icons** - Let me know if we missed anything
3. **Ready to implement?** - Say "implement backend" and I'll create:
   - Models with NavigationItem
   - Migration files
   - Seed command with all 27 items
   - Views and serializers
   - URL routes
   - Admin configuration

---

**Document Version:** 1.0  
**Status:** Awaiting Confirmation  
**Date:** November 2, 2025
