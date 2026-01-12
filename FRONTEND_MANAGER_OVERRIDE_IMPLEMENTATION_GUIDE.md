# Frontend Manager Override Implementation Guide

This guide shows how to implement manager override buttons in your housekeeping frontend to bypass room status transition restrictions.

## 🔐 API Endpoint

```
POST /api/staff/hotel/{hotel_slug}/housekeeping/rooms/{room_id}/manager_override/
```

**Authorization Required**: Manager-level staff or Django superuser

## 📝 Request Format

```json
{
  "to_status": "READY_FOR_GUEST",
  "note": "Maintenance completed - manager override"
}
```

**Parameters:**
- `to_status` (required): Target room status
- `note` (optional): Reason for override (defaults to "Manager override")

**Valid Status Values:**
- `OCCUPIED`
- `CHECKOUT_DIRTY`  
- `CLEANING_IN_PROGRESS`
- `CLEANED_UNINSPECTED`
- `MAINTENANCE_REQUIRED`
- `OUT_OF_ORDER`
- `READY_FOR_GUEST`

## ✅ Response Format

**Success (200):**
```json
{
  "message": "Manager override: Room 467 status changed to READY_FOR_GUEST",
  "room": {
    "id": 467,
    "room_number": "467",
    "room_status": "READY_FOR_GUEST",
    "last_cleaned_at": "2026-01-12T10:30:00Z",
    "last_inspected_at": "2026-01-12T11:00:00Z",
    "maintenance_required": false
  },
  "status_event": {
    "from_status": "MAINTENANCE_REQUIRED",
    "to_status": "READY_FOR_GUEST",
    "source": "MANAGER_OVERRIDE",
    "note": "Maintenance completed - manager override",
    "created_at": "2026-01-12T11:00:00Z"
  }
}
```

**Error (403):**
```json
{
  "error": "Manager privileges or superuser status required for override"
}
```

**Error (400):**
```json
{
  "error": "to_status is required"
}
```

## 🚀 Frontend Implementation Examples

### React Component with Manager Override Button

```jsx
import React, { useState } from 'react';

const RoomStatusCard = ({ room, user, onStatusUpdate }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  // Check if user can use manager override
  const canUseOverride = user.is_manager || user.is_superuser;
  
  const handleManagerOverride = async (toStatus, note = 'Manager override') => {
    if (!canUseOverride) {
      alert('Manager privileges required');
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/staff/hotel/${user.hotel_slug}/housekeeping/rooms/${room.id}/manager_override/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${user.token}`
          },
          body: JSON.stringify({
            to_status: toStatus,
            note: note
          })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        onStatusUpdate(data.room);
        alert(`✅ ${data.message}`);
      } else {
        const error = await response.json();
        alert(`❌ Error: ${error.error}`);
      }
    } catch (err) {
      alert(`❌ Network error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusActions = () => {
    const status = room.room_status;
    const actions = [];
    
    // Normal workflow buttons
    if (status === 'CHECKOUT_DIRTY') {
      actions.push({
        label: 'Start Cleaning',
        onClick: () => handleNormalStatusUpdate('CLEANING_IN_PROGRESS'),
        type: 'normal'
      });
    }
    
    if (status === 'CLEANED_UNINSPECTED') {
      actions.push({
        label: 'Mark Ready',
        onClick: () => handleNormalStatusUpdate('READY_FOR_GUEST'),
        type: 'normal'
      });
    }
    
    // Manager override buttons (always available for managers)
    if (canUseOverride) {
      actions.push({
        label: '🔓 Force Ready',
        onClick: () => handleManagerOverride('READY_FOR_GUEST', 'Room inspected and ready - manager override'),
        type: 'override',
        className: 'btn-override-ready'
      });
      
      if (status !== 'MAINTENANCE_REQUIRED') {
        actions.push({
          label: '🔧 Force Maintenance',
          onClick: () => handleManagerOverride('MAINTENANCE_REQUIRED', 'Emergency maintenance required'),
          type: 'override',
          className: 'btn-override-maintenance'
        });
      }
      
      if (status !== 'OUT_OF_ORDER') {
        actions.push({
          label: '🚫 Mark Out of Order',
          onClick: () => handleManagerOverride('OUT_OF_ORDER', 'Room temporarily out of service'),
          type: 'override',
          className: 'btn-override-ooo'
        });
      }
    }
    
    return actions;
  };

  return (
    <div className="room-status-card">
      <div className="room-header">
        <h4>Room {room.room_number}</h4>
        <span className={`status-badge ${room.room_status.toLowerCase()}`}>
          {room.room_status.replace('_', ' ')}
        </span>
      </div>
      
      <div className="room-actions">
        {getStatusActions().map((action, index) => (
          <button
            key={index}
            className={`btn ${action.className || ''} ${action.type === 'override' ? 'btn-override' : 'btn-normal'}`}
            onClick={action.onClick}
            disabled={isLoading}
          >
            {action.label}
          </button>
        ))}
      </div>
      
      {canUseOverride && (
        <div className="manager-note">
          <small>🔑 Manager Override Available</small>
        </div>
      )}
    </div>
  );
};
```

### Vue.js Implementation

```vue
<template>
  <div class="room-status-card">
    <div class="room-header">
      <h4>Room {{ room.room_number }}</h4>
      <span :class="['status-badge', room.room_status.toLowerCase()]">
        {{ room.room_status.replace('_', ' ') }}
      </span>
    </div>
    
    <div class="room-actions">
      <button 
        v-for="action in availableActions" 
        :key="action.label"
        :class="['btn', action.className, action.type === 'override' ? 'btn-override' : 'btn-normal']"
        @click="action.onClick"
        :disabled="isLoading"
      >
        {{ action.label }}
      </button>
    </div>
    
    <div v-if="canUseOverride" class="manager-note">
      <small>🔑 Manager Override Available</small>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RoomStatusCard',
  props: {
    room: Object,
    user: Object
  },
  data() {
    return {
      isLoading: false
    };
  },
  computed: {
    canUseOverride() {
      return this.user.is_manager || this.user.is_superuser;
    },
    availableActions() {
      const actions = [];
      const status = this.room.room_status;
      
      // Normal workflow buttons
      if (status === 'CHECKOUT_DIRTY') {
        actions.push({
          label: 'Start Cleaning',
          onClick: () => this.handleNormalStatusUpdate('CLEANING_IN_PROGRESS'),
          type: 'normal'
        });
      }
      
      // Manager override buttons
      if (this.canUseOverride) {
        actions.push({
          label: '🔓 Force Ready',
          onClick: () => this.handleManagerOverride('READY_FOR_GUEST', 'Manager override - room ready'),
          type: 'override',
          className: 'btn-override-ready'
        });
      }
      
      return actions;
    }
  },
  methods: {
    async handleManagerOverride(toStatus, note = 'Manager override') {
      if (!this.canUseOverride) {
        this.$toast.error('Manager privileges required');
        return;
      }
      
      this.isLoading = true;
      try {
        const response = await this.$http.post(
          `/api/staff/hotel/${this.user.hotel_slug}/housekeeping/rooms/${this.room.id}/manager_override/`,
          {
            to_status: toStatus,
            note: note
          }
        );
        
        this.$emit('status-updated', response.data.room);
        this.$toast.success(response.data.message);
      } catch (error) {
        this.$toast.error(`Error: ${error.response?.data?.error || error.message}`);
      } finally {
        this.isLoading = false;
      }
    }
  }
};
</script>
```

### Vanilla JavaScript Implementation

```javascript
class RoomManager {
  constructor(apiBaseUrl, authToken) {
    this.apiBaseUrl = apiBaseUrl;
    this.authToken = authToken;
  }

  async managerOverride(hotelSlug, roomId, toStatus, note = 'Manager override') {
    const response = await fetch(
      `${this.apiBaseUrl}/api/staff/hotel/${hotelSlug}/housekeeping/rooms/${roomId}/manager_override/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`
        },
        body: JSON.stringify({
          to_status: toStatus,
          note: note
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Unknown error');
    }

    return response.json();
  }

  createOverrideButton(room, user) {
    if (!user.is_manager && !user.is_superuser) {
      return null; // No override button for non-managers
    }

    const button = document.createElement('button');
    button.className = 'btn btn-override btn-override-ready';
    button.innerHTML = '🔓 Force Ready';
    button.onclick = async () => {
      if (confirm(`Force room ${room.room_number} to READY_FOR_GUEST status?`)) {
        try {
          const result = await this.managerOverride(
            user.hotel_slug,
            room.id,
            'READY_FOR_GUEST',
            'Room forced ready via manager override'
          );
          alert(`✅ ${result.message}`);
          location.reload(); // Refresh the page to show updated status
        } catch (error) {
          alert(`❌ Error: ${error.message}`);
        }
      }
    };

    return button;
  }
}

// Usage example
const roomManager = new RoomManager('https://your-api.com', userToken);

// Add override button to each room card
document.querySelectorAll('.room-card').forEach(card => {
  const roomId = card.dataset.roomId;
  const room = { id: roomId, room_number: card.dataset.roomNumber };
  const overrideButton = roomManager.createOverrideButton(room, currentUser);
  
  if (overrideButton) {
    card.querySelector('.room-actions').appendChild(overrideButton);
  }
});
```

## 🎨 CSS Styling Suggestions

```css
/* Manager Override Button Styles */
.btn-override {
  border: 2px solid #dc3545;
  background: linear-gradient(135deg, #dc3545, #c82333);
  color: white;
  font-weight: bold;
  position: relative;
}

.btn-override::before {
  content: '🔑';
  margin-right: 5px;
}

.btn-override:hover {
  background: linear-gradient(135deg, #c82333, #a71e2a);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
}

.btn-override-ready {
  background: linear-gradient(135deg, #28a745, #20c997);
  border-color: #28a745;
}

.btn-override-maintenance {
  background: linear-gradient(135deg, #ffc107, #fd7e14);
  border-color: #ffc107;
  color: #212529;
}

.btn-override-ooo {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  border-color: #6c757d;
}

.manager-note {
  margin-top: 8px;
  padding: 4px 8px;
  background: rgba(220, 53, 69, 0.1);
  border-radius: 4px;
  text-align: center;
}

.manager-note small {
  color: #dc3545;
  font-weight: 500;
}
```

## 🔄 Integration with Existing Workflow

### Strategy 1: Separate Override Section
```jsx
const RoomCard = ({ room, user }) => {
  return (
    <div className="room-card">
      {/* Normal workflow buttons */}
      <div className="normal-actions">
        <button>Start Cleaning</button>
        <button>Mark Cleaned</button>
      </div>
      
      {/* Manager override section */}
      {(user.is_manager || user.is_superuser) && (
        <div className="override-section">
          <hr />
          <h6>🔑 Manager Override</h6>
          <button className="btn-override">Force Ready</button>
          <button className="btn-override">Force Maintenance</button>
        </div>
      )}
    </div>
  );
};
```

### Strategy 2: Context Menu
```jsx
const RoomCard = ({ room, user }) => {
  const [showOverrideMenu, setShowOverrideMenu] = useState(false);
  
  return (
    <div className="room-card">
      <div className="room-actions">
        <button>Normal Action</button>
        
        {(user.is_manager || user.is_superuser) && (
          <div className="dropdown">
            <button 
              className="btn-override-menu"
              onClick={() => setShowOverrideMenu(!showOverrideMenu)}
            >
              🔑 Override ▼
            </button>
            
            {showOverrideMenu && (
              <div className="override-dropdown">
                <button onClick={() => handleOverride('READY_FOR_GUEST')}>
                  Force Ready
                </button>
                <button onClick={() => handleOverride('MAINTENANCE_REQUIRED')}>
                  Force Maintenance
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
```

## 🚨 Best Practices

### 1. **Confirmation Dialogs**
Always confirm manager overrides to prevent accidental changes:

```javascript
const handleManagerOverride = async (toStatus) => {
  const confirmed = confirm(
    `⚠️ Manager Override Warning\n\n` +
    `This will bypass normal workflow rules.\n` +
    `Change room ${room.room_number} to ${toStatus}?\n\n` +
    `This action will be logged in the audit trail.`
  );
  
  if (confirmed) {
    // Proceed with override
  }
};
```

### 2. **Visual Indicators**
Make override buttons clearly distinguishable:

```jsx
const OverrideButton = ({ onClick, children }) => (
  <button 
    className="btn-override"
    onClick={onClick}
    title="Manager Override - Bypasses workflow restrictions"
  >
    🔑 {children}
  </button>
);
```

### 3. **Error Handling**
Handle specific error cases:

```javascript
try {
  await managerOverride(roomId, 'READY_FOR_GUEST');
} catch (error) {
  if (error.message.includes('Manager privileges')) {
    showErrorModal('Access Denied', 'You need manager privileges to use override functionality.');
  } else if (error.message.includes('Invalid status')) {
    showErrorModal('Invalid Status', 'The requested status is not valid.');
  } else {
    showErrorModal('Error', `Unexpected error: ${error.message}`);
  }
}
```

### 4. **Audit Trail Visibility**
Show that overrides are logged:

```jsx
const OverrideConfirmation = ({ room, toStatus, onConfirm, onCancel }) => (
  <div className="override-modal">
    <h3>🔑 Manager Override Confirmation</h3>
    <p>Change Room {room.room_number} to <strong>{toStatus}</strong></p>
    <div className="warning">
      ⚠️ This will bypass normal workflow rules and will be logged in the audit trail.
    </div>
    <div className="actions">
      <button onClick={onConfirm} className="btn-danger">Confirm Override</button>
      <button onClick={onCancel} className="btn-secondary">Cancel</button>
    </div>
  </div>
);
```

## 📊 Real-Time Updates

If you're using WebSockets or Server-Sent Events, make sure to handle manager override events:

```javascript
// WebSocket event handling
websocket.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'room_status_changed') {
    const { room_id, new_status, source } = data;
    
    // Update UI
    updateRoomStatus(room_id, new_status);
    
    // Show notification for manager overrides
    if (source === 'MANAGER_OVERRIDE') {
      showNotification(`🔑 Manager Override: Room ${data.room_number} → ${new_status}`, 'warning');
    }
  }
});
```

This guide provides everything you need to implement manager override functionality in your housekeeping frontend!