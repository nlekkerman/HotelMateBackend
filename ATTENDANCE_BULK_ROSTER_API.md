# Attendance Bulk Roster API Guide

## Bulk Save Shifts Endpoint

**URL:** `POST /api/staff/hotel/{hotel_slug}/attendance/shifts/bulk-save/`

**Example:** `POST /api/staff/hotel/hotel-killarney/attendance/shifts/bulk-save/`

## Request Payload Format

```json
{
  "hotel": <hotel_id_number>,
  "period": <period_id_number>,
  "shifts": [
    {
      "staff": <staff_id_number>,
      "department": "<department_slug>",
      "shift_date": "YYYY-MM-DD",
      "shift_start": "HH:MM",
      "shift_end": "HH:MM",
      "location_id": <location_id_number>,
      "notes": "Optional notes",
      "break_start": "HH:MM",  // Optional
      "break_end": "HH:MM"     // Optional
    }
  ]
}
```

## Example Request

```json
{
  "hotel": 1,
  "period": 15,
  "shifts": [
    {
      "staff": 35,
      "department": "front-office",
      "shift_date": "2025-12-01",
      "shift_start": "09:00",
      "shift_end": "17:00",
      "location_id": 34,
      "notes": "Morning shift"
    },
    {
      "staff": 36,
      "department": "front-office", 
      "shift_date": "2025-12-01",
      "shift_start": "17:00",
      "shift_end": "23:00",
      "location_id": 34,
      "notes": "Evening shift"
    },
    {
      "staff": 35,
      "department": "front-office",
      "shift_date": "2025-12-02",
      "shift_start": "09:00",
      "shift_end": "17:00",
      "location_id": 34,
      "notes": ""
    }
  ]
}
```

## Key Features

### 1. Default Values
- Set `hotel` and `period` at the top level
- They'll be automatically applied to all shifts that don't specify them
- Individual shifts can override these defaults if needed

### 2. Create vs Update
- **Create:** Shifts without `id` field are created as new entries
- **Update:** Shifts with `id` field update existing entries

### 3. Validation & Safety
- **Overlap Detection:** Automatically checks for scheduling conflicts
- **Duplicate Prevention:** Prevents same staff/date/time duplicates
- **Transaction Safety:** All operations are atomic (all succeed or all fail)
- **Batch Validation:** Validates entire batch before processing

### 4. Department Field
- Uses **department slug** (string), not ID
- Common department slugs:
  - `"front-office"`
  - `"food-and-beverage"`
  - `"housekeeping"`
  - `"maintenance"`

## Response Format

### Success Response (200 OK)
```json
{
  "created": [
    {
      "id": 123,
      "staff": 35,
      "shift_date": "2025-12-01",
      "shift_start": "09:00",
      "shift_end": "17:00",
      // ... full shift object
    }
  ],
  "updated": [
    {
      "id": 124,
      "staff": 36,
      // ... updated shift object
    }
  ],
  "errors": []
}
```

### Error Response (400 Bad Request)
```json
{
  "created": [],
  "updated": [],
  "errors": [
    {
      "index": 0,
      "error": "Duplicate shift in batch."
    },
    {
      "id": 125,
      "detail": "Shift not found"
    }
  ]
}
```

## Split Shifts Support

The system supports **split shifts** - multiple shifts for the same staff member on the same day. This allows for:

- Morning + Evening shifts with breaks in between
- Multiple location assignments per day
- Flexible scheduling patterns

### Example Split Shift
```json
{
  "hotel": 1,
  "period": 15,
  "shifts": [
    // Morning shift
    {
      "staff": 35,
      "department": "front-office",
      "shift_date": "2025-12-01",
      "shift_start": "09:00",
      "shift_end": "13:00",
      "location_id": 34,
      "notes": "Morning reception"
    },
    // Evening shift (same staff, same day)
    {
      "staff": 35,
      "department": "food-and-beverage",
      "shift_date": "2025-12-01",
      "shift_start": "18:00",
      "shift_end": "23:00",
      "location_id": 35,
      "notes": "Evening restaurant"
    }
  ]
}
```

## Frontend Implementation Strategy

### 1. Local Storage Optimization
Store all roster changes locally before bulk submission:

```javascript
// Local storage structure
const rosterState = {
  hotel_id: 1,
  period_id: 15,
  shifts: [
    // All entered shifts stored here
  ],
  isDirty: true, // Has unsaved changes
  lastSaved: null
}

// Save to localStorage after each edit
localStorage.setItem('roster_draft', JSON.stringify(rosterState));
```

### 2. Progressive Shift Building
Allow users to create multiple shifts per staff member:

```javascript
// Add shift to local storage
function addShiftToRoster(staffId, date, shiftData) {
  const roster = JSON.parse(localStorage.getItem('roster_draft') || '{}');
  
  // Find existing shifts for this staff/date
  const existingShifts = roster.shifts.filter(s => 
    s.staff === staffId && s.shift_date === date
  );
  
  // Add new shift (supports split shifts)
  roster.shifts.push({
    staff: staffId,
    shift_date: date,
    ...shiftData
  });
  
  roster.isDirty = true;
  localStorage.setItem('roster_draft', JSON.stringify(roster));
}
```

### 3. Bulk Finalize Button
Single button to submit all changes:

```javascript
// Finalize roster - submit all changes at once
async function finalizeRoster() {
  const roster = JSON.parse(localStorage.getItem('roster_draft'));
  
  if (!roster.isDirty) {
    alert('No changes to save');
    return;
  }
  
  try {
    const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/shifts/bulk-save/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hotel: roster.hotel_id,
        period: roster.period_id,
        shifts: roster.shifts
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      // Success - clear local storage
      roster.isDirty = false;
      roster.lastSaved = new Date().toISOString();
      localStorage.setItem('roster_draft', JSON.stringify(roster));
      
      alert(`Roster saved! Created: ${result.created.length}, Updated: ${result.updated.length}`);
    } else {
      // Handle errors
      console.error('Bulk save errors:', result.errors);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}
```

## Usage Tips

### 1. Weekly Roster Creation
Create shifts for an entire week by including all 7 days in the shifts array:

```json
{
  "hotel": 1,
  "period": 15,
  "shifts": [
    // Monday shifts
    {"staff": 35, "department": "front-office", "shift_date": "2025-12-01", "shift_start": "09:00", "shift_end": "17:00", "location_id": 34},
    {"staff": 36, "department": "front-office", "shift_date": "2025-12-01", "shift_start": "17:00", "shift_end": "01:00", "location_id": 34},
    
    // Tuesday shifts
    {"staff": 35, "department": "front-office", "shift_date": "2025-12-02", "shift_start": "09:00", "shift_end": "17:00", "location_id": 34},
    
    // ... continue for rest of week
  ]
}
```

### 2. Mixed Create/Update Operations
```json
{
  "hotel": 1,
  "period": 15,
  "shifts": [
    // Create new shift (no id)
    {
      "staff": 35,
      "department": "front-office",
      "shift_date": "2025-12-03",
      "shift_start": "09:00",
      "shift_end": "17:00",
      "location_id": 34
    },
    // Update existing shift (with id)
    {
      "id": 123,
      "shift_start": "10:00",
      "shift_end": "18:00",
      "notes": "Updated timing"
    }
  ]
}
```

### 3. Required Data for Frontend
Before making the bulk save request, ensure you have:

1. **Hotel ID** (number) - Get from hotel slug lookup
2. **Period ID** (number) - Current roster period for the week
3. **Staff IDs** (numbers) - All staff members being scheduled
4. **Department Slugs** (strings) - Department names in slug format
5. **Location IDs** (numbers) - Available shift locations

## Frontend UX Recommendations

### 1. Visual Indicators
- **Unsaved Changes Badge:** Show count of pending shifts
- **Split Shift Visualization:** Different colors/icons for multiple shifts per day
- **Validation Warnings:** Real-time overlap detection before submission

### 2. User Workflow
```
1. User enters individual shifts (stored locally)
2. System allows multiple shifts per staff/day (split shifts)
3. Visual feedback shows all pending changes
4. "Finalize Roster" button submits everything at once
5. Success/error feedback with detailed results
```

### 3. Auto-Save & Recovery
```javascript
// Auto-save every 30 seconds
setInterval(() => {
  const roster = JSON.parse(localStorage.getItem('roster_draft') || '{}');
  if (roster.isDirty && roster.shifts.length > 0) {
    // Show "Auto-saved draft" indicator
    console.log('Draft auto-saved');
  }
}, 30000);

// Recover on page load
window.addEventListener('load', () => {
  const roster = JSON.parse(localStorage.getItem('roster_draft') || '{}');
  if (roster.isDirty && roster.shifts.length > 0) {
    if (confirm('You have unsaved roster changes. Restore them?')) {
      // Restore shifts to UI
      restoreShiftsFromDraft(roster);
    }
  }
});
```

## Error Handling

Common errors and solutions:

- **"Duplicate shift in batch"** - Remove duplicate entries from request
- **"This field is required"** - Ensure all required fields are included
- **"Shift not found"** - Check that the `id` exists when updating
- **"Overlap detected"** - Resolve scheduling conflicts before submitting