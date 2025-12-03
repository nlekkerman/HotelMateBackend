# Attendance Department Status API

## Overview

Get real-time attendance data grouped by department, including currently clocked-in staff and those needing approval.

## Endpoint

**URL:** `GET /api/staff/hotel/{hotel_slug}/attendance/clock-logs/department-status/`

**Example:** `GET /api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/`

## Response Format

```json
{
  "front-office": {
    "currently_clocked_in": [
      {
        "staff_id": 35,
        "staff_name": "John Doe",
        "clock_in_time": "09:15",
        "is_on_break": false,
        "hours_worked": 3.5,
        "is_approved": true
      },
      {
        "staff_id": 42,
        "staff_name": "Jane Smith", 
        "clock_in_time": "10:30",
        "is_on_break": false,
        "hours_worked": 2.0,
        "is_approved": false
      }
    ],
    "unrostered": [
      {
        "staff_id": 42,
        "staff_name": "Jane Smith",
        "clock_in_time": "10:30",
        "is_unrostered": true,
        "needs_approval": true,
        "hours_worked": 2.0,
        "is_on_break": false,
        "is_approved": false
      }
    ]
  },
  "food-and-beverage": {
    "currently_clocked_in": [
      {
        "staff_id": 48,
        "staff_name": "Mike Johnson",
        "clock_in_time": "08:00",
        "is_on_break": true,
        "hours_worked": 4.5,
        "is_approved": true
      }
    ],
    "unrostered": []
  },
  "housekeeping": {
    "currently_clocked_in": [],
    "unrostered": []
  }
}
```

## Data Structure

### Department Object
Each department contains:

#### `currently_clocked_in` Array
- **All staff currently clocked in** for this department
- Includes both scheduled and unscheduled staff
- Shows real-time status (break, hours worked, etc.)

#### `unrostered` Array  
- **Subset of currently_clocked_in** who need approval
- Staff who clocked in without scheduled shifts
- Only contains staff with `is_unrostered: true`

### Staff Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `staff_id` | Integer | Unique staff identifier |
| `staff_name` | String | Full name (First Last) |
| `clock_in_time` | String | Time clocked in (HH:MM format) |
| `is_on_break` | Boolean | Currently on break |
| `hours_worked` | Float | Hours worked so far today |
| `is_approved` | Boolean | Manager approved this log |
| `is_unrostered` | Boolean | *(Unrostered only)* Clocked in without schedule |
| `needs_approval` | Boolean | *(Unrostered only)* Requires manager approval |

## Frontend Usage Examples

### Get All Front Office Staff Currently Clocked In
```javascript
const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/');
const data = await response.json();

const frontOfficeStaff = data['front-office']?.currently_clocked_in || [];
console.log(`${frontOfficeStaff.length} front office staff currently working`);
```

### Get Staff Needing Approval
```javascript
const data = await response.json();

// Get all unrostered staff across all departments
const allUnrostered = Object.values(data)
  .flatMap(dept => dept.unrostered)
  .filter(staff => staff.needs_approval);

// Get just front office unrostered
const frontOfficeUnrostered = data['front-office']?.unrostered || [];
```

### Build Department Dashboard
```javascript
const data = await response.json();

Object.entries(data).forEach(([deptSlug, deptData]) => {
  const activeCount = deptData.currently_clocked_in.length;
  const unrosteredCount = deptData.unrostered.length;
  
  console.log(`${deptSlug}: ${activeCount} active, ${unrosteredCount} need approval`);
});
```

### Real-time Status Indicators
```javascript
const data = await response.json();

// Count staff on break
const onBreakCount = Object.values(data)
  .flatMap(dept => dept.currently_clocked_in)
  .filter(staff => staff.is_on_break).length;

// Find overtime staff (>8 hours)
const overtimeStaff = Object.values(data)
  .flatMap(dept => dept.currently_clocked_in)
  .filter(staff => staff.hours_worked > 8);
```

## Department Filtering

### Get Specific Department Data
```javascript
const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/');
const data = await response.json();

// Front Office only
const frontOffice = data['front-office'] || { currently_clocked_in: [], unrostered: [] };

// Food & Beverage only  
const foodBeverage = data['food-and-beverage'] || { currently_clocked_in: [], unrostered: [] };
```

### Available Department Slugs
- `front-office`
- `food-and-beverage` 
- `housekeeping`
- `maintenance`
- `management`
- `security`
- `unassigned` *(staff without department)*

## Error Handling

### Empty Department
If no staff are clocked in for a department:
```json
{
  "front-office": {
    "currently_clocked_in": [],
    "unrostered": []
  }
}
```

### No Active Staff
If no one is clocked in at the hotel:
```json
{}
```

### Error Response
```json
{
  "detail": "You don't have access to this hotel"
}
```

## Polling for Real-time Updates

### Recommended Polling Interval
```javascript
// Poll every 30 seconds for real-time dashboard
setInterval(async () => {
  try {
    const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/');
    const data = await response.json();
    updateDashboard(data);
  } catch (error) {
    console.error('Failed to fetch attendance status:', error);
  }
}, 30000); // 30 seconds
```

### Efficient Updates
```javascript
let lastUpdateTime = null;

const fetchAttendanceStatus = async () => {
  const params = lastUpdateTime ? `?since=${lastUpdateTime}` : '';
  const response = await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/${params}`);
  
  if (response.ok) {
    const data = await response.json();
    lastUpdateTime = new Date().toISOString();
    return data;
  }
};
```

## Approval Process for Unrostered Clock-ins

### Approve Unrostered Clock-in

**Endpoint:** `POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/approve/`

**Example:** `POST /api/staff/hotel/hotel-killarney/attendance/clock-logs/123/approve/`

#### Request
```javascript
const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/123/approve/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  }
});
```

#### Response (200 OK)
```json
{
  "detail": "Clock log approved.",
  "log": {
    "id": 123,
    "staff_name": "Jane Smith",
    "is_approved": true,
    "is_rejected": false,
    "is_unrostered": true,
    "time_in": "2025-12-03T10:30:00Z"
  }
}
```

### Reject Unrostered Clock-in

**Endpoint:** `POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/reject/`

#### What Happens on Rejection:
1. Sets `is_approved = false` and `is_rejected = true`
2. **Automatically clocks out the staff member**
3. Updates staff duty status to 'off_duty'
4. Sends real-time notification to staff

#### Response (200 OK)
```json
{
  "detail": "Clock log rejected and staff clocked out.",
  "log": {
    "id": 123,
    "is_approved": false,
    "is_rejected": true,
    "time_out": "2025-12-03T12:45:00Z"
  }
}
```

### Bulk Approval Actions

#### Approve Multiple Unrostered Logs
```javascript
const approveMultiple = async (logIds) => {
  const approvals = logIds.map(id => 
    fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${id}/approve/`, {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token }
    })
  );
  
  const results = await Promise.allSettled(approvals);
  
  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;
  
  console.log(`Approved: ${successful}, Failed: ${failed}`);
};
```

### Real-time Notifications

When managers approve/reject, staff receive instant notifications via Pusher:

#### Approval Notification
```javascript
// Staff receives this event
pusher.subscribe(`attendance-hotel-killarney-staff-${staffId}`)
  .bind('clocklog-approved', (data) => {
    showNotification(`✅ ${data.message}`, 'success');
    // data.approved_by = "Manager Name"
  });
```

#### Rejection Notification  
```javascript
// Staff receives this event
pusher.subscribe(`attendance-hotel-killarney-staff-${staffId}`)
  .bind('clocklog-rejected', (data) => {
    showNotification(`❌ ${data.message}`, 'error');
    // Automatically redirect to clock-in page
    window.location.href = '/attendance/clock-in';
  });
```

## Integration Examples

### Manager Approval Dashboard
```jsx
const ApprovalDashboard = () => {
  const [pendingLogs, setPendingLogs] = useState([]);
  
  const handleApprove = async (logId) => {
    try {
      await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${logId}/approve/`, {
        method: 'POST'
      });
      
      // Remove from pending list
      setPendingLogs(logs => logs.filter(log => log.staff_id !== logId));
      showSuccess('Clock-in approved!');
    } catch (error) {
      showError('Failed to approve');
    }
  };
  
  const handleReject = async (logId) => {
    try {
      await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${logId}/reject/`, {
        method: 'POST'
      });
      
      setPendingLogs(logs => logs.filter(log => log.staff_id !== logId));
      showSuccess('Clock-in rejected - staff clocked out');
    } catch (error) {
      showError('Failed to reject');
    }
  };
  
  return (
    <div className="approval-dashboard">
      {pendingLogs.map(log => (
        <div key={log.staff_id} className="approval-item">
          <span>{log.staff_name} - {log.clock_in_time}</span>
          <button onClick={() => handleApprove(log.staff_id)}>
            ✅ Approve
          </button>
          <button onClick={() => handleReject(log.staff_id)}>
            ❌ Reject & Clock Out
          </button>
        </div>
      ))}
    </div>
  );
};
```

### Manager Dashboard Component
```jsx
const AttendanceDashboard = () => {
  const [departmentData, setDepartmentData] = useState({});
  
  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/');
      const data = await response.json();
      setDepartmentData(data);
    };
    
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="attendance-dashboard">
      {Object.entries(departmentData).map(([dept, data]) => (
        <DepartmentCard 
          key={dept}
          department={dept}
          activeStaff={data.currently_clocked_in}
          unrosteredStaff={data.unrostered}
        />
      ))}
    </div>
  );
};
```

### Approval Queue Component  
```jsx
const ApprovalQueue = () => {
  const [pendingApprovals, setPendingApprovals] = useState([]);
  
  useEffect(() => {
    const fetchPending = async () => {
      const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/');
      const data = await response.json();
      
      // Extract all pending approvals
      const pending = Object.entries(data).flatMap(([dept, deptData]) => 
        deptData.unrostered
          .filter(staff => staff.needs_approval)
          .map(staff => ({ ...staff, department: dept }))
      );
      
      setPendingApprovals(pending);
    };
    
    fetchPending();
  }, []);
  
  return (
    <div className="approval-queue">
      <h3>Pending Approvals ({pendingApprovals.length})</h3>
      {pendingApprovals.map(staff => (
        <ApprovalItem key={staff.staff_id} staff={staff} />
      ))}
    </div>
  );
};
```