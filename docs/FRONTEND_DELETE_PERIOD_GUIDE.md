# Frontend Guide: Delete Period (Superuser Only)

## Overview
This guide explains how to implement the DELETE period functionality in the frontend. This feature allows **superusers only** to delete a period and all its related data.

---

## 🚨 **What Gets Deleted**

When a period is deleted, the following are **permanently removed**:

1. ✅ **The Period** itself
2. ✅ **All Stocktakes** for this period (matched by dates)
3. ✅ **All StocktakeLine** records (cascaded from stocktakes)
4. ✅ **All StockSnapshot** records (cascaded from period)

**Example:**
```
Deleting "November 2025" period removes:
- Period record
- 1 Stocktake (Nov 1-30)
- 254 Stocktake Lines
- 254 Stock Snapshots
```

---

## 🔒 **Permission Requirements**

### **Backend Permission Check:**
- Only users with `is_superuser = true` can delete periods
- Non-superusers receive `403 Forbidden` error

### **Frontend Permission Check:**
```javascript
// Check if user is superuser
const canDeletePeriod = user?.is_superuser === true;

// Show delete button only for superusers
{canDeletePeriod && (
  <button 
    onClick={() => handleDeletePeriod(period.id)}
    className="btn-danger"
  >
    🗑️ Delete Period
  </button>
)}
```

---

## 📡 **API Endpoint**

### **DELETE Period:**
```http
DELETE /api/stock-tracker/{hotel_identifier}/periods/{period_id}/
```

### **Request Headers:**
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

### **Success Response (200 OK):**
```json
{
  "message": "Period 'November 2025' and all related data deleted successfully",
  "deleted": {
    "period": 1,
    "stocktakes": 1,
    "stocktake_lines": 254,
    "snapshots": 254
  }
}
```

### **Error Response (403 Forbidden):**
```json
{
  "error": "Only superusers can delete periods"
}
```

### **Error Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

## 🎨 **Frontend UI Implementation**

### **1. Delete Button (Only for Superusers)**

Add delete button next to each period in the list:

```jsx
import React, { useState } from 'react';

const PeriodListItem = ({ period, user, onDelete }) => {
  const [isDeleting, setIsDeleting] = useState(false);
  
  return (
    <div className="period-item">
      <div className="period-info">
        <h3>{period.period_name}</h3>
        <p>{period.start_date} to {period.end_date}</p>
        <span className={`badge ${period.is_closed ? 'closed' : 'open'}`}>
          {period.is_closed ? 'Closed' : 'Open'}
        </span>
      </div>
      
      <div className="period-actions">
        <button onClick={() => viewPeriod(period.id)}>
          View Details
        </button>
        
        {/* Delete button - only for superusers */}
        {user?.is_superuser && (
          <button
            onClick={() => onDelete(period)}
            disabled={isDeleting}
            className="btn-danger"
          >
            {isDeleting ? 'Deleting...' : '🗑️ Delete'}
          </button>
        )}
      </div>
    </div>
  );
};
```

---

### **2. Confirmation Modal**

Show a confirmation dialog before deleting:

```jsx
const ConfirmDeleteModal = ({ period, onConfirm, onCancel }) => {
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>⚠️ Delete Period and All Data?</h2>
        
        <div className="warning-box">
          <p><strong>This will permanently delete:</strong></p>
          <ul>
            <li>Period: <strong>{period.period_name}</strong></li>
            <li>All stocktakes for this period</li>
            <li>All stocktake lines (250+ items)</li>
            <li>All stock snapshots</li>
          </ul>
          
          <p className="text-danger">
            <strong>⚠️ This action CANNOT be undone!</strong>
          </p>
        </div>
        
        <div className="modal-actions">
          <button onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
          <button onClick={onConfirm} className="btn-danger">
            ⚠️ DELETE PERMANENTLY
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

### **3. Delete Handler Function**

```javascript
import axios from 'axios';

const deletePeriod = async (period) => {
  // Step 1: Show confirmation modal
  const confirmed = window.confirm(
    `⚠️ DELETE PERIOD AND ALL DATA?\n\n` +
    `This will permanently delete:\n` +
    `- Period: ${period.period_name}\n` +
    `- All Stocktakes\n` +
    `- All Stocktake Lines\n` +
    `- All Stock Snapshots\n\n` +
    `This action CANNOT be undone!\n\n` +
    `Type "DELETE" to confirm.`
  );
  
  if (!confirmed) {
    console.log('Delete cancelled by user');
    return;
  }
  
  // Step 2: Log deletion attempt
  console.log('🗑️ Deleting period:', {
    period_id: period.id,
    period_name: period.period_name,
    user_is_superuser: user.is_superuser
  });
  
  try {
    // Step 3: Call DELETE API
    const response = await axios.delete(
      `/api/stock-tracker/${hotelSlug}/periods/${period.id}/`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    // Step 4: Log success
    console.log('✅ Period deleted successfully:', {
      message: response.data.message,
      deleted: response.data.deleted
    });
    
    // Step 5: Show success message
    alert(
      `✅ Successfully deleted!\n\n` +
      `${response.data.message}\n\n` +
      `Deleted items:\n` +
      `- Periods: ${response.data.deleted.period}\n` +
      `- Stocktakes: ${response.data.deleted.stocktakes}\n` +
      `- Lines: ${response.data.deleted.stocktake_lines}\n` +
      `- Snapshots: ${response.data.deleted.snapshots}`
    );
    
    // Step 6: Refresh period list
    await fetchPeriods();
    
  } catch (error) {
    // Handle errors
    console.error('❌ Delete failed:', {
      status: error.response?.status,
      message: error.response?.data?.error || error.message,
      period_id: period.id
    });
    
    if (error.response?.status === 403) {
      alert('❌ Permission Denied\n\nOnly superusers can delete periods.');
    } else if (error.response?.status === 404) {
      alert('❌ Period Not Found\n\nThis period may have already been deleted.');
    } else {
      alert('❌ Delete Failed\n\nAn error occurred while deleting the period. Please try again.');
    }
  }
};
```

---

## 🔍 **Console Logging for Debugging**

### **Log Delete Attempt:**
```javascript
console.log('🗑️ Attempting to delete period:', {
  period_id: period.id,
  period_name: period.period_name,
  start_date: period.start_date,
  end_date: period.end_date,
  is_closed: period.is_closed,
  user_is_superuser: user.is_superuser
});
```

### **Log Delete Success:**
```javascript
console.log('✅ Period deleted successfully:', {
  message: response.data.message,
  deleted_counts: {
    periods: response.data.deleted.period,
    stocktakes: response.data.deleted.stocktakes,
    lines: response.data.deleted.stocktake_lines,
    snapshots: response.data.deleted.snapshots
  },
  timestamp: new Date().toISOString()
});
```

### **Log Permission Error:**
```javascript
console.error('❌ Permission denied:', {
  status: 403,
  error: 'Only superusers can delete periods',
  user_is_superuser: user.is_superuser,
  user_role: user.role
});
```

### **Log Not Found Error:**
```javascript
console.error('❌ Period not found:', {
  status: 404,
  period_id: period.id,
  error: 'Period may have already been deleted'
});
```

---

## ✅ **Complete React Component Example**

```jsx
import React, { useState } from 'react';
import axios from 'axios';

const PeriodsList = ({ hotelSlug, user, accessToken }) => {
  const [periods, setPeriods] = useState([]);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [periodToDelete, setPeriodToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Fetch periods
  const fetchPeriods = async () => {
    const response = await axios.get(
      `/api/stock-tracker/${hotelSlug}/periods/`
    );
    setPeriods(response.data);
  };
  
  // Handle delete click
  const handleDeleteClick = (period) => {
    setPeriodToDelete(period);
    setShowDeleteModal(true);
  };
  
  // Confirm delete
  const confirmDelete = async () => {
    setIsDeleting(true);
    
    console.log('🗑️ Deleting period:', {
      period_id: periodToDelete.id,
      period_name: periodToDelete.period_name
    });
    
    try {
      const response = await axios.delete(
        `/api/stock-tracker/${hotelSlug}/periods/${periodToDelete.id}/`,
        {
          headers: { 'Authorization': `Bearer ${accessToken}` }
        }
      );
      
      console.log('✅ Deleted:', response.data);
      
      alert(`✅ ${response.data.message}`);
      
      // Refresh list
      await fetchPeriods();
      
      // Close modal
      setShowDeleteModal(false);
      setPeriodToDelete(null);
      
    } catch (error) {
      console.error('❌ Delete failed:', error);
      
      if (error.response?.status === 403) {
        alert('Only superusers can delete periods');
      } else {
        alert('Failed to delete period');
      }
    } finally {
      setIsDeleting(false);
    }
  };
  
  return (
    <div className="periods-list">
      <h2>Stock Periods</h2>
      
      {periods.map(period => (
        <div key={period.id} className="period-card">
          <h3>{period.period_name}</h3>
          <p>{period.start_date} to {period.end_date}</p>
          
          <div className="actions">
            <button onClick={() => viewDetails(period.id)}>
              View Details
            </button>
            
            {/* Delete button - only for superusers */}
            {user?.is_superuser && (
              <button
                onClick={() => handleDeleteClick(period)}
                className="btn-danger"
              >
                🗑️ Delete
              </button>
            )}
          </div>
        </div>
      ))}
      
      {/* Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>⚠️ Delete Period?</h2>
            <p>
              This will permanently delete <strong>{periodToDelete.period_name}</strong> 
              and all related data (stocktakes, lines, snapshots).
            </p>
            <p className="warning">This cannot be undone!</p>
            
            <div className="modal-actions">
              <button 
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button 
                onClick={confirmDelete}
                disabled={isDeleting}
                className="btn-danger"
              >
                {isDeleting ? 'Deleting...' : '⚠️ DELETE'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PeriodsList;
```

---

## 🎨 **CSS Styling Example**

```css
/* Delete button */
.btn-danger {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-danger:hover {
  background-color: #c82333;
}

.btn-danger:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
}

.warning {
  color: #dc3545;
  font-weight: bold;
  margin: 16px 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}
```

---

## ⚠️ **Important Notes**

### **1. Cascade Delete is Automatic**
- Backend handles all cascade deletions
- No need to delete stocktakes/lines/snapshots separately
- Database constraints ensure data integrity

### **2. Permission Check on Backend**
- Backend validates `is_superuser` before deletion
- Frontend UI check is for UX only (not security)
- Always expect 403 errors from non-superusers

### **3. Cannot Undo**
- Deletion is permanent
- No soft-delete or trash bin
- Always show strong confirmation dialogs

### **4. What Happens to Related Data:**
```
Period (deleted) 
  ↓
Stocktakes (cascade deleted)
  ↓
StocktakeLine (cascade deleted)

Period (deleted)
  ↓
StockSnapshot (cascade deleted)
```

### **5. When to Use:**
- ❌ Wrong period dates created
- ❌ Duplicate period by mistake
- ❌ Test data cleanup
- ❌ Corrupted stocktake data

### **6. When NOT to Use:**
- ✅ Period is closed and has valid data
- ✅ Period is referenced in reports
- ✅ Historical data needed for audits

---

## 🔍 **Testing the Feature**

### **Test Case 1: Superuser Can Delete**
```javascript
// User: is_superuser = true
// Expected: 200 OK, period deleted

test('superuser can delete period', async () => {
  const response = await deletePeriod(periodId);
  expect(response.status).toBe(200);
  expect(response.data.deleted.period).toBe(1);
});
```

### **Test Case 2: Non-superuser Cannot Delete**
```javascript
// User: is_superuser = false
// Expected: 403 Forbidden

test('non-superuser cannot delete period', async () => {
  try {
    await deletePeriod(periodId);
    fail('Should have thrown 403 error');
  } catch (error) {
    expect(error.response.status).toBe(403);
    expect(error.response.data.error).toContain('superuser');
  }
});
```

### **Test Case 3: Period Not Found**
```javascript
// Period ID: 99999 (doesn't exist)
// Expected: 404 Not Found

test('returns 404 for non-existent period', async () => {
  try {
    await deletePeriod(99999);
    fail('Should have thrown 404 error');
  } catch (error) {
    expect(error.response.status).toBe(404);
  }
});
```

---

## 📊 **Expected Console Output**

### **Successful Delete:**
```
🗑️ Deleting period: { period_id: 19, period_name: "November 2025" }
🌐 API Request: { method: "DELETE", url: "/api/stock-tracker/hotel1/periods/19/" }
✅ API Response: { status: 200, data: { message: "...", deleted: {...} } }
✅ Period deleted successfully: {
  message: "Period 'November 2025' and all related data deleted successfully",
  deleted_counts: {
    periods: 1,
    stocktakes: 1,
    lines: 254,
    snapshots: 254
  }
}
```

### **Permission Denied:**
```
🗑️ Deleting period: { period_id: 19, period_name: "November 2025" }
🌐 API Request: { method: "DELETE", url: "/api/stock-tracker/hotel1/periods/19/" }
❌ API Error: { status: 403, error: "Only superusers can delete periods" }
❌ Permission denied: {
  status: 403,
  user_is_superuser: false,
  error: "Only superusers can delete periods"
}
```

---

## ✅ **Summary**

1. **Only superusers** can delete periods
2. **Deletes cascaded data**: stocktakes, lines, snapshots
3. **Always show confirmation** before deleting
4. **Log all delete attempts** for auditing
5. **Handle 403/404 errors** gracefully
6. **Refresh period list** after successful delete

---

*For questions, contact backend team or check the main stocktake guide.*
