# Attendance Dashboard API - Latest Updates

## 🆕 New Endpoint: Staff Attendance Summary

### Endpoint
```
GET /api/staff/{hotel_slug}/attendance-summary/
```

### Query Parameters
- `from` (required): Start date (YYYY-MM-DD)
- `to` (optional): End date (defaults to `from`)
- `department` (optional): Filter by department slug
- `status` (optional): Filter by attendance status (`active`, `completed`, `no_log`, `issue`)

### Response Format
```json
{
  "results": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "department_name": "Housekeeping",
      "department_slug": "housekeeping",
      "duty_status": "on_duty",
      "avatar_url": "https://res.cloudinary.com/...",
      
      // Attendance Metrics
      "planned_shifts": 5,
      "worked_shifts": 4,
      "total_worked_minutes": 1920,
      "issues_count": 1,
      "attendance_status": "active",
      
      // UI Badge Information
      "duty_status_badge": {
        "label": "On Duty",
        "color": "success",
        "bg_color": "#28a745",
        "status_type": "active"
      },
      "attendance_status_badge": {
        "label": "Currently Active",
        "color": "success",
        "priority": 1
      }
    }
  ],
  "count": 25,
  "date_range": {
    "from": "2025-12-03",
    "to": "2025-12-03"
  },
  "filters": {
    "hotel": "hotel-killarney",
    "department": "housekeeping",
    "status": "active"
  }
}
```

## 📊 Attendance Status Types

| Status | Description | UI Priority |
|--------|-------------|-------------|
| `active` | Currently clocked in and on duty | 1 (highest) |
| `completed` | Has completed shifts, no issues | 2 |
| `issue` | Has attendance problems (missing clock-out, excessive hours, etc.) | 3 |
| `no_log` | Planned shifts but no attendance records | 4 (lowest) |

## 🔧 Department Filter Fix

### Fixed Issue
- **Before**: Department dropdown showed only 2 departments
- **After**: Shows all departments used by hotel staff (~12 departments)

### Affected Endpoint
```
GET /api/staff/{hotel_slug}/metadata/
```

Now returns hotel-scoped departments instead of global list.

## 💡 Usage Examples

### Get Today's Attendance Dashboard
```javascript
fetch('/api/staff/hotel-killarney/attendance-summary/?from=2025-12-03')
```

### Filter by Department
```javascript
fetch('/api/staff/hotel-killarney/attendance-summary/?from=2025-12-03&department=housekeeping')
```

### Weekly Summary with Issues
```javascript
fetch('/api/staff/hotel-killarney/attendance-summary/?from=2025-11-25&to=2025-12-01&status=issue')
```

## 🎨 Badge Styling Reference

### Duty Status Colors
- **On Duty**: `#28a745` (success green)
- **Off Duty**: `#6c757d` (secondary gray)
- **On Break**: `#ffc107` (warning yellow)

### Attendance Status Colors
- **Active**: `#28a745` (success green)
- **Completed**: `#007bff` (primary blue)
- **Issue**: `#dc3545` (danger red)
- **No Log**: `#f8f9fa` (light gray)

## 🔄 Backward Compatibility

All existing endpoints remain unchanged. This is a new addition to the Staff API that enhances dashboard functionality without breaking existing features.