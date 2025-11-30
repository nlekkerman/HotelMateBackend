# Kiosk Mode Implementation Guide

## Backend Changes Made

### 1. Added `is_kiosk_mode` field to ClockLog model
```python
is_kiosk_mode = models.BooleanField(
    default=False,
    help_text="True if clocked in via shared kiosk device"
)
```

### 2. Updated Face Recognition Serializer
```python
is_kiosk_mode = serializers.BooleanField(
    required=False,
    default=False,
    help_text="True if this is a shared kiosk device"
)
```

### 3. All Face Recognition Responses Now Include `kiosk_action`
```javascript
{
  "action": "clock_in_success",
  "staff": { "name": "John Doe" },
  "kiosk_action": "refresh_for_next_person" // or "stay_logged_in"
}
```

## Frontend Implementation Required

### 1. Attendance Dashboard - Add Kiosk Toggle Button
```html
<button id="kiosk-toggle-btn" onclick="toggleKioskMode()">
  🖥️ Set Device as Kiosk
</button>
```

### 2. Kiosk Mode Toggle Function
```javascript
function toggleKioskMode() {
  const isCurrentlyKiosk = localStorage.getItem('isKioskMode') === 'true';
  
  if (isCurrentlyKiosk) {
    // Disable kiosk mode
    if (confirm('Disable kiosk mode? This will return to personal device mode.')) {
      localStorage.removeItem('isKioskMode');
      showSuccessModal('Personal Mode Enabled', 'This device is now in personal mode.');
      updateKioskButton(false);
    }
  } else {
    // Enable kiosk mode
    if (confirm('Enable kiosk mode? This will make the device shared for all staff.')) {
      localStorage.setItem('isKioskMode', 'true');
      showSuccessModal('Kiosk Mode Enabled', 'This device is now in kiosk mode for all staff.');
      updateKioskButton(true);
    }
  }
}

function updateKioskButton(isKioskMode) {
  const btn = document.getElementById('kiosk-toggle-btn');
  if (isKioskMode) {
    btn.innerHTML = '📱 Disable Kiosk Mode';
    btn.classList.add('kiosk-active');
  } else {
    btn.innerHTML = '🖥️ Set Device as Kiosk';
    btn.classList.remove('kiosk-active');
  }
}
```

### 3. Face Recognition Request - Send Kiosk Mode
```javascript
async function faceClockIn(faceEncoding) {
  const isKioskMode = localStorage.getItem('isKioskMode') === 'true';
  
  const response = await fetch('/api/staff/hotel/hotel-slug/attendance/face-management/face-clock-in/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      encoding: faceEncoding,
      location_note: 'Front Desk',
      is_kiosk_mode: isKioskMode  // <- SEND THIS
    })
  });
  
  const result = await response.json();
  handleFaceResult(result);
}
```

### 4. Handle Backend Response Based on kiosk_action
```javascript
function handleFaceResult(result) {
  switch (result.kiosk_action) {
    case 'refresh_for_next_person':
      // Kiosk mode: Show success, then refresh for next person
      showKioskSuccess(result);
      setTimeout(() => {
        resetCameraForNextPerson();
      }, 3000);
      break;
      
    case 'stay_logged_in':
      // Personal mode: Stay on personal dashboard
      showPersonalSuccess(result);
      updatePersonalAttendanceStatus(result);
      break;
      
    case 'show_options_then_refresh':
      // Kiosk mode: Show break/clock out options
      showActionButtons(result);
      // After action completed, will refresh for next person
      break;
      
    case 'show_options_stay_logged_in':
      // Personal mode: Show options, stay logged in
      showActionButtons(result);
      // After action completed, stay on personal page
      break;
  }
}

function showKioskSuccess(result) {
  showModal({
    title: '✅ Success',
    message: `${result.staff.name} ${result.action.replace('_', ' ')}!`,
    autoClose: 3000
  });
}

function resetCameraForNextPerson() {
  // Clear previous data
  clearFaceData();
  // Reset camera interface
  showCameraInterface();
  // Show "Ready for next person"
  document.getElementById('instruction').textContent = 'Ready for next person - Look at camera';
}
```

### 5. Navigation Clock In/Out Buttons
```javascript
function initializeClockButtons() {
  const isKioskMode = localStorage.getItem('isKioskMode') === 'true';
  
  if (isKioskMode) {
    // Hide navigation clock buttons in kiosk mode
    document.querySelectorAll('.clock-nav-btn').forEach(btn => {
      btn.style.display = 'none';
    });
    // Show kiosk interface instead
    showKioskInterface();
  } else {
    // Show normal navigation buttons
    document.querySelectorAll('.clock-nav-btn').forEach(btn => {
      btn.style.display = 'block';
    });
  }
}
```

### 6. CSS for Kiosk Button
```css
.kiosk-toggle-btn {
  background: #2196F3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}

.kiosk-toggle-btn.kiosk-active {
  background: #FF9800;
}

.kiosk-interface {
  text-align: center;
  font-size: 1.5rem;
  padding: 2rem;
}
```

## Key Points:
- ✅ Backend saves kiosk mode to database
- ✅ Frontend uses localStorage to remember kiosk setting
- ✅ All face recognition actions return `kiosk_action` instruction
- ✅ Frontend automatically refreshes for next person in kiosk mode
- ✅ Personal mode keeps user logged in and shows personal dashboard