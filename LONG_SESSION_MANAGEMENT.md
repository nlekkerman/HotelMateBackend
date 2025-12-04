# Long Session Management & Notifications

## Overview
When staff forget to clock out and work extended hours, the system automatically triggers progressive warnings and notifications to ensure compliance and staff wellbeing.

## Warning Thresholds (AttendanceSettings)

### Default Settings per Hotel:
- **Break Warning**: 6.0 hours - Suggests taking a break
- **Overtime Warning**: 10.0 hours - Long shift alert 
- **Hard Limit**: 12.0 hours - **REQUIRES MANDATORY ACTION**

## Progressive Warning System

### 1. Break Warning (6+ hours)
**Trigger**: Staff works 6+ hours continuously
**Notification**: Gentle reminder to take a break
**Action**: Optional - staff can continue or take break

### 2. Overtime Warning (10+ hours) 
**Trigger**: Staff works 10+ hours
**Notification**: Long shift alert for wellbeing monitoring
**Action**: Advisory only - managers notified for oversight

### 3. Hard Limit Warning (12+ hours)
**Trigger**: Staff works 12+ hours 
**Notification**: **MANDATORY ACTION REQUIRED**
**Actions**: Staff MUST choose one:
- **"Continue Working"** - acknowledges extended session
- **"Clock Out Now"** - forces immediate clock out

## API Endpoints

### Stay Clocked In (Acknowledge Long Session)
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/stay-clocked-in/
```

### Force Clock Out
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/force-clock-out/
```

## Pusher Real-time Notifications

### 1. Break Warning Notification
**Channel**: `attendance-{hotel_slug}-staff-{staff_id}`
**Event**: `break-reminder`
**Data**:
```json
{
  "type": "break_reminder",
  "clock_log_id": 456,
  "staff_id": 123,
  "staff_name": "John Doe",
  "duration_hours": 6.2,
  "message": "You've been working for 6.2 hours. Consider taking a break.",
  "timestamp": "2025-12-04T14:30:00Z"
}
```

### 2. Overtime Warning Notification
**Channel**: `attendance-{hotel_slug}-staff-{staff_id}`
**Event**: `overtime-warning`
**Data**:
```json
{
  "type": "overtime_warning",
  "clock_log_id": 456,
  "staff_id": 123,
  "staff_name": "John Doe", 
  "duration_hours": 10.5,
  "message": "Long shift alert: You've been working for 10.5 hours. Monitor your wellbeing.",
  "timestamp": "2025-12-04T18:30:00Z"
}
```

### 3. Hard Limit Warning (CRITICAL)
**Channel**: `attendance-{hotel_slug}-staff-{staff_id}`
**Event**: `hard-limit-warning`
**Data**:
```json
{
  "type": "hard_limit_warning",
  "clock_log_id": 456,
  "staff_id": 123,
  "staff_name": "John Doe",
  "duration_hours": 12.1,
  "message": "Maximum shift duration reached: 12.1 hours. Please choose to continue or clock out.",
  "requires_action": true,
  "actions": [
    {
      "label": "Continue Working",
      "action": "stay_clocked_in",
      "endpoint": "/api/staff/hotel/{hotel_slug}/attendance/clock-logs/456/stay-clocked-in/"
    },
    {
      "label": "Clock Out Now", 
      "action": "force_clock_out",
      "endpoint": "/api/staff/hotel/{hotel_slug}/attendance/clock-logs/456/force-clock-out/"
    }
  ],
  "timestamp": "2025-12-04T22:30:00Z"
}
```

### 4. Manager Oversight Notifications
**Channel**: `attendance-{hotel_slug}-managers`
**Event**: `long-session-alert`
**Data**:
```json
{
  "type": "long_session_alert",
  "clock_log_id": 456,
  "staff_id": 123,
  "staff_name": "John Doe",
  "department": "Housekeeping",
  "duration_hours": 12.1,
  "warning_level": "hard_limit", 
  "message": "John Doe has been working for 12.1 hours and requires immediate attention.",
  "timestamp": "2025-12-04T22:30:00Z"
}
```

## Frontend Implementation

### Badge Updates
Listen for Pusher events to update staff duty badges:

```javascript
// Subscribe to attendance channel
const channel = pusher.subscribe(`attendance-${hotelSlug}-staff-${staffId}`);

// Break reminder
channel.bind('break-reminder', (data) => {
  showBreakSuggestion(data);
  updateStaffBadge(data.staff_id, 'needs-break');
});

// Overtime warning  
channel.bind('overtime-warning', (data) => {
  showOvertimeAlert(data);
  updateStaffBadge(data.staff_id, 'overtime');
});

// Hard limit warning (CRITICAL)
channel.bind('hard-limit-warning', (data) => {
  showCriticalModal(data);
  updateStaffBadge(data.staff_id, 'critical');
  blockFurtherActions(); // Prevent other actions until resolved
});
```

### Staff Badge States
- **Normal**: Green badge, normal duration display
- **Needs Break**: Yellow badge, "6.2h - Break suggested"
- **Overtime**: Orange badge, "10.5h - Long shift" 
- **Critical**: Red badge, "12.1h - ACTION REQUIRED"

### Message Display
```javascript
function showCriticalModal(data) {
  const modal = createModal({
    title: "⚠️ Maximum Shift Duration Reached",
    message: data.message,
    type: "critical",
    actions: data.actions,
    canClose: false, // Must choose an action
    autoClose: false
  });
  
  modal.show();
}
```

## Database Tracking

### ClockLog Fields
- `break_warning_sent`: Boolean - Break reminder sent
- `overtime_warning_sent`: Boolean - Overtime alert sent  
- `hard_limit_warning_sent`: Boolean - Hard limit warning sent
- `long_session_ack_mode`: CharField - Staff choice ('stay' or 'clocked_out')

## Compliance & Audit
- All extended sessions are logged with timestamps
- Staff acknowledgments are recorded for audit trails
- Manager oversight notifications ensure compliance monitoring
- Progressive escalation prevents "forgotten" clock-outs

## Real-world Scenario
**15+ Hour Session**:
1. **6h**: Break reminder sent → Badge turns yellow
2. **10h**: Overtime warning → Badge turns orange, managers notified
3. **12h**: **CRITICAL ACTION REQUIRED** → Badge turns red, modal blocks UI
4. **Staff chooses**: Continue working OR Clock out immediately
5. **15h**: If continued, they acknowledged the extended session at 12h mark