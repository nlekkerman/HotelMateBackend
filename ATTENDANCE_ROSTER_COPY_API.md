# Attendance Roster Copy Operations API

## Overview

The attendance system provides comprehensive copy operations for efficient roster management. All copy operations are department-oriented and support bulk operations for teams and individual staff members.

## Copy Operations

### 1. Copy Single Day for All Staff (Department-wide)

**URL:** `POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-roster-day-all/`

Copy an entire day's schedule to another date, optionally filtered by department.

#### Request Payload
```json
{
  "source_date": "2025-12-01",
  "target_date": "2025-12-08",
  "department_slug": "front-office"  // Optional: specific department only
}
```

#### Use Cases
- Copy Monday's schedule to next Monday for entire department
- Replicate successful shift patterns
- Quick setup for recurring weekly schedules

#### Example
```json
POST /api/staff/hotel/hotel-killarney/attendance/shift-copy/copy-roster-day-all/
{
  "source_date": "2025-12-01",
  "target_date": "2025-12-08",
  "department_slug": "food-and-beverage"
}
```

---

### 2. Copy One Staff for Entire Week

**URL:** `POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-week-staff/`

Copy all shifts for a single staff member from one roster period to another.

#### Request Payload
```json
{
  "staff_id": 35,
  "source_period_id": 10,
  "target_period_id": 11
}
```

#### Use Cases
- Copy consistent staff member's schedule to next period
- Template staff scheduling patterns
- Maintain regular staff rotations

#### Example
```json
POST /api/staff/hotel/hotel-killarney/attendance/shift-copy/copy-week-staff/
{
  "staff_id": 35,
  "source_period_id": 10,
  "target_period_id": 11
}
```

---

### 3. Copy Multiple Selected Staff (Bulk Department Copy)

**URL:** `POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-roster-bulk/`

Copy shifts for multiple staff members or entire departments between periods.

#### Request Payload
```json
{
  "source_period_id": 10,
  "target_period_id": 11,
  "staff_ids": [35, 36, 37],        // Optional: specific staff only
  "department_slug": "front-office"  // Optional: specific department
}
```

#### Filtering Options
- **No filters:** Copy all shifts from source to target period
- **Department only:** Copy entire department's roster
- **Staff IDs only:** Copy specific staff members (any department)
- **Both:** Copy specific staff from specific department

#### Use Cases
- Copy entire department roster to new period
- Copy selected team members
- Department-specific roster templates
- Cross-training staff assignments

#### Examples

**Copy Entire Front Office Department:**
```json
{
  "source_period_id": 10,
  "target_period_id": 11,
  "department_slug": "front-office"
}
```

**Copy Specific Staff Members:**
```json
{
  "source_period_id": 10,
  "target_period_id": 11,
  "staff_ids": [35, 36, 37]
}
```

**Copy Specific Staff from Specific Department:**
```json
{
  "source_period_id": 10,
  "target_period_id": 11,
  "staff_ids": [35, 36],
  "department_slug": "housekeeping"
}
```

---

### 4. Copy Entire Period (All Departments)

**URL:** `POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-entire-period/`

Copy complete roster from one period to another, including all departments and staff.

#### Request Payload
```json
{
  "source_period_id": 10,
  "target_period_id": 11
}
```

#### Use Cases
- Clone successful roster periods
- Seasonal schedule templates
- Emergency backup roster creation
- Standard operating schedule templates

#### Example
```json
POST /api/staff/hotel/hotel-killarney/attendance/shift-copy/copy-entire-period/
{
  "source_period_id": 10,
  "target_period_id": 11
}
```

---

## Department-Oriented Features

### Supported Department Slugs
- `"front-office"`
- `"food-and-beverage"`
- `"housekeeping"`
- `"maintenance"`
- `"management"`
- `"security"`

### Cross-Department Support
- Staff can work in multiple departments
- Copy operations respect department assignments
- Split shifts across departments are preserved

### Bulk Department Operations
- Copy entire department rosters
- Maintain department-specific shift patterns
- Preserve location assignments within departments

## Response Format

### Success Response (200 OK)
```json
{
  "detail": "Successfully copied 25 shifts",
  "copied_shifts": 25,
  "skipped_conflicts": 2,
  "operation_details": {
    "source_period": "Week 1 - Dec 01-07",
    "target_period": "Week 2 - Dec 08-14",
    "departments_affected": ["front-office", "food-and-beverage"],
    "staff_affected": [35, 36, 37, 42, 43]
  }
}
```

### Error Response (400 Bad Request)
```json
{
  "detail": "Cannot copy shifts to a published period.",
  "error_code": "TARGET_PERIOD_PUBLISHED"
}
```

## Common Error Scenarios

### 1. Target Period Published
```json
{
  "detail": "Cannot copy shifts to a published period.",
  "error_code": "TARGET_PERIOD_PUBLISHED"
}
```

### 2. No Source Shifts Found
```json
{
  "detail": "No shifts found in the source period.",
  "error_code": "NO_SOURCE_SHIFTS"
}
```

### 3. Period Hotel Mismatch
```json
{
  "detail": "Source and target periods must belong to the same hotel.",
  "error_code": "HOTEL_MISMATCH"
}
```

### 4. Rate Limited
```json
{
  "detail": "Too many copy operations. Please wait before trying again.",
  "error_code": "RATE_LIMITED"
}
```

## Advanced Usage Patterns

### 1. Progressive Department Setup
```javascript
// Copy departments one by one for better control
const departments = ['front-office', 'food-and-beverage', 'housekeeping'];

for (const dept of departments) {
  await copyDepartmentRoster({
    source_period_id: 10,
    target_period_id: 11,
    department_slug: dept
  });
}
```

### 2. Template-Based Scheduling
```javascript
// Create roster templates for different seasons
const templates = {
  summer: { source_period_id: 5 },
  winter: { source_period_id: 12 },
  holiday: { source_period_id: 8 }
};

// Apply template to new period
await copyEntirePeriod({
  source_period_id: templates.summer.source_period_id,
  target_period_id: newPeriodId
});
```

### 3. Selective Staff Rotation
```javascript
// Copy core staff, then add temporary staff manually
await copyBulkRoster({
  source_period_id: 10,
  target_period_id: 11,
  staff_ids: coreStaffIds,
  department_slug: 'front-office'
});

// Add temporary/seasonal staff separately using bulk-save
```

### 4. Cross-Training Schedules
```javascript
// Copy staff to different departments for cross-training
await copyWeekStaff({
  staff_id: 35,
  source_period_id: 10,
  target_period_id: 11
});

// Then modify department assignments in bulk-save
```

## Performance Considerations

### Rate Limiting
- Copy operations are rate limited to prevent system overload
- Large operations (100+ shifts) may have extended processing time
- Use bulk operations instead of multiple small copies

### Conflict Resolution
- Existing shifts in target period are **preserved** by default
- Copy operations **skip** conflicting shifts (same staff/date/time)
- Use `skipped_conflicts` count in response to track this

### Validation Rules
- Target periods cannot be published/locked
- Source and target must belong to same hotel
- Staff must exist and be active
- Departments must be valid for the hotel

## Integration with Frontend

### Copy Button Implementation
```javascript
async function copyDepartmentWeek(sourcePeriod, targetPeriod, department) {
  const response = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/shift-copy/copy-roster-bulk/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_period_id: sourcePeriod,
      target_period_id: targetPeriod,
      department_slug: department
    })
  });
  
  const result = await response.json();
  
  if (response.ok) {
    showSuccess(`Copied ${result.copied_shifts} shifts. Skipped ${result.skipped_conflicts} conflicts.`);
    refreshRosterView();
  } else {
    showError(result.detail);
  }
}
```

### Batch Copy UI
```javascript
// Allow users to select multiple copy operations
const copyOperations = [
  { type: 'department', department: 'front-office' },
  { type: 'staff', staffIds: [35, 36] },
  { type: 'day', sourceDate: '2025-12-01', targetDate: '2025-12-08' }
];

// Execute in sequence with progress feedback
for (const operation of copyOperations) {
  await executeCopyOperation(operation);
  updateProgressBar(operations.indexOf(operation) + 1, operations.length);
}
```