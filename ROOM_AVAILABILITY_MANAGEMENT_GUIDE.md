# Room Availability Management Quick Guide

## 🚀 Quick Start

**Admin Panel**: Go to `/admin/rooms/roomtypeinventory/`
**Purpose**: Control room availability for specific dates
**Current Status**: ✅ Inventory records deleted - using physical room counts

## 📋 Common Room Management Tasks

### 🛠️ Block Rooms for Maintenance

**Scenario**: Maintenance team needs to work on 10 Deluxe rooms from Jan 15-20

**Steps**:
1. Go to `/admin/rooms/roomtypeinventory/`
2. Click **"Add Room Type Inventory"**
3. Fill in for each date:
   ```
   Room Type: Deluxe Double Room
   Date: 2025-01-15
   Total Rooms: 25  (35 physical - 10 blocked)
   Stop Sell: ❌ (unchecked)
   ```
4. Repeat for Jan 16, 17, 18, 19, 20
5. Save all records

### ⛔ Block Entire Room Type

**Scenario**: Close all Standard Rooms for Christmas Day

**Steps**:
1. Add inventory record:
   ```
   Room Type: Standard Room
   Date: 2025-12-25
   Total Rooms: (leave blank)
   Stop Sell: ✅ (checked)
   ```
2. Save - **NO rooms bookable for this date**

### 📈 Increase Availability

**Scenario**: Add extra rooms for Valentine's Day event

**Steps**:
1. Add inventory record:
   ```
   Room Type: Deluxe Double Room
   Date: 2025-02-14
   Total Rooms: 40  (more than 35 physical)
   Stop Sell: ❌ (unchecked)
   ```
2. Save - **40 rooms available** (allows overbooking)

### 🏖️ Seasonal Room Closure

**Scenario**: Close Family Suites during winter (Dec 1 - Mar 1)

**Option A - Individual Dates**:
1. Create inventory record for each date
2. Set `Stop Sell = True` for all dates

**Option B - Reduced Capacity**:
1. Create inventory records with `Total Rooms = 1`
2. Keep minimal availability

### 🎯 Event-Based Availability

**Scenario**: Wedding weekend - limit Standard rooms, keep Suites available

**Steps**:
1. **Standard Rooms** (reduce):
   ```
   Date: 2025-06-15, 2025-06-16
   Total Rooms: 15  (instead of 35)
   Stop Sell: ❌
   ```

2. **Deluxe Suites** (unchanged):
   - Don't create inventory records
   - Uses full physical room count

## 📊 Monitoring & Management

### Check Current Overrides
1. Go to `/admin/rooms/roomtypeinventory/`
2. Use **date hierarchy** to navigate months
3. Filter by:
   - `stop_sell = Yes` (blocked dates)
   - `room_type` (specific room types)

### Quick Edit Multiple Records
1. Select records using checkboxes
2. Edit `total_rooms` and `stop_sell` inline
3. Click away to auto-save changes

### Remove Overrides
**Delete records to restore physical room count**:
1. Select inventory records to remove
2. Actions dropdown → "Delete selected"
3. Confirm deletion
4. System returns to physical room counting

## 🔧 Troubleshooting Scenarios

### Problem: "No rooms available" but hotel is empty
**Fix**: Check for inventory records with `stop_sell = True`
```
1. Filter: stop_sell = Yes
2. Uncheck stop_sell for affected dates
3. Save changes
```

### Problem: Wrong room count showing
**Fix**: Check for inventory overrides
```
1. Look for records with low total_rooms
2. Either increase the number or delete record
3. Refresh availability check
```

### Problem: Can't create bookings for future dates
**Fix**: Check for inventory blocks
```
1. Search by room type name
2. Check future dates for stop_sell = True
3. Remove or modify blocks as needed
```

## 🎨 Advanced Usage Patterns

### Dynamic Pricing Events
```
High Demand Period:
- Reduce total_rooms to create scarcity
- Frontend shows "Only X rooms left"
- Drives urgency for bookings
```

### Maintenance Schedules
```
Rolling Maintenance:
- Week 1: Block rooms 101-110
- Week 2: Block rooms 111-120
- Week 3: Block rooms 121-130
Create separate inventory records for each period
```

### Seasonal Management
```
Off-Season Strategy:
- Reduce availability to 60% of physical rooms
- Close entire floors if needed
- Staff can manage smaller hotel footprint
```

## 📱 Field Reference

| Field | When to Use | Example Value |
|-------|-------------|---------------|
| `total_rooms` | Reduce/increase availability | `25` (limit to 25) |
| `stop_sell = True` | Block all bookings | Christmas Day |
| `stop_sell = False` | Allow limited bookings | Maintenance period |
| Leave `total_rooms` blank | Use physical count | Normal operations |

## ⚡ Quick Commands

### Emergency Block All Rooms
```python
# Run in Django shell
from rooms.models import RoomTypeInventory, RoomType
from datetime import date

# Block all room types for today
for rt in RoomType.objects.filter(is_active=True):
    RoomTypeInventory.objects.create(
        room_type=rt,
        date=date.today(),
        stop_sell=True
    )
```

### Bulk Remove Overrides
```python
# Remove all future inventory records
from datetime import date
RoomTypeInventory.objects.filter(date__gte=date.today()).delete()
```

## 🎯 Best Practices

### ✅ Do This
- **Plan ahead**: Create records before events/maintenance
- **Document reasons**: Use admin comments for why blocks exist
- **Regular cleanup**: Remove old records monthly
- **Test bookings**: Verify changes work as expected

### ❌ Don't Do This
- **Permanent blocks**: Use Room model status instead
- **Forget to remove**: Old records can cause confusion
- **Block without backup**: Always have alternative room types
- **Ignore weekends**: Plan for maintenance during low occupancy

## 📞 Emergency Contacts

**If availability system breaks**:
1. Check inventory records first
2. Verify physical room statuses
3. Test with debug script: `python debug_rooms_quick.py`
4. Contact system admin if issues persist

---

**Last Updated**: December 18, 2025  
**File Location**: `/admin/rooms/roomtypeinventory/`  
**Related Files**: `ROOM_TYPE_INVENTORY_GUIDE.md` (technical details)