# Staff Status Enhancement - Break Tracking

## Backend Changes Made

### 1. Enhanced Staff Model
Added `get_current_status()` method to Staff model:
```python
def get_current_status(self):
    """Returns detailed attendance status including break information"""
    if not self.is_on_duty:
        return {
            'status': 'off_duty',
            'label': 'Off Duty',
            'is_on_break': False
        }
    
    # Check current break status from ClockLog
    if current_log and current_log.is_on_break:
        return {
            'status': 'on_break',
            'label': 'On Break', 
            'is_on_break': True,
            'break_start': current_log.break_start,
            'total_break_minutes': current_log.total_break_minutes
        }
    
    return {
        'status': 'on_duty',
        'label': 'On Duty',
        'is_on_break': False
    }
```

### 2. Updated Staff Serializer
Added `current_status` field to provide detailed status information:
```python
current_status = serializers.SerializerMethodField()

def get_current_status(self, obj):
    return obj.get_current_status()
```

## API Response Enhancement

### Before (Basic Status):
```javascript
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "is_on_duty": true  // Only basic on/off info
}
```

### After (Enhanced Status):
```javascript
{
  "id": 123,
  "first_name": "John", 
  "last_name": "Doe",
  "is_on_duty": true,
  "current_status": {
    "status": "on_break",           // off_duty | on_duty | on_break
    "label": "On Break",            // Human-readable text
    "is_on_break": true,
    "break_start": "2025-11-30T14:00:00Z",
    "total_break_minutes": 15
  }
}
```

## Frontend Implementation Guide

### 1. Live UI Status Updates
```javascript
function updateStaffStatusDisplay(staff) {
  const statusElement = document.getElementById(`staff-${staff.id}-status`);
  const status = staff.current_status;
  
  // Update status indicator
  statusElement.className = `status-indicator ${status.status}`;
  statusElement.textContent = status.label;
  
  // Update status colors and icons
  switch (status.status) {
    case 'off_duty':
      statusElement.innerHTML = '🔴 Off Duty';
      statusElement.className += ' status-off';
      break;
      
    case 'on_duty': 
      statusElement.innerHTML = '🟢 On Duty';
      statusElement.className += ' status-on';
      break;
      
    case 'on_break':
      const breakTime = Math.round((Date.now() - new Date(status.break_start)) / 60000);
      statusElement.innerHTML = `🟡 On Break (${breakTime}min)`;
      statusElement.className += ' status-break';
      break;
  }
}
```

### 2. Dynamic Clock In/Out Button Text
```javascript
function updateClockButton(staff) {
  const clockButton = document.getElementById('clock-action-btn');
  const status = staff.current_status;
  
  switch (status.status) {
    case 'off_duty':
      clockButton.textContent = '🕐 Clock In';
      clockButton.className = 'btn-clock-in';
      clockButton.onclick = () => performClockIn();
      break;
      
    case 'on_duty':
      clockButton.textContent = '⏰ Clock Out'; 
      clockButton.className = 'btn-clock-out';
      clockButton.onclick = () => showClockOutOptions();
      break;
      
    case 'on_break':
      clockButton.textContent = '▶️ Resume Work';
      clockButton.className = 'btn-resume';
      clockButton.onclick = () => resumeFromBreak();
      break;
  }
}
```

### 3. Real-Time Status Polling
```javascript
// Poll for status updates every 30 seconds
setInterval(async () => {
  const response = await fetch('/api/staff/me/');
  const staff = await response.json();
  
  updateStaffStatusDisplay(staff);
  updateClockButton(staff);
  updateNavigationBadges(staff);
}, 30000);

function updateNavigationBadges(staff) {
  const navBadge = document.getElementById('nav-status-badge');
  const status = staff.current_status;
  
  navBadge.textContent = status.label;
  navBadge.className = `badge ${status.status}`;
}
```

### 4. Attendance Dashboard Live Updates
```javascript
function renderAttendanceDashboard(staffList) {
  const dashboard = document.getElementById('attendance-dashboard');
  
  const statusCounts = {
    on_duty: staffList.filter(s => s.current_status.status === 'on_duty').length,
    on_break: staffList.filter(s => s.current_status.status === 'on_break').length,
    off_duty: staffList.filter(s => s.current_status.status === 'off_duty').length
  };
  
  dashboard.innerHTML = `
    <div class="status-summary">
      <div class="status-card on-duty">
        <h3>🟢 On Duty</h3>
        <span class="count">${statusCounts.on_duty}</span>
      </div>
      <div class="status-card on-break">
        <h3>🟡 On Break</h3> 
        <span class="count">${statusCounts.on_break}</span>
      </div>
      <div class="status-card off-duty">
        <h3>🔴 Off Duty</h3>
        <span class="count">${statusCounts.off_duty}</span>
      </div>
    </div>
    
    <div class="staff-list">
      ${staffList.map(staff => `
        <div class="staff-item ${staff.current_status.status}">
          <img src="${staff.profile_image_url}" alt="${staff.first_name}">
          <div class="staff-info">
            <h4>${staff.first_name} ${staff.last_name}</h4>
            <span class="department">${staff.department?.name}</span>
            <span class="status">${staff.current_status.label}</span>
            ${staff.current_status.is_on_break ? 
              `<span class="break-time">Break: ${staff.current_status.total_break_minutes}min total</span>` 
              : ''}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
```

### 5. CSS Status Styling
```css
.status-indicator {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-indicator.off_duty {
  background: #ffebee;
  color: #c62828;
}

.status-indicator.on_duty {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-indicator.on_break {
  background: #fff3e0;
  color: #ef6c00;
}

.btn-clock-in {
  background: #4caf50;
  color: white;
}

.btn-clock-out {
  background: #f44336;
  color: white;
}

.btn-resume {
  background: #ff9800;
  color: white;
}

.staff-item.on_break {
  border-left: 4px solid #ff9800;
}

.break-time {
  font-size: 0.75rem;
  color: #666;
  font-style: italic;
}
```

## Real-Time Pusher Integration (REQUIRED)

### Backend Automatically Sends Pusher Events
Every face recognition action now triggers real-time updates:
- **Clock In** → `clock-status-updated` event with `action: 'clock_in'`
- **Clock Out** → `clock-status-updated` event with `action: 'clock_out'`  
- **Break Start** → `clock-status-updated` event with `action: 'break_start'`
- **Break End** → `clock-status-updated` event with `action: 'break_end'`

### Frontend Pusher Listener (REQUIRED)
```javascript
// Subscribe to hotel channel for real-time updates
const pusher = new Pusher('your-pusher-key');
const channel = pusher.subscribe(`hotel-${hotelSlug}`);

// Listen for all clock status changes
channel.bind('clock-status-updated', (data) => {
  console.log('Real-time status update:', data);
  
  // Data structure:
  // {
  //   "user_id": 123,
  //   "staff_id": 456,
  //   "is_on_duty": true,
  //   "clock_time": "2025-11-30T09:00:00Z",
  //   "first_name": "John",
  //   "last_name": "Doe",
  //   "action": "break_start",  // clock_in, clock_out, break_start, break_end
  //   "department": "Reception",
  //   "department_slug": "reception"
  // }
  
  // Update UI immediately
  handleRealTimeStatusUpdate(data);
});

function handleRealTimeStatusUpdate(data) {
  const { staff_id, action, is_on_duty } = data;
  
  // Update staff status in dashboard
  updateStaffStatusCard(staff_id, action, is_on_duty);
  
  // Update attendance counters
  updateAttendanceCounts();
  
  // Update clock button if it's the current user
  if (isCurrentUser(staff_id)) {
    updateMyClockButton(action, is_on_duty);
  }
  
  // Show notification
  showStatusNotification(data);
}
```

### Real-Time Status Card Updates
```javascript
function updateStaffStatusCard(staffId, action, isOnDuty) {
  const card = document.getElementById(`staff-card-${staffId}`);
  if (!card) return;
  
  const statusElement = card.querySelector('.status-indicator');
  const nameElement = card.querySelector('.staff-name');
  const staffName = nameElement.textContent;
  
  // Update status based on action
  switch (action) {
    case 'clock_in':
      statusElement.className = 'status-indicator on_duty';
      statusElement.textContent = '🟢 On Duty';
      showToast(`${staffName} clocked in`);
      break;
      
    case 'clock_out':
      statusElement.className = 'status-indicator off_duty';
      statusElement.textContent = '🔴 Off Duty';
      showToast(`${staffName} clocked out`);
      break;
      
    case 'break_start':
      statusElement.className = 'status-indicator on_break';
      statusElement.textContent = '🟡 On Break';
      showToast(`${staffName} started break`);
      break;
      
    case 'break_end':
      statusElement.className = 'status-indicator on_duty';
      statusElement.textContent = '🟢 On Duty';
      showToast(`${staffName} resumed work`);
      break;
  }
}
```

### Real-Time Attendance Counters
```javascript
function updateAttendanceCounts() {
  // Count current status indicators on page
  const onDutyCount = document.querySelectorAll('.status-indicator.on_duty').length;
  const onBreakCount = document.querySelectorAll('.status-indicator.on_break').length;
  const offDutyCount = document.querySelectorAll('.status-indicator.off_duty').length;
  
  // Update dashboard counters
  document.getElementById('on-duty-count').textContent = onDutyCount;
  document.getElementById('on-break-count').textContent = onBreakCount;
  document.getElementById('off-duty-count').textContent = offDutyCount;
  
  // Update navigation badge
  document.getElementById('total-on-duty').textContent = onDutyCount + onBreakCount;
}
```

### Real-Time Clock Button Updates
```javascript
function updateMyClockButton(action, isOnDuty) {
  const clockBtn = document.getElementById('my-clock-button');
  if (!clockBtn) return;
  
  switch (action) {
    case 'clock_in':
      clockBtn.textContent = '⏰ Clock Out';
      clockBtn.className = 'btn btn-danger';
      clockBtn.onclick = showClockOutOptions;
      break;
      
    case 'clock_out':
      clockBtn.textContent = '🕐 Clock In';
      clockBtn.className = 'btn btn-success';
      clockBtn.onclick = performClockIn;
      break;
      
    case 'break_start':
      clockBtn.textContent = '▶️ Resume Work';
      clockBtn.className = 'btn btn-warning';
      clockBtn.onclick = resumeFromBreak;
      break;
      
    case 'break_end':
      clockBtn.textContent = '⏰ Clock Out';
      clockBtn.className = 'btn btn-danger';
      clockBtn.onclick = showClockOutOptions;
      break;
  }
}
```

### Notification Toasts
```javascript
function showStatusNotification(data) {
  const { first_name, last_name, action, department } = data;
  const name = `${first_name} ${last_name}`;
  
  const messages = {
    clock_in: `${name} (${department}) clocked in`,
    clock_out: `${name} (${department}) clocked out`,
    break_start: `${name} (${department}) started break`,
    break_end: `${name} (${department}) resumed work`
  };
  
  showToast(messages[action], 'info', 3000);
}

function showToast(message, type = 'info', duration = 3000) {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  // Auto-remove after duration
  setTimeout(() => {
    toast.remove();
  }, duration);
}
```

## Usage Benefits

✅ **INSTANT real-time updates** - No polling needed, immediate UI updates  
✅ **Live break tracking** - See who's on break in real-time  
✅ **Dynamic button text** - Clock buttons update instantly  
✅ **Live notifications** - Toast messages for all status changes  
✅ **Real-time counters** - Attendance numbers update automatically  
✅ **Better UX** - Always shows current status across all devices

This enhancement provides comprehensive break tracking and improves the user experience with dynamic, context-aware interfaces.