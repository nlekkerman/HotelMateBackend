# Heroku Scheduler Setup - Auto Clock-Out System

## 🚀 Overview
Automatic clock-out system for staff working excessive hours (12+ hours by default) with real-time Pusher notifications.

## ⚙️ Heroku Scheduler Configuration

### 1. Add Scheduler Add-on
```bash
heroku addons:create scheduler:standard
```

### 2. Configure Auto Clock-Out Job
```bash
heroku addons:open scheduler
```

**Job Configuration:**
- **Command:** `python manage.py auto_clock_out_excessive`
- **Frequency:** Every 30 minutes
- **Dyno Size:** Standard-1X (recommended)

### 3. Alternative Job Configurations

#### Conservative Approach (Hourly)
- **Command:** `python manage.py auto_clock_out_excessive`
- **Frequency:** Every hour at :00

#### Custom Threshold Override
- **Command:** `python manage.py auto_clock_out_excessive --max-hours=16`
- **Frequency:** Every 30 minutes

#### Single Hotel Testing
- **Command:** `python manage.py auto_clock_out_excessive --hotel=hotel-killarney --dry-run`
- **Frequency:** Manual (for testing)

## 📊 Current System Configuration

### Default Behavior
- **Auto Clock-Out Trigger:** 12 hours (AttendanceSettings.hard_limit_hours)
- **Real-time Notifications:** ✅ Pusher integration enabled
- **Staff Status Updates:** ✅ Auto-updates duty_status to 'off_duty'
- **Safety Requirements:** Only clocks out after hard_limit_warning_sent OR --force flag

### Notification Channels
```javascript
// Real-time Pusher events sent:
hotel-{slug}.attendance          // Clock status updates
hotel-{slug}.staff-{id}-notifications  // Personal notifications
```

### Notification Payload Example
```json
{
  "type": "auto_clock_out",
  "staff_id": 123,
  "staff_name": "John Doe",
  "department": "Reception",
  "time": "2025-12-11T18:30:00Z",
  "verified_by_face": false,
  "auto_clock_out": true,
  "reason": "Auto clock-out after 12.5 hours"
}
```

## 🛡️ Safety Features

### Prerequisites for Auto Clock-Out
1. **Hard Limit Warning Sent:** `hard_limit_warning_sent = True` on ClockLog
2. **OR Force Override:** `--force` flag bypasses warning requirement
3. **Approved Logs Only:** `is_approved = True` and `is_rejected = False`

### Progressive Warning System
- **6 hours:** Break reminder notification
- **10 hours:** Overtime warning notification  
- **12 hours:** Hard limit warning + enables auto clock-out
- **12+ hours:** Automatic clock-out (if warning sent)

## 📋 Monitoring Commands

### Test Auto Clock-Out (Dry Run)
```bash
heroku run python manage.py auto_clock_out_excessive --dry-run
```

### Check Specific Hotel
```bash
heroku run python manage.py auto_clock_out_excessive --hotel=hotel-killarney
```

### Force Clock-Out (Emergency)
```bash
heroku run python manage.py auto_clock_out_excessive --force
```

### View Scheduler Jobs
```bash
heroku addons:open scheduler
```

## 🔧 Environment Variables (Optional)

Add these to Heroku for additional configuration:
```bash
heroku config:set AUTO_CLOCK_OUT_ENABLED=true
heroku config:set AUTO_CLOCK_OUT_NOTIFICATION_ENABLED=true
heroku config:set PUSHER_AUTO_CLOCK_OUT_CHANNEL_PREFIX=hotel-
```

## 📱 Frontend Integration

The auto clock-out system sends real-time notifications that the frontend can listen to:

```javascript
// Listen for auto clock-out events
const channel = pusher.subscribe(`hotel-${hotelSlug}.attendance`);

channel.bind('auto_clock_out', function(data) {
  // Handle auto clock-out notification
  console.log(`${data.staff_name} was auto-clocked out after ${data.reason}`);
  
  // Update UI accordingly
  updateStaffStatus(data.staff_id, 'off_duty');
  showNotification(`${data.staff_name} was automatically clocked out`, 'warning');
});
```

## ⚡ Quick Setup Checklist

- [ ] Install Heroku Scheduler add-on
- [ ] Configure 30-minute auto clock-out job
- [ ] Verify AttendanceSettings for each hotel (12h default)
- [ ] Test with dry-run command
- [ ] Confirm Pusher notifications working
- [ ] Monitor scheduler logs for first week

## 🎯 Expected Results

**Every 30 minutes, the system will:**
1. Check all hotels for staff with 12+ hour sessions
2. Auto clock-out eligible staff (warnings sent)
3. Send real-time Pusher notifications
4. Update staff duty status to 'off_duty'
5. Log all actions with detailed output

**Sample Output:**
```
🤖 Auto Clock-Out System - Using hotel-specific AttendanceSettings
🏨 Processing 3 hotels
  Hotel Killarney (12.0h limit): 2 excessive, 2 auto-clocked-out
  Hotel Cork (12.0h limit): 1 excessive, 1 auto-clocked-out  
  Hotel Dublin (12.0h limit): 0 excessive, 0 auto-clocked-out
🎯 TOTAL: 3 excessive sessions, 3 auto-clocked-out
```