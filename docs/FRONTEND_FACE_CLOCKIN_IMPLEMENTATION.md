
Face Clock-In Not Available
Face attendance is not enabled for this hotel. Please use the regular clock-in method.# Frontend Face Clock-In Implementation Guide

## Overview

This guide implements a face recognition clock-in system with the following behavior:

- **Clock-In**: One-step automatic (shows success with staff name and image)
- **Clock-Out**: Two-step confirmation with options (Clock Out or Break)
- **Break Management**: Start break, end break, resume shift
- **Staff Verification**: Display staff image from face registration for confirmation

## Flow Logic

```
┌─────────────────┐
│  Face Detected  │
└─────────┬───────┘
          │
          ▼
     ┌─────────┐
     │Not      │──────► One-Step Clock-In
     │Clocked  │        (Automatic)
     │In?      │
     └─────┬───┘
           │
           ▼ (Clocked In)
      ┌──────────┐
      │Show      │──────► Two-Step Options:
      │Options   │        • Clock Out
      │Menu      │        • Start/End Break
      └──────────┘
```

## Implementation

### 1. Main Face Recognition Handler

```javascript
class FaceClockInSystem {
  constructor(hotelSlug, apiBaseUrl) {
    this.hotelSlug = hotelSlug;
    this.apiBaseUrl = apiBaseUrl;
    this.lastFaceEncoding = null;
  }

  async handleFaceRecognition(faceEncoding) {
    this.lastFaceEncoding = faceEncoding;
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/staff/hotel/${this.hotelSlug}/attendance/face-management/face-clock-in/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({
          encoding: faceEncoding,
          location_note: 'Front Desk Kiosk'
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        this.handleClockResult(result);
      } else {
        this.showError(result.error || 'Face not recognized');
      }
    } catch (error) {
      this.showError('Connection error. Please try again.');
    }
  }

  handleClockResult(result) {
    switch (result.action) {
      case 'clock_in_success':
        this.showClockInSuccess(result);
        break;
      
      case 'clock_out_options':
        this.showClockOutOptions(result);
        break;
      
      case 'unrostered_detected':
        this.showUnrosteredConfirmation(result);
        break;
      
      default:
        this.showError('Unknown response from server');
    }
  }
}
```

### 2. Clock-In Success (One-Step)

```javascript
showClockInSuccess(result) {
  const { staff, shift_info, confidence_score, clock_log } = result;
  
  // Show success message with staff image
  this.displaySuccessModal({
    title: "✅ Clocked In Successfully!",
    staffName: staff.name,
    staffImage: staff.image, // From face registration
    department: staff.department,
    shiftInfo: shift_info ? {
      startTime: shift_info.start_time,
      endTime: shift_info.end_time,
      date: shift_info.date
    } : null,
    confidence: Math.round((1 - confidence_score) * 100),
    clockInTime: new Date(clock_log.time_in).toLocaleTimeString(),
    autoCloseAfter: 3000 // Auto close after 3 seconds
  });

  // Optional: Play success sound
  this.playSuccessSound();
  
  // Update UI state
  this.updateKioskState('clocked_in', staff);
}

displaySuccessModal(data) {
  const modal = document.createElement('div');
  modal.className = 'success-modal';
  modal.innerHTML = `
    <div class="modal-content success">
      <div class="success-header">
        <div class="checkmark">✅</div>
        <h2>${data.title}</h2>
      </div>
      
      <div class="staff-info">
        ${data.staffImage ? `<img src="${data.staffImage}" alt="${data.staffName}" class="staff-photo">` : ''}
        <div class="staff-details">
          <h3>${data.staffName}</h3>
          <p class="department">${data.department}</p>
          <p class="time">Clocked in at ${data.clockInTime}</p>
          ${data.shiftInfo ? `
            <div class="shift-info">
              <p>Shift: ${data.shiftInfo.startTime} - ${data.shiftInfo.endTime}</p>
            </div>
          ` : ''}
        </div>
      </div>
      
      <div class="confidence-score">
        Recognition: ${data.confidence}%
      </div>
    </div>
  `;
  
  document.body.appendChild(modal);
  
  // Auto close
  if (data.autoCloseAfter) {
    setTimeout(() => {
      document.body.removeChild(modal);
    }, data.autoCloseAfter);
  }
}
```

### 3. Clock-Out Options (Two-Step)

```javascript
showClockOutOptions(result) {
  const { staff, session_info, available_actions } = result;
  
  this.displayOptionsModal({
    staffName: staff.name,
    staffImage: staff.image,
    department: staff.department,
    sessionInfo: {
      duration: session_info.duration_hours,
      clockInTime: new Date(session_info.clock_in_time).toLocaleTimeString(),
      isOnBreak: session_info.is_on_break,
      currentBreakMinutes: session_info.current_break_minutes,
      totalBreakMinutes: session_info.total_break_minutes
    },
    actions: available_actions
  });
}

displayOptionsModal(data) {
  const modal = document.createElement('div');
  modal.className = 'options-modal';
  
  const breakStatus = data.sessionInfo.isOnBreak 
    ? `<div class="break-status on-break">
         🕐 On Break (${data.sessionInfo.currentBreakMinutes} min)
       </div>`
    : `<div class="break-status">
         Total Break: ${data.sessionInfo.totalBreakMinutes} min
       </div>`;
  
  modal.innerHTML = `
    <div class="modal-content options">
      <div class="staff-header">
        ${data.staffImage ? `<img src="${data.staffImage}" alt="${data.staffName}" class="staff-photo">` : ''}
        <div class="staff-info">
          <h3>${data.staffName}</h3>
          <p class="department">${data.department}</p>
          <p class="session-time">Working ${data.sessionInfo.duration}h</p>
          ${breakStatus}
        </div>
      </div>
      
      <div class="action-buttons">
        ${data.actions.map(action => `
          <button 
            class="action-btn ${action.primary ? 'primary' : 'secondary'}" 
            onclick="clockSystem.handleAction('${action.action}', '${action.endpoint}')">
            <span class="btn-label">${action.label}</span>
            <span class="btn-desc">${action.description}</span>
          </button>
        `).join('')}
      </div>
      
      <button class="cancel-btn" onclick="clockSystem.closeModal()">
        Cancel
      </button>
    </div>
  `;
  
  document.body.appendChild(modal);
  this.currentModal = modal;
}
```

### 4. Action Handlers

```javascript
async handleAction(actionType, endpoint) {
  this.closeModal();
  
  try {
    let response;
    
    switch (actionType) {
      case 'clock_out':
        response = await this.confirmClockOut();
        break;
      
      case 'start_break':
      case 'end_break':
        response = await this.toggleBreak();
        break;
      
      default:
        this.showError('Unknown action');
        return;
    }
    
    if (response.ok) {
      const result = await response.json();
      this.handleActionResult(result);
    } else {
      this.showError('Action failed');
    }
  } catch (error) {
    this.showError('Connection error');
  }
}

async confirmClockOut() {
  return fetch(`${this.apiBaseUrl}/api/staff/hotel/${this.hotelSlug}/attendance/face-management/confirm-clock-out/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getAuthToken()}`
    },
    body: JSON.stringify({
      encoding: this.lastFaceEncoding
    })
  });
}

async toggleBreak() {
  return fetch(`${this.apiBaseUrl}/api/staff/hotel/${this.hotelSlug}/attendance/face-management/toggle-break/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getAuthToken()}`
    },
    body: JSON.stringify({
      encoding: this.lastFaceEncoding
    })
  });
}

handleActionResult(result) {
  switch (result.action) {
    case 'clock_out_success':
      this.showClockOutSuccess(result);
      break;
    
    case 'break_started':
      this.showBreakStarted(result);
      break;
    
    case 'break_ended':
      this.showBreakEnded(result);
      break;
    
    default:
      this.showError('Unknown result');
  }
}
```

### 5. Break Management

```javascript
showBreakStarted(result) {
  const { staff, break_info } = result;
  
  this.displayInfoModal({
    title: "🕐 Break Started",
    staffName: staff.name,
    staffImage: staff.image,
    message: "Enjoy your break!",
    info: `Break started at ${new Date(break_info.break_start_time).toLocaleTimeString()}`,
    autoCloseAfter: 2000
  });
  
  this.updateKioskState('on_break', staff);
}

showBreakEnded(result) {
  const { staff, break_info } = result;
  
  this.displayInfoModal({
    title: "✅ Break Ended",
    staffName: staff.name,
    staffImage: staff.image,
    message: "Welcome back to work!",
    info: `Break duration: ${break_info.break_duration_minutes} minutes`,
    autoCloseAfter: 2000
  });
  
  this.updateKioskState('clocked_in', staff);
}

showClockOutSuccess(result) {
  const { staff, session_summary } = result;
  
  this.displaySuccessModal({
    title: "👋 Clocked Out Successfully!",
    staffName: staff.name,
    staffImage: staff.image,
    department: staff.department,
    message: "Have a great day!",
    sessionSummary: {
      duration: session_summary.duration_hours,
      totalBreak: session_summary.total_break_minutes,
      clockOutTime: new Date(session_summary.clock_out_time).toLocaleTimeString()
    },
    autoCloseAfter: 3000
  });
  
  this.updateKioskState('clocked_out', staff);
}
```

### 6. UI State Management

```javascript
updateKioskState(state, staff) {
  const statusDisplay = document.getElementById('kiosk-status');
  
  switch (state) {
    case 'clocked_in':
      statusDisplay.innerHTML = `
        <div class="status-active">
          <div class="status-indicator active"></div>
          <p>${staff.name} is working</p>
        </div>
      `;
      break;
    
    case 'on_break':
      statusDisplay.innerHTML = `
        <div class="status-break">
          <div class="status-indicator break"></div>
          <p>${staff.name} is on break</p>
        </div>
      `;
      break;
    
    case 'clocked_out':
      statusDisplay.innerHTML = `
        <div class="status-idle">
          <div class="status-indicator idle"></div>
          <p>Ready for next staff member</p>
        </div>
      `;
      break;
  }
}

closeModal() {
  if (this.currentModal) {
    document.body.removeChild(this.currentModal);
    this.currentModal = null;
  }
}

showError(message) {
  const errorModal = document.createElement('div');
  errorModal.className = 'error-modal';
  errorModal.innerHTML = `
    <div class="modal-content error">
      <div class="error-icon">❌</div>
      <h3>Error</h3>
      <p>${message}</p>
      <button onclick="this.parentElement.parentElement.remove()">Try Again</button>
    </div>
  `;
  document.body.appendChild(errorModal);
  
  setTimeout(() => {
    if (document.body.contains(errorModal)) {
      document.body.removeChild(errorModal);
    }
  }, 3000);
}

getAuthToken() {
  // Implement your token retrieval logic
  return localStorage.getItem('auth_token');
}

playSuccessSound() {
  // Optional: Play success sound
  const audio = new Audio('/sounds/success-beep.mp3');
  audio.play().catch(() => {
    // Ignore audio errors
  });
}
```

### 7. CSS Styling

```css
/* Add to your CSS file */
.success-modal, .options-modal, .error-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.staff-photo {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #4CAF50;
}

.success-header {
  margin-bottom: 1rem;
}

.checkmark {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.staff-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1rem 0;
}

.action-btn {
  display: block;
  width: 100%;
  padding: 1rem;
  margin: 0.5rem 0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
}

.action-btn.primary {
  background: #f44336;
  color: white;
}

.action-btn.secondary {
  background: #2196F3;
  color: white;
}

.btn-label {
  display: block;
  font-weight: bold;
  font-size: 1.1rem;
}

.btn-desc {
  display: block;
  font-size: 0.9rem;
  opacity: 0.8;
}

.break-status.on-break {
  color: #FF9800;
  font-weight: bold;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}

.status-indicator.active {
  background: #4CAF50;
}

.status-indicator.break {
  background: #FF9800;
}

.status-indicator.idle {
  background: #999;
}
```

### 8. Usage Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Face Clock-In Kiosk</title>
    <link rel="stylesheet" href="kiosk-styles.css">
</head>
<body>
    <div id="kiosk-container">
        <div id="camera-view">
            <!-- Camera feed goes here -->
        </div>
        
        <div id="kiosk-status">
            <div class="status-idle">
                <div class="status-indicator idle"></div>
                <p>Ready for next staff member</p>
            </div>
        </div>
        
        <button id="capture-btn" onclick="captureFace()">
            Scan Face to Clock In/Out
        </button>
    </div>

    <script>
        // Initialize the face clock-in system
        const clockSystem = new FaceClockInSystem('your-hotel-slug', 'https://your-api-url');
        
        async function captureFace() {
            try {
                // Your face detection logic here
                const faceEncoding = await detectFaceFromCamera();
                
                if (faceEncoding && faceEncoding.length === 128) {
                    await clockSystem.handleFaceRecognition(faceEncoding);
                } else {
                    clockSystem.showError('No face detected. Please look at the camera.');
                }
            } catch (error) {
                clockSystem.showError('Camera error. Please try again.');
            }
        }
        
        // Your face detection implementation
        async function detectFaceFromCamera() {
            // Implement face detection and return 128-dimensional encoding
            // This is where you integrate with face-api.js or similar library
            return [/* 128 float values */];
        }
    </script>
</body>
</html>
```

## Summary

This implementation provides:

✅ **One-step clock-in** with success message showing staff name and image  
✅ **Two-step clock-out** with options (Clock Out or Break)  
✅ **Break management** (start/end break, resume shift)  
✅ **Staff verification** with images from face registration  
✅ **Clear UI feedback** for all actions  
✅ **Error handling** for failed recognitions  

The system automatically handles all the flow logic you requested and provides a smooth user experience for hotel staff.