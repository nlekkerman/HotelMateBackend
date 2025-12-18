# Room Type Inventory Management Guide

## Overview
The **Room Type Inventory** system allows you to control room availability for specific dates by overriding the default physical room count or stopping sales completely.

## When to Use Room Type Inventory

### ✅ Use Cases
- **Maintenance Periods**: Block rooms during renovations
- **Special Events**: Limit availability during high-demand periods  
- **Overbooking Protection**: Reduce available rooms to prevent overbooking
- **Seasonal Adjustments**: Temporarily close room types during off-season
- **Holiday Management**: Block sales during Christmas, New Year's, etc.
- **Staff Events**: Reserve rooms for staff training or company events

### ❌ Don't Use For
- Regular booking management (use actual bookings instead)
- Permanent room closures (update physical Room records instead)

## How It Works

### Default Behavior (No Inventory Records)
- System counts **physical Room records** with status `AVAILABLE` or `READY_FOR_GUEST`
- Example: 35 physical rooms = 35 available for booking

### With Inventory Override
- System uses `total_rooms` value from `RoomTypeInventory` record instead
- Example: Physical rooms = 35, Inventory override = 8 → Only 8 available

## Where to Manage Inventory

### 📊 Django Admin Panel
**Location**: `/admin/rooms/roomtypeinventory/`

**Access**: Staff users with admin permissions

**Features**:
- List view with date hierarchy navigation
- Quick edit `total_rooms` and `stop_sell` inline
- Filter by hotel, room type, and stop_sell status
- Search by room type name
- Date-based organization

**Quick Actions**:
- **Edit inline**: Click on `total_rooms` or `stop_sell` fields to edit directly
- **Bulk operations**: Select multiple records and apply actions
- **Date navigation**: Use date hierarchy to jump to specific months/years

### 🏨 Staff Dashboard (Future)
**Location**: Staff panel → Rooms → Inventory Management

**Planned Features**:
- Calendar view for easy date selection
- Bulk date range operations
- Quick templates for holidays/events
- Visual availability charts

## Managing Inventory Records

### Creating New Records

#### Via Django Admin
1. Go to `/admin/rooms/roomtypeinventory/`
2. Click **"Add Room Type Inventory"**
3. Fill in:
   - **Room Type**: Select from dropdown
   - **Date**: Choose specific date
   - **Total Rooms**: Override count (leave blank to use physical rooms)
   - **Stop Sell**: Check to completely block bookings
4. Click **"Save"**

#### Via Management Command
```bash
# Create inventory for next 90 days (used during setup)
python manage.py populate_killarney_pms
```

### Field Explanations

| Field | Description | Example |
|-------|-------------|---------|
| `room_type` | Which room type this affects | "Deluxe Double Room" |
| `date` | Specific date for override | 2025-12-25 |
| `total_rooms` | Room count override | 8 (overrides 35 physical) |
| `stop_sell` | Complete sales block | ✅ = No bookings allowed |

### Common Operations

#### ⛔ Block Room Type for Holiday
```
room_type: Standard Room
date: 2025-12-25
total_rooms: (leave blank)
stop_sell: ✅ (checked)
```

#### 🔒 Limit Rooms During Maintenance  
```
room_type: Deluxe Suite
date: 2025-01-15
total_rooms: 2
stop_sell: ❌ (unchecked)
```

#### 📈 Increase Availability for Event
```
room_type: Standard Room  
date: 2025-02-14
total_rooms: 40
stop_sell: ❌ (unchecked)
```

## Troubleshooting

### Problem: "No availability" despite empty hotel
**Cause**: Inventory records limiting room count

**Solution**: 
1. Check `/admin/rooms/roomtypeinventory/`
2. Look for records with low `total_rooms` values
3. Either increase `total_rooms` or delete the records

### Problem: Can't book despite rooms showing available
**Cause**: `stop_sell = True` for the dates

**Solution**:
1. Filter inventory by `stop_sell = Yes`
2. Uncheck `stop_sell` for affected dates
3. Save changes

### Problem: Wrong room count showing
**Cause**: Inventory override doesn't match physical rooms

**Solution**:
1. Count physical rooms: `Room.objects.filter(room_type=X, room_status__in=['AVAILABLE', 'READY_FOR_GUEST']).count()`
2. Update inventory `total_rooms` to match
3. Or delete inventory record to use physical count

## Best Practices

### 📅 Date Management
- **Plan ahead**: Create inventory records for known events/maintenance
- **Regular cleanup**: Remove old inventory records to improve performance
- **Date ranges**: Create records for consecutive dates when needed

### 🔄 Maintenance Workflow
1. **Before maintenance**: Set `total_rooms = 0` or `stop_sell = True`
2. **During maintenance**: Monitor bookings aren't affected
3. **After maintenance**: Remove inventory records or restore counts

### 📊 Monitoring
- **Weekly review**: Check inventory overrides are still needed
- **Seasonal updates**: Adjust for peak/off-peak periods  
- **Event coordination**: Align with hotel event calendar

## Integration Points

### ⚙️ Availability Service
File: `hotel/services/availability.py`
- Function `_inventory_for_date()` checks for RoomTypeInventory records
- If found: uses `total_rooms` value
- If not found: counts physical Room records
- If `stop_sell = True`: returns 0 availability

### 🌐 Public API
Endpoints affected:
- `/api/public/hotel/{slug}/availability/`
- Booking creation APIs
- Room type availability checks

### 📱 Frontend Display
- Room selection pages show adjusted availability
- "No availability" messages when `stop_sell = True`
- Booking flow blocked when inventory = 0

## Quick Reference

### Fast Fix Commands
```bash
# Delete ALL inventory overrides (use physical room counts)
python -c "from rooms.models import RoomTypeInventory; RoomTypeInventory.objects.all().delete()"

# Update today's inventory to match physical rooms
python fix_inventory_limits.py

# Check current inventory issues
python debug_rooms_quick.py
```

### Admin URLs
- **Inventory List**: `/admin/rooms/roomtypeinventory/`
- **Add New**: `/admin/rooms/roomtypeinventory/add/`
- **Room Types**: `/admin/rooms/roomtype/`
- **Physical Rooms**: `/admin/rooms/room/`

### Related Models
- `rooms.Room` - Physical room records
- `rooms.RoomType` - Room categories  
- `hotel.RoomBooking` - Actual bookings
- `rooms.RatePlan` - Pricing plans