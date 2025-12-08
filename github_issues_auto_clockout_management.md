# Auto Clock-Out Management System

## ⏰ User Story
As a hotel manager, I want an automated system that prevents staff from working excessive hours by automatically clocking them out after configurable limits, so that we comply with labor regulations and protect staff wellbeing.

## 🤖 Overview  
Implementation of a comprehensive auto clock-out management system integrated with Heroku Scheduler for monitoring staff with excessive working hours (24+ by default) and automatically terminating their sessions with proper notifications and status updates.

## ✅ Acceptance Criteria

### Management Command Implementation
- [x] **Auto Clock-Out Command**: `python manage.py auto_clock_out_excessive`
- [x] **Configurable Hours**: `--max-hours` parameter (default: 24.0 hours)
- [x] **Hotel Targeting**: `--hotel` parameter for specific hotel processing
- [x] **Dry Run Mode**: `--dry-run` flag for testing without actual changes
- [x] **Force Mode**: `--force` flag to bypass warning requirements
- [x] **Comprehensive Logging**: Detailed output of operations performed

### Heroku Scheduler Integration
- [x] **Scheduled Execution**: Runs every 30 minutes via Heroku Scheduler
- [x] **Production Ready**: Safe execution in production environment
- [x] **Error Handling**: Graceful failure handling without system disruption
- [x] **Resource Efficiency**: Minimal resource usage during execution
- [x] **Multi-Hotel Support**: Processes all active hotels automatically

### Staff Duty Status Automation
- [x] **Status Updates**: Automatic `duty_status` field updates to 'off_duty'
- [x] **Legacy Support**: Maintains `is_on_duty` field synchronization
- [x] **Real-time Notifications**: Pusher events for immediate UI updates
- [x] **Attendance Logging**: Proper attendance record maintenance
- [x] **Manager Alerts**: Notifications to management about auto clock-outs

### Long Session Handling
- [x] **Warning System**: Progressive warnings before auto clock-out
- [x] **Hard Limit Enforcement**: Automatic termination after maximum hours
- [x] **Acknowledgment Tracking**: Staff acknowledgment of long session warnings
- [x] **Break Management**: End any active breaks before clock-out
- [x] **Session Duration Tracking**: Accurate time calculation and logging

## 🔧 Technical Implementation

### Files Created/Modified
- `attendance/management/commands/auto_clock_out_excessive.py` - Main command implementation
- `attendance/models.py` - Added `auto_clock_out` and `long_session_ack_mode` fields
- `attendance/utils.py` - Warning and notification functions
- `staff/models.py` - Duty status management integration
- `LONG_SESSION_MANAGEMENT.md` - Complete system documentation

### Command Structure
```python
class Command(BaseCommand):
    help = 'Automatically clock-out staff with excessive hours (24+ by default)'

    def add_arguments(self, parser):
        parser.add_argument('--max-hours', type=float, default=24.0)
        parser.add_argument('--hotel', type=str, help='Hotel slug')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **options):
        # Process hotels and find excessive sessions
        # Auto clock-out eligible staff
        # Send notifications and update status
```

### Core Logic Implementation
```python
def process_hotel(self, hotel, max_hours, dry_run, force):
    """Process excessive sessions for a specific hotel"""
    current_time = now()
    
    # Find open logs with excessive hours
    open_logs = ClockLog.objects.filter(
        hotel=hotel,
        time_out__isnull=True,
        is_approved=True,
        is_rejected=False
    ).select_related('staff')
    
    excessive_logs = []
    for log in open_logs:
        duration_hours = (current_time - log.time_in).total_seconds() / 3600
        if duration_hours >= max_hours:
            # Only auto-clock-out if hard limit warning was sent OR force flag
            if log.hard_limit_warning_sent or force:
                excessive_logs.append((log, duration_hours))
    
    # Process each excessive session
    for log, duration_hours in excessive_logs:
        if not dry_run:
            # Close the session
            log.time_out = current_time
            log.long_session_ack_mode = 'auto_clocked_out'
            log.auto_clock_out = True
            log.save()
            
            # Update staff status
            log.staff.duty_status = 'off_duty'
            log.staff.is_on_duty = False
            log.staff.save()
            
            # Send notifications
            self.send_notifications(log, duration_hours)
```

### Database Schema Extensions
```python
# ClockLog model additions
class ClockLog(models.Model):
    auto_clock_out = models.BooleanField(default=False)
    hard_limit_warning_sent = models.BooleanField(default=False)
    long_session_ack_mode = models.CharField(
        max_length=20,
        choices=[
            ('acknowledged', 'Staff Acknowledged'),
            ('ignored', 'Staff Ignored Warning'), 
            ('auto_clocked_out', 'Auto Clocked Out'),
        ],
        null=True, blank=True
    )
```

## 🔔 Notification & Alert System

### Real-time Notifications
```python
def send_notifications(self, log, duration_hours):
    """Send comprehensive notifications for auto clock-out"""
    staff_name = f"{log.staff.first_name} {log.staff.last_name}"
    
    # Real-time status update via NotificationManager
    trigger_clock_status_update(log.hotel.slug, log.staff, "clock_out")
    
    # Attendance logging for managers
    trigger_attendance_log(
        log.hotel.slug,
        {
            'id': log.id,
            'staff_id': log.staff.id,
            'staff_name': staff_name,
            'department': log.staff.department.name if log.staff.department else None,
            'time': log.time_out,
            'verified_by_face': False,
            'auto_clock_out': True,
            'reason': f'Auto clock-out after {duration_hours:.1f} hours'
        },
        "auto_clock_out"
    )
```

### Progressive Warning System
```python
def send_overtime_warning(hotel, clock_log, duration_hours):
    """Send overtime warning notification"""
    event_data = {
        'type': 'overtime_warning',
        'staff_id': clock_log.staff.id,
        'duration_hours': round(duration_hours, 2),
        'message': f"Long shift alert: You've been working for {duration_hours:.1f} hours."
    }
    
    # Send to staff-specific channel
    pusher_client.trigger(
        f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        'overtime-warning',
        event_data
    )

def send_hard_limit_warning(hotel, clock_log, duration_hours):
    """Send hard limit warning with action choices"""
    event_data = {
        'type': 'hard_limit_warning',
        'message': f"Maximum shift duration reached: {duration_hours:.1f} hours.",
        'actions': [
            {
                'label': 'Continue Working',
                'action': 'stay_clocked_in',
                'endpoint': f'/api/hotels/{hotel.slug}/clock-logs/{clock_log.id}/stay-clocked-in/'
            },
            {
                'label': 'Clock Out Now', 
                'action': 'force_clock_out',
                'endpoint': f'/api/hotels/{hotel.slug}/clock-logs/{clock_log.id}/force-clock-out/'
            }
        ]
    }
    
    pusher_client.trigger(f"attendance-{hotel.slug}-staff-{clock_log.staff.id}", 'hard-limit-warning', event_data)
```

## 📅 Heroku Scheduler Configuration

### Scheduler Setup
```bash
# Production Heroku Scheduler (runs every 30 minutes)
python manage.py auto_clock_out_excessive

# Alternative configurations
python manage.py auto_clock_out_excessive --max-hours=20  # 20-hour limit
python manage.py auto_clock_out_excessive --hotel=killarney  # Specific hotel
```

### Resource Optimization
- **Memory Usage**: Processes hotels sequentially to minimize memory footprint
- **Database Queries**: Optimized with `select_related()` for efficient data fetching  
- **Execution Time**: Typically completes in under 30 seconds for all hotels
- **Error Recovery**: Continues processing other hotels if one fails

## 🔧 Command Usage Examples

### Basic Usage
```bash
# Process all hotels with 24-hour limit
python manage.py auto_clock_out_excessive

# Test mode - see what would happen
python manage.py auto_clock_out_excessive --dry-run

# Force clock-out without requiring prior warnings
python manage.py auto_clock_out_excessive --force

# Custom hour limit
python manage.py auto_clock_out_excessive --max-hours=18
```

### Targeted Execution
```bash
# Process specific hotel only
python manage.py auto_clock_out_excessive --hotel=killarney

# Dry run for specific hotel
python manage.py auto_clock_out_excessive --hotel=grand-hotel --dry-run
```

### Output Examples
```
🤖 Auto Clock-Out System - Max Hours: 24.0
🏨 Processing 3 hotels

Hotel Killarney:
  🔍 Checking 12 open sessions...
  ✅ AUTO CLOCKED OUT: John Doe - 25.3h
  ✅ AUTO CLOCKED OUT: Jane Smith - 26.1h
  Hotel Killarney: 2 excessive, 2 auto-clocked-out

🎯 TOTAL: 2 excessive sessions, 2 auto-clocked-out
```

## 🛡️ Safety Features

### Pre-Execution Validation
- **Warning Requirement**: Only auto-clocks-out staff who received hard limit warnings
- **Force Override**: `--force` flag bypasses warning requirement for emergency use
- **Dry Run Testing**: `--dry-run` shows actions without executing them
- **Hotel Filtering**: Target specific hotels to avoid unintended operations

### Break Management
```python
# End break if currently on break before clocking out
if existing_log.is_on_break:
    existing_log.is_on_break = False
    if existing_log.break_start:
        break_duration = (now() - existing_log.break_start).total_seconds() / 60
        existing_log.total_break_minutes += int(break_duration)
    existing_log.break_end = now()
```

### Data Integrity
- **Audit Trail**: All auto clock-outs are logged with reasons
- **Status Synchronization**: Both `duty_status` and legacy `is_on_duty` updated
- **Attendance Records**: Proper attendance history maintenance
- **Notification Delivery**: Real-time updates to all relevant parties

## 🚀 Key Benefits

1. **✅ Labor Compliance**: Automatic enforcement of working hour regulations
2. **✅ Staff Protection**: Prevents excessive working hours and burnout
3. **✅ Manager Oversight**: Real-time notifications of long sessions
4. **✅ Automated Enforcement**: No manual intervention required
5. **✅ Configurable Limits**: Flexible hour thresholds per hotel needs
6. **✅ Comprehensive Logging**: Full audit trail of all actions
7. **✅ Safe Deployment**: Dry-run and force modes for testing
8. **✅ Multi-Hotel Support**: Scales across entire hotel chain

## 📊 Monitoring & Reporting

### Execution Logging
```python
# Sample execution output
self.stdout.write(f"🤖 Auto Clock-Out System - Max Hours: {max_hours}")
self.stdout.write(f"🏨 Processing {hotels.count()} hotels")

for hotel in hotels:
    results = self.process_hotel(hotel, max_hours, dry_run, force)
    if results['found'] > 0:
        self.stdout.write(
            f"  {hotel.name}: {results['found']} excessive, "
            f"{results['clocked_out']} auto-clocked-out"
        )
```

### Manager Dashboards
- Real-time alerts for auto clock-outs
- Historical reporting of excessive sessions
- Staff working pattern analysis
- Compliance tracking and reporting

## 🔗 Related Systems Integration

### Attendance Alert System
- Works alongside `check_attendance_alerts` command
- Coordinated warning progression system
- Shared notification infrastructure

### Face Recognition Integration
- Supports face-verified attendance records
- Maintains verification flags during auto clock-out
- Integrates with existing face attendance workflows

## 🔗 Related Documentation
- `LONG_SESSION_MANAGEMENT.md` - Complete system documentation
- `attendance/management/commands/check_attendance_alerts.py` - Alert system
- `FRONTEND_ME_ENDPOINT_DUTY_STATUS_GUIDE.md` - Duty status frontend guide

---

**Implementation Status**: ✅ **COMPLETE**
**Priority**: High
**Domain**: Attendance Management
**Type**: Automated System