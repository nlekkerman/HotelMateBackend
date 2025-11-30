# Face Clock-In Frontend Implementation Examples

## Summary: Current System Capabilities

Your HotelMate attendance system **does NOT have break clock-in/clock-out functionality**. It only has:

1. **Regular Clock-In/Clock-Out** - Basic attendance tracking
2. **Break Warnings** - Notifications only (after 6 hours)
3. **Overtime Warnings** - Notifications only (after 10 hours)
4. **Hard Limit Warnings** - Force action required (after 12 hours)

## Recommended Frontend Flow Options

### Option 1: One-Step Automatic (Current Default)

**Simple and Fast - Good for frequent users**

```javascript
// Take picture → Automatic clock-in/clock-out
const handleFaceClockIn = async (faceEncoding) => {
  try {
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/face-clock-in/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        encoding: faceEncoding,
        location_note: 'Front Desk Kiosk'
      })
    });

    const result = await response.json();
    
    if (result.action === 'clock_in') {
      showSuccess(`${result.staff.name} clocked in successfully!`);
    } else if (result.action === 'clock_out') {
      showSuccess(`${result.staff.name} clocked out after ${result.session_duration_hours}h`);
    } else if (result.action === 'unrostered_detected') {
      showUnrosteredConfirmation(result);
    }
  } catch (error) {
    showError('Face not recognized or system error');
  }
};
```

### Option 2: Two-Step Confirmation (Recommended for Better UX)

**Safer - Shows staff info and requires confirmation**

```javascript
// Step 1: Detect staff and show current status
const detectStaff = async (faceEncoding) => {
  try {
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/detect-staff/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ encoding: faceEncoding })
    });

    const result = await response.json();
    
    if (result.recognized) {
      showStaffConfirmation(result);
    } else {
      showError('Face not recognized');
    }
  } catch (error) {
    showError('Detection failed');
  }
};

// Step 2: Show confirmation UI
const showStaffConfirmation = (staffInfo) => {
  const { staff, current_status, available_actions } = staffInfo;
  
  const currentStatusText = current_status.is_clocked_in 
    ? `Currently clocked in (${current_status.session_duration_hours}h)`
    : 'Currently clocked out';
  
  const primaryAction = available_actions[0];
  const isUrgent = primaryAction.urgent; // Long session warning
  
  // Show UI with staff info
  displayConfirmationModal({
    staffName: staff.name,
    department: staff.department,
    currentStatus: currentStatusText,
    actionButton: {
      label: primaryAction.label,
      description: primaryAction.description,
      urgent: isUrgent,
      onClick: () => performAction(primaryAction.endpoint)
    }
  });
};

// Step 3: Perform confirmed action
const performAction = async (endpoint) => {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        encoding: lastFaceEncoding,
        location_note: 'Front Desk Kiosk'
      })
    });

    const result = await response.json();
    handleActionResult(result);
  } catch (error) {
    showError('Action failed');
  }
};
```

### Option 3: Hybrid Mode (Best of Both)

**Fast for regular users, confirmation for edge cases**

```javascript
const handleSmartClockIn = async (faceEncoding) => {
  // First detect staff
  const staffInfo = await detectStaff(faceEncoding);
  
  if (!staffInfo.recognized) {
    showError('Face not recognized');
    return;
  }

  // Check if confirmation needed
  const needsConfirmation = 
    staffInfo.current_status.session_duration_hours >= 8 ||  // Long session
    staffInfo.available_actions.some(a => a.urgent) ||       // Urgent action
    isFirstUseToday(staffInfo.staff.id);                     // First use today

  if (needsConfirmation) {
    showStaffConfirmation(staffInfo); // Two-step
  } else {
    performAutoAction(staffInfo.available_actions[0].endpoint); // One-step
  }
};
```

## Handle Unrostered Staff

```javascript
const showUnrosteredConfirmation = (unrosteredInfo) => {
  const { staff, message, confidence_score } = unrosteredInfo;
  
  displayUnrosteredModal({
    staffName: staff.name,
    message: message,
    confidence: Math.round((1 - confidence_score) * 100), // Convert to percentage
    onConfirm: () => forceClockInUnrostered(staff.id),
    onCancel: () => closeModal()
  });
};

const forceClockInUnrostered = async (staffId) => {
  try {
    const reason = prompt('Reason for unrostered clock-in:') || 'Emergency coverage';
    
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/force-clock-in/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        encoding: lastFaceEncoding,
        reason: reason,
        location_note: 'Front Desk Kiosk'
      })
    });

    const result = await response.json();
    
    if (result.action === 'unrostered_clock_in') {
      showSuccess(`${result.staff.name} clocked in (awaiting manager approval)`);
    }
  } catch (error) {
    showError('Force clock-in failed');
  }
};
```

## Break Functionality Status

**❌ NOT IMPLEMENTED** - Your system does not have:
- Break clock-in/clock-out tracking
- Break duration calculations
- Break compliance monitoring

**✅ IMPLEMENTED** - Your system has:
- Break reminders (notifications after 6 hours)
- Overtime warnings (notifications after 10 hours)
- Hard limit enforcement (forced action after 12 hours)

## To Add Break Functionality (Future Enhancement)

You would need to extend the ClockLog model:

```python
# Would require new model fields (not currently implemented)
class ClockLog(models.Model):
    # ... existing fields ...
    
    # Break tracking (NOT IMPLEMENTED)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True) 
    break_duration_minutes = models.IntegerField(default=0)
    is_on_break = models.BooleanField(default=False)
```

## Recommended Implementation

For your current needs, I recommend **Option 2 (Two-Step Confirmation)** because:

1. ✅ Shows staff name clearly before action
2. ✅ Displays current status (clocked in/out + duration)
3. ✅ Safer for clock-out (prevents accidental clock-out)
4. ✅ Handles long sessions with warnings
5. ✅ Better UX for unrostered staff
6. ✅ Confidence score visible to users

The endpoints are now ready for both approaches!