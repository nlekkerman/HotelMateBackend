# Face Clock-In Frontend Implementation

## Unrostered Staff Confirmation Dialog

When face recognition detects an unrostered staff member, display a confirmation modal:

### 1. Confirmation Dialog Layout
```
┌─────────────────────────────────────┐
│  ⚠️  Unrostered Clock-In Detected    │
├─────────────────────────────────────┤
│                                     │
│  [Staff Photo]    Nikola Simic      │
│                   Front Office       │
│                                     │
│  No scheduled shift found.          │
│  Confirm to clock in anyway?        │
│                                     │
│  Reason (optional):                 │
│  [___________________________]     │
│                                     │
│  Location:                          │
│  [___________________________]     │
│                                     │
│      [Cancel]    [Confirm Clock In] │
└─────────────────────────────────────┘
```

### 2. Display Staff Image
**IMPORTANT:** Always show the staff's face image for verification:

```javascript
// Get staff image from face recognition data
const staffImage = result.staff.image; // URL from face registration
```

### 3. Success Message with Image
After successful clock-in, show confirmation with staff photo:

```
┌─────────────────────────────────────┐
│  ✅ Clock-In Successful             │
├─────────────────────────────────────┤
│                                     │
│  [Staff Photo]    Nikola Simic      │
│                   Front Office       │
│                                     │
│  Clocked in at 09:15 AM             │
│  Status: On Duty                    │
│                                     │
│         [Continue]                  │
└─────────────────────────────────────┘
```

### 4. Key Frontend Requirements

#### Response Handling:
- Check `action` field in API response
- Show confirmation for `action: 'unrostered_detected'`
- Display success for `action: 'clock_in_success'`

#### Staff Image Display:
- **Always show staff face photo** for verification
- Image URL is in `result.staff.image`
- Helps confirm correct person was recognized

#### Confirmation Button:
- POST to `result.confirmation_endpoint`
- Include same face `encoding` from original scan
- Add `reason` and `location_note` from form inputs

#### Visual Feedback:
- Use staff photo for trust and verification
- Clear success/warning messages
- Proper button states (loading, disabled)

### 5. Code Example
```javascript
function showUnrosteredDialog(result) {
  return new Promise((resolve) => {
    const modal = createModal({
      title: "⚠️ Unrostered Clock-In",
      image: result.staff.image, // Show staff photo!
      message: result.message,
      staffName: result.staff.name,
      department: result.staff.department,
      onConfirm: (reason, location) => {
        resolve({ proceed: true, reason, location });
      },
      onCancel: () => {
        resolve({ proceed: false });
      }
    });
    modal.show();
  });
}
```

**Remember:** The staff image is crucial for verification - always display it!