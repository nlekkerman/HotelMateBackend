# HotelMate Roster System - Complete Guide

## Overview
The HotelMate roster system provides secure staff scheduling with creation, copying, and management capabilities. This guide covers all roster operations, security improvements, and frontend integration.

## 🔒 Security Enhancements (Recently Implemented)

### Critical Fixes Applied
- **Transaction Safety**: All operations use atomic transactions with duplicate prevention
- **Permission Security**: Hotel-specific staff member validation
- **Data Integrity**: Overlap detection and business rule validation
- **Audit Logging**: Complete tracking of all roster modifications
- **Rate Limiting**: Protection against abuse and performance issues

---

## 📋 Core Roster Models

### 1. RosterPeriod
Defines scheduling periods (typically weekly).
```python
{
  "id": 1,
  "hotel": "hotel-killarney",
  "title": "Week 48 Roster",
  "start_date": "2025-11-24",
  "end_date": "2025-11-30",
  "published": false
}
```

### 2. StaffRoster
Individual staff shifts within periods.
```python
{
  "id": 123,
  "staff": 15,
  "hotel": "hotel-killarney",
  "period": 1,
  "shift_date": "2025-11-25",
  "shift_start": "09:00",
  "shift_end": "17:00",
  "department": "housekeeping",
  "location": 2,
  "expected_hours": 8.0,
  "is_split_shift": false
}
```

### 3. RosterAuditLog (New)
Tracks all roster modifications for accountability.
```python
{
  "id": 1,
  "hotel": "hotel-killarney", 
  "performed_by": "john-manager",
  "operation_type": "copy_bulk",
  "affected_shifts_count": 45,
  "source_period": 1,
  "target_period": 2,
  "success": true,
  "timestamp": "2025-11-29T14:30:00Z"
}
```

---

## 🔐 Authentication & Permissions

### Required Headers
```javascript
{
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
}
```

### Permission Requirements
1. **IsAuthenticated** - Valid JWT token required
2. **IsStaffMember** - User must have `staff_profile`
3. **IsSameHotel** - Staff must belong to hotel in URL

### Error Responses
```javascript
// 401 - Unauthorized
{ "detail": "Authentication credentials were not provided." }

// 403 - Forbidden
{ "detail": "You don't have access to this hotel" }
```

---

## 📅 Roster Creation APIs

### 1. Create Individual Shift
**Endpoint:** `POST /api/attendance/{hotel_slug}/shifts/`

**Request:**
```json
{
  "staff": 15,
  "period": 1,
  "shift_date": "2025-11-25",
  "shift_start": "09:00",
  "shift_end": "17:00", 
  "department": "housekeeping",
  "location": 2
}
```

**Response:**
```json
{
  "id": 123,
  "staff_name": "John Doe",
  "period_title": "Week 48 Roster",
  "department_name": "Housekeeping",
  "expected_hours": 8.0,
  // ... full shift data
}
```

### 2. Bulk Save Shifts
**Endpoint:** `POST /api/attendance/{hotel_slug}/shifts/bulk-save/`

**Features:**
- ✅ Overlap detection
- ✅ Duplicate prevention  
- ✅ Split shift marking
- ✅ Transaction safety

**Request:**
```json
{
  "hotel": "hotel-killarney",
  "period": 1,
  "shifts": [
    {
      "staff": 15,
      "shift_date": "2025-11-25",
      "shift_start": "09:00",
      "shift_end": "17:00",
      "department": "housekeeping"
    },
    {
      "staff": 16, 
      "shift_date": "2025-11-25",
      "shift_start": "14:00",
      "shift_end": "22:00",
      "department": "reception"
    }
  ]
}
```

**Response:**
```json
{
  "created": [/* new shifts */],
  "updated": [/* modified shifts */],
  "errors": []
}
```

### 3. Create Department Roster
**Endpoint:** `POST /api/attendance/{hotel_slug}/periods/{id}/create-department-roster/`

**Request:**
```json
{
  "department": "housekeeping",
  "shifts": [
    {
      "staff": 15,
      "shift_date": "2025-11-25",
      "shift_start": "09:00", 
      "shift_end": "17:00"
    }
  ]
}
```

---

## 📋 Roster Copying APIs

### 1. Copy Entire Period (Bulk)
**Endpoint:** `POST /api/attendance/{hotel_slug}/shift-copy/copy-roster-bulk/`

**Features:**
- ✅ Rate limited (10 ops/hour, max 500 shifts)
- ✅ Published period protection
- ✅ Hotel validation
- ✅ Audit logging

**Request:**
```json
{
  "source_period_id": 1,
  "target_period_id": 2
}
```

**Success Response:**
```json
{
  "copied_shifts_count": 45,
  "actual_created_count": 42
}
```

**Error Responses:**
```json
// Rate limit exceeded
{
  "detail": "Rate limit exceeded. Maximum 10 copy operations per hour.",
  "status": 429
}

// Operation too large
{
  "detail": "Operation too large. Bulk period copy would copy 750 shifts. Maximum allowed: 500. Please use smaller date ranges.",
  "status": 400
}

// Published period
{
  "detail": "Cannot copy shifts to a published period.",
  "status": 400
}

// Overlap detection
{
  "detail": "Copying would create overlapping shifts. Operation cancelled.", 
  "status": 400
}
```

### 2. Copy Single Day (All Staff)
**Endpoint:** `POST /api/attendance/{hotel_slug}/shift-copy/copy-roster-day-all/`

**Request:**
```json
{
  "source_date": "2025-11-25",
  "target_date": "2025-12-02"
}
```

### 3. Copy Staff Member (Week)
**Endpoint:** `POST /api/attendance/{hotel_slug}/shift-copy/copy-week-staff/`

**Request:**
```json
{
  "staff_id": 15,
  "source_period_id": 1, 
  "target_period_id": 2
}
```

---

## 📊 Roster Analytics & Reports

### 1. Period Management
**Endpoints:**
- `GET /api/attendance/{hotel_slug}/periods/` - List periods
- `POST /api/attendance/{hotel_slug}/periods/` - Create period
- `GET /api/attendance/{hotel_slug}/periods/{id}/` - Period details

### 2. PDF Reports
**Endpoints:**
- `GET /api/attendance/{hotel_slug}/shifts/daily-pdf/?date=2025-11-25`
- `GET /api/attendance/{hotel_slug}/shifts/staff-pdf/?staff_id=15&start_date=2025-11-25`
- `GET /api/attendance/{hotel_slug}/periods/{id}/export-pdf/`

---

## 🔧 Frontend Integration Examples

### React Hook for Roster Operations
```javascript
import { useState } from 'react';

export const useRoster = (hotelSlug) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const copyRosterBulk = async (sourceId, targetId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/attendance/${hotelSlug}/shift-copy/copy-roster-bulk/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            source_period_id: sourceId,
            target_period_id: targetId
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        
        // Handle specific errors
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait before copying again.');
        }
        
        throw new Error(errorData.detail || 'Copy operation failed');
      }

      const result = await response.json();
      return result;
      
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createShift = async (shiftData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/attendance/${hotelSlug}/shifts/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(shiftData)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create shift');
      }

      return await response.json();
      
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const bulkSaveShifts = async (shiftsData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/attendance/${hotelSlug}/shifts/bulk-save/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(shiftsData)
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.errors?.[0] || 'Bulk save failed');
      }

      return await response.json();
      
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    copyRosterBulk,
    createShift,
    bulkSaveShifts,
    loading,
    error
  };
};
```

### Copy Roster Component
```javascript
import React, { useState } from 'react';
import { useRoster } from './hooks/useRoster';

export const RosterCopyModal = ({ hotelSlug, periods, onSuccess, onClose }) => {
  const [sourceId, setSourceId] = useState('');
  const [targetId, setTargetId] = useState('');
  const { copyRosterBulk, loading, error } = useRoster(hotelSlug);

  const handleCopy = async () => {
    try {
      const result = await copyRosterBulk(sourceId, targetId);
      
      // Show success message
      alert(`Successfully copied ${result.actual_created_count} shifts!`);
      
      onSuccess();
      onClose();
      
    } catch (err) {
      // Error is already set in hook
      console.error('Copy failed:', err.message);
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Copy Roster</h2>
        
        <div className="form-group">
          <label>Source Period:</label>
          <select 
            value={sourceId} 
            onChange={(e) => setSourceId(e.target.value)}
          >
            <option value="">Select source period...</option>
            {periods.map(period => (
              <option key={period.id} value={period.id}>
                {period.title} ({period.start_date} - {period.end_date})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Target Period:</label>
          <select 
            value={targetId} 
            onChange={(e) => setTargetId(e.target.value)}
          >
            <option value="">Select target period...</option>
            {periods
              .filter(p => p.id !== sourceId && !p.published)
              .map(period => (
                <option key={period.id} value={period.id}>
                  {period.title} ({period.start_date} - {period.end_date})
                </option>
              ))
            }
          </select>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="modal-actions">
          <button onClick={onClose} disabled={loading}>
            Cancel
          </button>
          <button 
            onClick={handleCopy} 
            disabled={loading || !sourceId || !targetId}
          >
            {loading ? 'Copying...' : 'Copy Roster'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

## ⚠️ Important Constraints & Limits

### Rate Limiting
- **10 copy operations per hour** per user
- **500 shifts maximum** per copy operation
- Rate limits reset every hour

### Business Rules
- Cannot copy to **published periods**
- Source and target periods must belong to **same hotel**
- **No overlapping shifts** allowed (except adjacent or ending before 04:00)
- **Duplicate shifts** are automatically prevented

### Data Integrity
- All operations use **atomic transactions**
- **Audit logging** tracks every modification
- **Permission validation** on every request
- **Overlap detection** prevents scheduling conflicts

---

## 🐛 Error Handling Best Practices

### Frontend Error Display
```javascript
const handleRosterError = (error, operation) => {
  const errorMessages = {
    429: 'You have reached the hourly limit for copy operations. Please try again later.',
    400: error.detail || 'Invalid request. Please check your selections.',
    403: 'You do not have permission to perform this action.',
    404: 'Requested resource not found.',
    500: 'Server error occurred. Please try again or contact support.'
  };

  const message = errorMessages[error.status] || 'An unexpected error occurred.';
  
  // Show user-friendly error
  showNotification({
    type: 'error',
    title: `${operation} Failed`,
    message: message,
    duration: 5000
  });
};
```

### Validation Before API Calls
```javascript
const validateCopyOperation = (sourceId, targetId, periods) => {
  const sourcePeriod = periods.find(p => p.id === sourceId);
  const targetPeriod = periods.find(p => p.id === targetId);

  if (!sourcePeriod || !targetPeriod) {
    throw new Error('Please select both source and target periods');
  }

  if (targetPeriod.published) {
    throw new Error('Cannot copy to a published period');
  }

  if (sourceId === targetId) {
    throw new Error('Source and target periods must be different');
  }

  return true;
};
```

---

## 📈 Performance Considerations

### Optimization Tips
1. **Use bulk operations** instead of individual shift creation
2. **Implement pagination** for large roster lists  
3. **Cache period data** to reduce API calls
4. **Show loading states** during copy operations
5. **Debounce search/filter inputs**

### Monitoring
- Track copy operation success rates
- Monitor API response times
- Watch for rate limit hits
- Audit log analysis for usage patterns

---

## 🔄 Migration & Deployment Notes

### Database Changes Applied
```sql
-- New audit log model
CREATE TABLE attendance_rosterauditlog (
    id BIGSERIAL PRIMARY KEY,
    hotel_id BIGINT NOT NULL,
    performed_by_id BIGINT,
    operation_type VARCHAR(20) NOT NULL,
    affected_shifts_count INTEGER NOT NULL DEFAULT 0,
    -- ... additional fields
);

-- Indexes for performance
CREATE INDEX attendance_rosterauditlog_hotel_operation ON attendance_rosterauditlog(hotel_id, operation_type);
CREATE INDEX attendance_rosterauditlog_performed_by_timestamp ON attendance_rosterauditlog(performed_by_id, timestamp);
```

### Security Improvements
- ✅ Transaction safety prevents race conditions
- ✅ Permission validation prevents unauthorized access
- ✅ Rate limiting prevents abuse
- ✅ Audit logging provides accountability
- ✅ Data integrity checks prevent corruption

The roster system is now production-ready with enterprise-grade security and reliability.