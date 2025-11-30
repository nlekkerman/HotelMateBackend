# Frontend Attendance & Roster API Guide

This guide provides comprehensive documentation for all attendance and roster-related endpoints in the HotelMate Backend system.

## Base URL Structure

All staff attendance and roster endpoints follow this pattern:
```
/api/staff/hotel/{hotel_slug}/attendance/{endpoint}
```

## Authentication

All endpoints require:
- **Authentication**: Bearer token in Authorization header
- **Staff Permission**: User must be authenticated staff member
- **Hotel Access**: Staff must belong to the specified hotel

```javascript
headers: {
  'Authorization': 'Bearer your_jwt_token',
  'Content-Type': 'application/json'
}
```

---

## 1. Face Recognition Management

### 1.1 Face Registration (Enhanced)

**Register Staff Face with Cloudinary Storage**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/face-management/register-face/
```

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "encoding": [0.123, -0.456, 0.789, ...], 
  "staff_id": 123,
  "consent_given": true
}
```

**Response:**
```json
{
  "message": "Face registered successfully",
  "face_data": {
    "id": 45,
    "staff": 123,
    "staff_name": "John Doe",
    "hotel": 1,
    "hotel_slug": "grand-hotel",
    "image_url": "https://res.cloudinary.com/.../staff_faces/face_image.jpg",
    "public_id": "staff_faces/face_image_xyz123",
    "encoding_length": 128,
    "is_active": true,
    "consent_given": true,
    "registered_by": "Manager Smith",
    "created_at": "2025-11-30T10:00:00Z",
    "updated_at": "2025-11-30T10:00:00Z"
  }
}
```

### 1.2 Face Revocation

**Revoke Staff Face Data**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/face-management/revoke-face/
```

**Request Body:**
```json
{
  "staff_id": 123,
  "reason": "Privacy request from staff member"
}
```

**Response:**
```json
{
  "message": "Face data revoked successfully",
  "staff_id": 123,
  "staff_name": "John Doe",
  "revoked_at": "2025-11-30T15:30:00Z"
}
```

### 1.3 List Registered Faces

**List All Registered Faces (Privacy-Safe)**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/face-management/list-faces/
```

**Query Parameters:**
- `active_only`: true/false (default: true)
- `staff_id`: Filter by specific staff ID

**Response:**
```json
{
  "count": 25,
  "faces": [
    {
      "id": 45,
      "staff": 123,
      "staff_name": "John Doe",
      "hotel": 1,
      "image_url": "https://res.cloudinary.com/.../face_image.jpg",
      "public_id": "staff_faces/xyz123",
      "encoding_length": 128,
      "is_active": true,
      "consent_given": true,
      "registered_by_name": "Manager Smith",
      "created_at": "2025-11-30T10:00:00Z",
      "updated_at": "2025-11-30T10:00:00Z"
    }
  ]
}
```

### 1.4 Face Status Check

**Check Current User's Face Registration Status**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/face-management/face-status/
```

**Response (Registered):**
```json
{
  "has_registered_face": true,
  "face_data": {
    "id": 45,
    "staff": 123,
    "staff_name": "John Doe",
    "image_url": "https://res.cloudinary.com/.../face_image.jpg",
    "is_active": true,
    "consent_given": true,
    "created_at": "2025-11-30T10:00:00Z"
  }
}
```

**Response (Not Registered):**
```json
{
  "has_registered_face": false,
  "face_data": null
}
```

### 1.5 Face Audit Logs

**Get Face Lifecycle Audit Logs**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/face-management/audit-logs/
```

**Query Parameters:**
- `staff_id`: Filter by staff ID
- `action`: Filter by action (REGISTERED/REVOKED/RE_REGISTERED)
- `start_date`: Filter from date (YYYY-MM-DD)
- `end_date`: Filter to date (YYYY-MM-DD)
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 50, max: 200)

**Response:**
```json
{
  "count": 150,
  "page": 1,
  "page_size": 50,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": 78,
      "hotel_slug": "grand-hotel",
      "staff": 123,
      "staff_name": "John Doe", 
      "action": "REGISTERED",
      "performed_by": 45,
      "performed_by_name": "Manager Smith",
      "reason": "",
      "consent_given": true,
      "client_ip": "192.168.1.100",
      "created_at": "2025-11-30T10:00:00Z"
    }
  ]
}
```

---

## 2. Clock Management Endpoints

### 2.1 Enhanced Face Clock-In/Out

**Clock In/Out Using Face Recognition (Enhanced)**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/face-management/face-clock-in/
```

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "encoding": [0.123, -0.456, 0.789, ...],
  "location_note": "Front Desk",
  "force_action": "clock_in"
}
```

**Response (Clock In):**
```json
{
  "action": "clock_in",
  "message": "Clocked in successfully",
  "confidence_score": 0.23,
  "clock_log": {
    "id": 234,
    "staff": 123,
    "staff_name": "John Doe",
    "hotel_slug": "grand-hotel",
    "time_in": "2025-11-30T09:00:00Z",
    "time_out": null,
    "verified_by_face": true,
    "location_note": "Front Desk",
    "is_unrostered": false,
    "roster_shift": {
      "id": 456,
      "date": "2025-11-30",
      "start": "09:00:00",
      "end": "17:00:00",
      "location": "Front Desk",
      "department": "Reception"
    }
  }
}
```

**Response (Clock Out):**
```json
{
  "action": "clock_out",
  "message": "Clocked out successfully",
  "confidence_score": 0.23,
  "clock_log": {
    "id": 234,
    "staff": 123,
    "staff_name": "John Doe",
    "time_in": "2025-11-30T09:00:00Z",
    "time_out": "2025-11-30T17:00:00Z",
    "hours_worked": "8.00",
    "verified_by_face": true,
    "location_note": "Front Desk"
  }
}
```

**Error Response (Face Not Recognized):**
```json
{
  "error": "Face not recognized",
  "confidence_score": 0.85,
  "message": "No matching face found or confidence too low"
}
```

### 2.2 Legacy Face Registration (Deprecated)

**⚠️ DEPRECATED: Use face-management endpoints instead**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/register-face/
```

### 2.3 Legacy Face Clock-In (Deprecated)

**⚠️ DEPRECATED: Use face-management endpoints instead**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/face-clock-in/
```

### 1.3 Clock Logs Management

**List Clock Logs**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/clock-logs/
```

**Query Parameters:**
- `staff`: Filter by staff ID
- `date`: Filter by specific date (YYYY-MM-DD)
- `start_date`: Filter from date
- `end_date`: Filter to date
- `department`: Filter by department slug
- `is_unrostered`: Filter unrostered sessions (true/false)
- `is_approved`: Filter approval status
- `page`: Page number for pagination

**Get Current Clock Status**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/clock-logs/status/
```

**Response:**
```json
{
  "is_clocked_in": true,
  "current_session": {
    "id": 234,
    "time_in": "2025-11-30T09:00:00Z",
    "location_note": "Front Desk",
    "hours_worked": 4.5
  }
}
```

**Get Currently Clocked In Staff**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/clock-logs/currently-clocked-in/
```

**Get Department Logs**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/clock-logs/department-logs/?department={dept_slug}&date={YYYY-MM-DD}
```

### 1.4 Unrostered Clock-In Management

**Confirm Unrostered Clock-In**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/unrostered-confirm/
```

**Request Body:**
```json
{
  "location_note": "Emergency shift - Front Desk",
  "expected_duration_hours": 8
}
```

**Approve Unrostered Session**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/approve/
```

**Request Body:**
```json
{
  "approval_note": "Emergency coverage approved"
}
```

**Reject Unrostered Session**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/reject/
```

**Request Body:**
```json
{
  "rejection_reason": "Unauthorized overtime"
}
```

### 1.5 Clock Management Actions

**Auto-Attach Shift to Clock Log**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/auto-attach-shift/
```

**Relink Day Clock Logs**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/relink-day/
```

**Request Body:**
```json
{
  "date": "2025-11-30",
  "staff_ids": [123, 124, 125]
}
```

**Stay Clocked In (Acknowledge Long Session)**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/stay-clocked-in/
```

**Force Clock Out**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/clock-logs/{log_id}/force-clock-out/
```

---

## 2. Roster Period Management

### 2.1 Roster Periods CRUD

**List Roster Periods**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/periods/
```

**Response:**
```json
[
  {
    "id": 12,
    "title": "Week of Nov 25",
    "hotel": 1,
    "start_date": "2025-11-25",
    "end_date": "2025-12-01",
    "created_by": 45,
    "created_by_name": "Manager Smith",
    "published": true,
    "is_finalized": false,
    "finalized_by": null,
    "finalized_by_name": null,
    "finalized_at": null
  }
]
```

**Create Roster Period**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/periods/
```

**Request Body:**
```json
{
  "title": "Week of Dec 02",
  "start_date": "2025-12-02",
  "end_date": "2025-12-08",
  "published": false
}
```

**Get Roster Period**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/
```

**Update Roster Period**
```http
PUT /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/
```

**Delete Roster Period**
```http
DELETE /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/
```

### 2.2 Roster Period Actions

**Create Weekly Roster Period**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/periods/create-for-week/
```

**Request Body:**
```json
{
  "start_date": "2025-12-02"
}
```

**Add Shift to Period**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/add-shift/
```

**Request Body:**
```json
{
  "staff": 123,
  "shift_date": "2025-12-02",
  "shift_start": "09:00:00",
  "shift_end": "17:00:00",
  "location": 5,
  "department": 2
}
```

**Create Department Roster**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/create-department-roster/
```

**Request Body:**
```json
{
  "department_id": 2,
  "shifts": [
    {
      "staff": 123,
      "shift_date": "2025-12-02",
      "shift_start": "09:00:00",
      "shift_end": "17:00:00",
      "location": 5
    }
  ]
}
```

### 2.3 Period Finalization

**Finalize Roster Period**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/finalize/
```

**Response:**
```json
{
  "detail": "Period 'Week of Nov 25' finalized successfully.",
  "period": {
    "id": 12,
    "is_finalized": true,
    "finalized_by": 45,
    "finalized_by_name": "Manager Smith",
    "finalized_at": "2025-11-30T15:30:00Z"
  }
}
```

**Unfinalize Roster Period**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/unfinalize/
```

**Get Finalization Status**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/finalization-status/
```

**Response:**
```json
{
  "can_finalize": true,
  "validation_errors": [],
  "warnings": [
    "Some shifts have no assigned staff"
  ],
  "stats": {
    "total_shifts": 45,
    "staffed_shifts": 42,
    "unstaffed_shifts": 3
  }
}
```

### 2.4 Period PDF Export

**Export Period as PDF**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/periods/{period_id}/export-pdf/
```

**Query Parameters:**
- `format`: pdf (default)
- `department`: Filter by department slug

---

## 3. Staff Roster (Shifts) Management

### 3.1 Shift CRUD Operations

**List Shifts**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/shifts/
```

**Query Parameters:**
- `staff`: Staff ID
- `staff_id`: Staff ID (alternative)
- `period`: Period ID
- `location`: Location ID
- `start`: Start date (YYYY-MM-DD)
- `end`: End date (YYYY-MM-DD)
- `department`: Department slug

**Response:**
```json
[
  {
    "id": 789,
    "staff": 123,
    "staff_name": "John Doe",
    "period": 12,
    "shift_date": "2025-12-02",
    "shift_start": "09:00:00",
    "shift_end": "17:00:00",
    "location": {
      "id": 5,
      "name": "Front Desk"
    },
    "department": {
      "id": 2,
      "name": "Reception",
      "slug": "reception"
    },
    "is_approved": true,
    "approved_by": 45
  }
]
```

**Create Shift**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/shifts/
```

**Update Shift**
```http
PUT /api/staff/hotel/{hotel_slug}/attendance/shifts/{shift_id}/
```

**Delete Shift**
```http
DELETE /api/staff/hotel/{hotel_slug}/attendance/shifts/{shift_id}/
```

### 3.2 Bulk Operations

**Bulk Save Shifts**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/shifts/bulk-save/
```

**Request Body:**
```json
{
  "shifts": [
    {
      "id": 789,
      "staff": 123,
      "shift_date": "2025-12-02",
      "shift_start": "09:00:00",
      "shift_end": "17:00:00",
      "location": 5
    },
    {
      "staff": 124,
      "shift_date": "2025-12-02",
      "shift_start": "10:00:00",
      "shift_end": "18:00:00",
      "location": 6
    }
  ],
  "period": 12
}
```

### 3.3 Shift PDF Reports

**Daily Roster PDF**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/shifts/daily-pdf/
```

**Query Parameters:**
- `date`: YYYY-MM-DD (required)
- `department`: Department slug (optional)

**Staff Roster PDF**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/shifts/staff-pdf/
```

**Query Parameters:**
- `staff_id`: Staff ID (required)
- `start_date`: YYYY-MM-DD (required)
- `end_date`: YYYY-MM-DD (required)

---

## 4. Roster Analytics

Base URL for analytics: `/api/staff/hotel/{hotel_slug}/attendance/roster-analytics/`

### 4.1 Summary Reports

**KPIs Overview**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/kpis/
```

**Query Parameters:**
- `start_date`: YYYY-MM-DD (required)
- `end_date`: YYYY-MM-DD (required)
- `department`: Department slug (optional)

**Response:**
```json
{
  "total_scheduled_hours": 1680,
  "total_worked_hours": 1632,
  "attendance_rate": 97.14,
  "average_hours_per_staff": 40.8,
  "total_staff_count": 40,
  "total_departments": 4,
  "overtime_hours": 52,
  "undertime_hours": 28
}
```

**Department Summary**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/department-summary/
```

**Response:**
```json
[
  {
    "department_name": "Reception",
    "department_slug": "reception",
    "total_scheduled_hours": 420,
    "total_worked_hours": 415,
    "attendance_rate": 98.81,
    "staff_count": 10,
    "average_hours_per_staff": 41.5
  }
]
```

**Staff Summary**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/staff-summary/
```

**Response:**
```json
[
  {
    "staff_id": 123,
    "staff_name": "John Doe",
    "department_name": "Reception",
    "total_scheduled_hours": 42,
    "total_worked_hours": 41.5,
    "attendance_rate": 98.81,
    "shifts_count": 6,
    "average_hours_per_shift": 6.92
  }
]
```

### 4.2 Daily Analytics

**Daily Totals**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/daily-totals/
```

**Response:**
```json
[
  {
    "date": "2025-11-30",
    "total_scheduled_hours": 240,
    "total_worked_hours": 238,
    "attendance_rate": 99.17,
    "staff_count": 30,
    "shifts_count": 35
  }
]
```

**Daily by Department**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/daily-by-department/
```

**Daily by Staff**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/daily-by-staff/
```

### 4.3 Weekly Analytics

**Weekly Totals**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/weekly-totals/
```

**Weekly by Department**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/weekly-by-department/
```

**Weekly by Staff**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/weekly-by-staff/
```

---

## 5. Shift Locations

**List Shift Locations**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/shift-locations/
```

**Response:**
```json
[
  {
    "id": 5,
    "name": "Front Desk",
    "description": "Main reception area",
    "hotel": 1,
    "is_active": true
  }
]
```

**Create Shift Location**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/shift-locations/
```

**Request Body:**
```json
{
  "name": "Housekeeping Storage",
  "description": "Storage area for housekeeping supplies",
  "is_active": true
}
```

---

## 6. Daily Plans

### 6.1 Daily Plan Management

**List Daily Plans**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/daily-plans/
```

**Create Daily Plan**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/daily-plans/
```

**Request Body:**
```json
{
  "date": "2025-12-02",
  "department": 2,
  "notes": "Special event coverage needed"
}
```

### 6.2 Department-Specific Daily Plans

**Prepare Daily Plan for Department**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/departments/{dept_slug}/daily-plans/prepare-daily-plan/
```

**Query Parameters:**
- `date`: YYYY-MM-DD (required)

**Download Daily Plan PDF**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/departments/{dept_slug}/daily-plans/download-pdf/
```

**Query Parameters:**
- `date`: YYYY-MM-DD (required)

---

## 7. Roster Copy Operations

### 7.1 Bulk Copy Operations

**Copy Entire Day Roster**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-roster-day-all/
```

**Request Body:**
```json
{
  "source_date": "2025-11-30",
  "target_dates": ["2025-12-07", "2025-12-14"],
  "department_ids": [1, 2, 3]
}
```

**Copy Roster Bulk**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-roster-bulk/
```

**Request Body:**
```json
{
  "source_period_id": 12,
  "target_period_id": 13,
  "copy_options": {
    "departments": [1, 2],
    "staff_ids": [123, 124, 125],
    "preserve_locations": true
  }
}
```

**Copy Week for Staff**
```http
POST /api/staff/hotel/{hotel_slug}/attendance/shift-copy/copy-week-staff/
```

**Request Body:**
```json
{
  "source_start_date": "2025-11-25",
  "target_start_date": "2025-12-02",
  "staff_id": 123
}
```

---

## 8. Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid date format",
  "errors": {
    "start_date": ["Enter a valid date."]
  }
}
```

**403 Forbidden**
```json
{
  "detail": "You don't have access to this hotel"
}
```

**404 Not Found**
```json
{
  "detail": "Roster period not found"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": "Validation failed",
  "errors": {
    "shift_end": ["End time must be after start time"]
  }
}
```

---

## 9. Pagination

Most list endpoints support pagination:

**Request:**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/shifts/?page=2&page_size=20
```

**Response:**
```json
{
  "count": 150,
  "next": "http://api.example.com/api/staff/hotel/grand-hotel/attendance/shifts/?page=3",
  "previous": "http://api.example.com/api/staff/hotel/grand-hotel/attendance/shifts/?page=1",
  "results": [...]
}
```

---

## 10. WebSocket Events (If Applicable)

For real-time updates, subscribe to these WebSocket channels:

```javascript
// Clock-in/out updates
ws://api.example.com/ws/staff/{hotel_slug}/attendance/clock-logs/

// Roster updates
ws://api.example.com/ws/staff/{hotel_slug}/attendance/roster-updates/

// Unrostered approvals
ws://api.example.com/ws/staff/{hotel_slug}/attendance/unrostered-approvals/
```

---

## 11. Usage Examples

### Complete Face Registration & Clock-In Flow
```javascript
// 1. Check if user has registered face
const faceStatusResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/face-status/`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const faceStatus = await faceStatusResponse.json();

if (!faceStatus.has_registered_face) {
  // 2. Register face first (with user consent)
  const registrationResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/register-face/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image: `data:image/jpeg;base64,${base64ImageData}`,
      encoding: faceEncodingArray, // 128-dimensional array
      consent_given: true
    })
  });
  
  const registrationResult = await registrationResponse.json();
  console.log('Face registered:', registrationResult);
}

// 3. Check current clock status
const statusResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/clock-logs/status/`);
const status = await statusResponse.json();

if (!status.is_clocked_in) {
  // 4. Clock in using enhanced face recognition
  const clockInResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/face-clock-in/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image: `data:image/jpeg;base64,${base64ImageData}`,
      encoding: faceEncodingArray,
      location_note: 'Front Desk'
    })
  });
  
  const clockResult = await clockInResponse.json();
  
  if (clockResult.error) {
    console.error('Clock-in failed:', clockResult.error);
    // Handle face not recognized
  } else {
    console.log('Clocked in successfully:', clockResult);
    console.log('Confidence score:', clockResult.confidence_score);
  }
}
```

### Face Management Admin Flow
```javascript
// 1. List all registered faces in hotel
const facesResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/list-faces/`, {
  headers: { 'Authorization': `Bearer ${adminToken}` }
});
const faces = await facesResponse.json();

// 2. Revoke a staff member's face data
const revokeResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/revoke-face/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    staff_id: 123,
    reason: 'Privacy request from staff member'
  })
});

// 3. View audit logs for compliance
const auditResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/face-management/audit-logs/?staff_id=123`, {
  headers: { 'Authorization': `Bearer ${adminToken}` }
});
const auditLogs = await auditResponse.json();
```

### Roster Management Flow
```javascript
// 1. Get roster periods
const periodsResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/periods/`);
const periods = await periodsResponse.json();

// 2. Get shifts for a period
const shiftsResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/shifts/?period=${periodId}`);
const shifts = await shiftsResponse.json();

// 3. Bulk save updated shifts
const bulkSaveResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/shifts/bulk-save/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    shifts: updatedShifts,
    period: periodId
  })
});
```

### Analytics Dashboard
```javascript
// Get KPIs for dashboard
const kpisResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/kpis/?start_date=2025-11-01&end_date=2025-11-30`);
const kpis = await kpisResponse.json();

// Get department breakdown
const deptSummaryResponse = await fetch(`/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/department-summary/?start_date=2025-11-01&end_date=2025-11-30`);
const departmentData = await deptSummaryResponse.json();
```

---

## 12. Best Practices

### Performance Optimization
- Use pagination for large datasets
- Filter by date ranges to reduce data transfer
- Cache frequently accessed data (locations, departments)
- Use bulk operations when possible

### Error Handling
- Always check response status codes
- Implement retry logic for network errors
- Show user-friendly error messages
- Log errors for debugging

### Security
- Never log or store authentication tokens
- Validate all user inputs on frontend
- Use HTTPS in production
- Implement proper session management

### UI/UX Considerations
- Show loading states during API calls
- Implement optimistic updates where appropriate
- Provide real-time feedback for clock-in/out actions
- Cache data for offline capability where possible

### Face Recognition Security
- **Privacy First**: Always obtain explicit consent before face registration
- **Data Minimization**: Face encoding vectors are never included in API responses
- **Audit Trail**: All face lifecycle events are logged with IP addresses and timestamps
- **Cloudinary Storage**: Face images stored securely in cloud, not locally
- **Revocation Rights**: Staff can request face data deletion at any time
- **Access Control**: Only hotel staff can access face management endpoints
- **Confidence Thresholds**: Configurable similarity thresholds prevent false matches

### Face Recognition Implementation Tips
```javascript
// Always handle face recognition errors gracefully
const handleFaceClockIn = async (imageData, encoding) => {
  try {
    const response = await faceClockIn(imageData, encoding);
    
    if (response.confidence_score > 0.7) {
      // Low confidence - ask user to try again
      showMessage('Face recognition confidence low. Please try again in better lighting.');
      return;
    }
    
    // Success
    showMessage(`${response.action === 'clock_in' ? 'Clocked in' : 'Clocked out'} successfully!`);
    
  } catch (error) {
    if (error.message.includes('Face not recognized')) {
      showMessage('Face not recognized. Please ensure you are registered.');
      // Redirect to registration flow
    } else {
      showMessage('Clock-in failed. Please try again or use manual entry.');
    }
  }
};

// Implement proper consent flow
const requestFaceRegistration = async () => {
  const consent = await showConsentDialog({
    title: 'Face Recognition Consent',
    message: 'Do you consent to storing your facial data for attendance tracking? You can revoke this consent at any time.',
    options: ['Accept', 'Decline']
  });
  
  if (consent === 'Accept') {
    return registerFace(imageData, encoding, true);
  }
  
  return null;
};
```

---

## 13. Face Recognition Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `FACE_NOT_RECOGNIZED` | No matching face found or confidence too low | Re-register face or use manual clock-in |
| `INVALID_IMAGE_FORMAT` | Image format not supported | Use JPEG, PNG, or WebP format |
| `IMAGE_TOO_LARGE` | Image exceeds 10MB limit | Compress image or reduce resolution |
| `INVALID_ENCODING` | Face encoding format invalid | Ensure 128-dimensional float array |
| `NO_FACE_REGISTERED` | User has no registered face data | Complete face registration first |
| `FACE_DATA_REVOKED` | Face data has been revoked | Re-register face data if desired |
| `CONSENT_REQUIRED` | Explicit consent needed for face processing | Obtain user consent before registration |
| `HOTEL_FACE_DISABLED` | Face attendance disabled for hotel | Contact administrator |

---

This documentation covers all attendance and roster-related endpoints in the HotelMate Backend system, including the comprehensive face recognition management system with Cloudinary integration, privacy controls, and audit trails. For questions or issues, please refer to the backend team or check the API error responses for detailed validation messages.