# 🚀 Frontend Team: GitHub Issues Creation Guide

## 🎯 **OBJECTIVE**
Create comprehensive GitHub issues in your **frontend repository** to match the backend implementation work and track frontend integration tasks.

## 📋 **BACKEND ISSUES COMPLETED** ✅
**Repository**: `nlekkerman/HotelMateBackend`  
**Issues Created & Closed**: #55-59

1. **#55** - Staff Chat Unread Count System Implementation
2. **#56** - FCM Chat Implementation & Event Transformation  
3. **#57** - NotificationManager Architecture & Unified Events
4. **#58** - Auto Clock-Out Management System for Heroku Scheduler
5. **#59** - Staff Chat Real-time Updates & Pusher Migration

---

## 🎯 **FRONTEND TEAM TASKS**

### **Step 1: Create Frontend Integration Issues**

Create **corresponding frontend issues** in your frontend repository to track integration of these backend features:

#### **Issue 1: Staff Chat Unread Count Frontend Integration**
```markdown
## 🎯 User Story
**As a staff member**, I want **real-time unread count badges in the UI**, so that **I can see unread messages at a glance and prioritize my communication**.

## 📝 Context
Integrate the backend Staff Chat Unread Count System (#55 in backend) with frontend real-time UI updates, badges, and notifications.

## ✅ Acceptance Criteria
- [ ] Subscribe to staff personal notification channels: `hotel-{slug}.staff-{id}-notifications`
- [ ] Handle `unread_updated` events with conversation-specific and total counts
- [ ] Update conversation list badges in real-time
- [ ] Update navigation bar total unread badge
- [ ] Implement badge animations (bounce, pulse) for new unreads
- [ ] Auto-mark conversations as read when opened
- [ ] Update document title with unread count
- [ ] Add sound notifications for new messages

## 🔧 Technical Implementation

### Backend Integration
- **Event Channel**: `hotel-{slug}.staff-{id}-notifications`
- **Event Type**: `unread_updated` 
- **Payload Structure**:
```json
{
  "category": "staff_chat",
  "type": "unread_updated",
  "payload": {
    "staff_id": 123,
    "conversation_id": 456,     // null for total count
    "unread_count": 3,          // count for this conversation
    "total_unread": 15,         // null for specific conversation updates
    "updated_at": "2025-12-08T10:30:00Z"
  }
}
```

### Frontend Tasks
- [ ] Update eventBus to handle `unread_updated` events
- [ ] Create badge components with animation support
- [ ] Implement conversation sorting by unread status
- [ ] Add CSS animations for badge updates
- [ ] Update chat list components
- [ ] Add navigation badge updates
- [ ] Implement sound notification system

## 📚 Backend Documentation Reference
- `STAFF_CHAT_UNREAD_COUNT_GUIDE.md` - Complete frontend integration guide
- Backend Issue: nlekkerman/HotelMateBackend#55

---

**Priority**: High  
**Backend Status**: ✅ Complete  
**Frontend Status**: 🔄 Integration Needed
```

#### **Issue 2: FCM Chat Features Frontend Integration**
```markdown
## 🎯 User Story
**As a user**, I want **FCM notifications to integrate seamlessly with the chat interface**, so that **I can receive and interact with messages across all platforms**.

## 📝 Context
Integrate FCM Chat Implementation & Event Transformation (backend #56) with frontend chat interface, including read receipts, replies, and deep linking.

## ✅ Acceptance Criteria
- [ ] Implement FCM event transformation layer for eventBus compatibility
- [ ] Add read receipt indicators to messages
- [ ] Implement reply functionality with threading UI
- [ ] Handle FCM notification clicks for deep linking
- [ ] Auto-mark messages as read on navigation
- [ ] Add file attachment support (50MB limit)
- [ ] Implement message status indicators (delivered, read)
- [ ] Create Vue.js and React chat components

## 🔧 Technical Implementation

### FCM Integration
```javascript
// Transform FCM events to eventBus format
function transformFCMEvent(fcmEvent) {
  const eventMapping = {
    'new_chat_message': {
      category: 'guest_chat',
      type: 'staff_message_created',
      channel: `hotel-${hotelSlug}.guest-chat.${roomNumber}`
    },
    'staff_chat_message': {
      category: 'staff_chat',
      type: 'message_created',
      channel: `hotel-${hotelSlug}.staff-chat.${conversationId}`
    }
  };
  return transformedEvent;
}
```

### API Endpoints to Implement
- `POST /api/chat/conversations/{id}/mark-read/` - Mark guest chat read
- `POST /api/staff-chat/{hotel_slug}/conversations/{id}/mark_as_read/` - Mark staff chat read
- `POST /api/staff-chat/{hotel_slug}/conversations/{id}/messages/` - Send replies
- File attachment endpoints with CloudinaryField support

## 📚 Backend Documentation Reference
- `FCM_CHAT_IMPLEMENTATION_GUIDE.md` - 670-line complete implementation guide
- Backend Issue: nlekkerman/HotelMateBackend#56

---

**Priority**: High  
**Backend Status**: ✅ Complete  
**Frontend Status**: 🔄 Integration Needed
```

#### **Issue 3: Unified Real-time Events Frontend Integration**
```markdown
## 🎯 User Story
**As a developer**, I want **consistent event handling across all domains**, so that **real-time features work reliably and maintainably**.

## 📝 Context
Integrate the unified NotificationManager architecture (backend #57) with frontend eventBus system for consistent real-time event handling across all 5 domains.

## ✅ Acceptance Criteria
- [ ] Update eventBus to handle unified event structure
- [ ] Migrate from hyphenated events (`message-created`) to underscore (`message_created`)
- [ ] Implement domain-specific event handlers (staff_chat, guest_chat, attendance, booking, room_service)
- [ ] Add consistent error handling for all real-time events
- [ ] Create event logging and debugging tools
- [ ] Update all existing event subscriptions
- [ ] Test cross-domain event compatibility

## 🔧 Technical Implementation

### Event Structure Migration
**Old Format (Deprecated)**:
```javascript
channel.bind('message-created', function(data) { ... });
```

**New Format (Unified)**:
```javascript
eventBus.subscribe('hotel-slug.staff-chat.conversation-id', (event) => {
  if (event.type === 'message_created') { ... }
});
```

### Domain Coverage
1. **Staff Chat**: Message operations, unread counts, attachments
2. **Guest Chat**: Message delivery, read receipts
3. **Attendance**: Clock status, duty updates, auto clock-out
4. **Booking**: Confirmations, cancellations, updates  
5. **Room Service**: Order notifications, status updates

## 📚 Backend Documentation Reference
- Backend Issue: nlekkerman/HotelMateBackend#57
- NotificationManager documentation in backend

---

**Priority**: Critical  
**Backend Status**: ✅ Complete  
**Frontend Status**: 🔄 Architecture Update Needed
```

#### **Issue 4: Auto Clock-Out UI Integration**
```markdown
## 🎯 User Story
**As a staff member**, I want **to see warnings before auto clock-out**, so that **I can acknowledge long sessions or clock out manually**.

## 📝 Context
Integrate Auto Clock-Out Management System (backend #58) with frontend UI for warnings, notifications, and status displays.

## ✅ Acceptance Criteria
- [ ] Display progressive warning notifications (12h, 16h, 20h)
- [ ] Show auto clock-out notifications when they occur
- [ ] Update staff status immediately when auto clocked out
- [ ] Add acknowledgment buttons for long sessions
- [ ] Implement warning countdown timers
- [ ] Show clock session duration in real-time
- [ ] Add manual clock-out option with warnings

## 🔧 Technical Implementation

### Real-time Events
- **Channel**: `hotel-{slug}.attendance`
- **Events**: `clock_status_updated`, `long_session_warning`
- **Personal Channel**: `hotel-{slug}.staff-{id}-notifications`

### Warning System
```javascript
// Handle progressive warnings
eventBus.subscribe('hotel-slug.staff-id-notifications', (event) => {
  if (event.type === 'long_session_warning') {
    showWarningModal(event.payload.warning_type, event.payload.duration);
  }
});
```

## 📚 Backend Documentation Reference
- Backend Issue: nlekkerman/HotelMateBackend#58
- Heroku scheduler runs every 30 minutes

---

**Priority**: Medium  
**Backend Status**: ✅ Complete  
**Frontend Status**: 🔄 UI Integration Needed
```

### **Step 2: Create the Issues Script**

Create a similar script for your frontend repository:

```javascript
// create_frontend_integration_issues.js
const { exec } = require('child_process');

const issues = [
  {
    title: "Staff Chat Unread Count Frontend Integration",
    body: `[Issue 1 content from above]`,
    labels: ["integration", "staff-chat", "real-time", "high-priority"]
  },
  {
    title: "FCM Chat Features Frontend Integration", 
    body: `[Issue 2 content from above]`,
    labels: ["integration", "fcm", "chat", "high-priority"]
  },
  {
    title: "Unified Real-time Events Frontend Integration",
    body: `[Issue 3 content from above]`, 
    labels: ["architecture", "real-time", "critical", "eventbus"]
  },
  {
    title: "Auto Clock-Out UI Integration",
    body: `[Issue 4 content from above]`,
    labels: ["integration", "attendance", "ui", "warnings"]
  }
];

// Create each issue
issues.forEach(issue => {
  const cmd = `gh issue create --title "${issue.title}" --body "${issue.body}"`;
  exec(cmd, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error creating issue: ${error}`);
    } else {
      console.log(`✅ Created: ${stdout}`);
    }
  });
});
```

### **Step 3: Execution Instructions**

1. **Navigate to your frontend repository**
2. **Run the issue creation script**:
   ```bash
   node create_frontend_integration_issues.js
   ```
3. **Link issues to backend work** in issue descriptions
4. **Assign to appropriate frontend developers**
5. **Set proper priorities and milestones**

---

## 🎯 **BENEFITS FOR FRONTEND TEAM**

### **Clear Tracking**
- **✅ Visibility**: Each backend feature has corresponding frontend task
- **✅ Documentation**: Complete implementation guides included
- **✅ Priorities**: Critical path items clearly marked
- **✅ Cross-Reference**: Backend issues linked for context

### **Implementation Guidance**
- **✅ API Endpoints**: Exact endpoints and payload structures
- **✅ Event Formats**: Real-time event schemas and examples  
- **✅ Code Examples**: JavaScript/Vue/React integration patterns
- **✅ Testing Checklists**: Validation criteria for each feature

### **Coordination**
- **✅ Backend-Frontend Sync**: Matching issue numbers and references
- **✅ Status Tracking**: Clear completion status across teams
- **✅ Documentation Links**: Direct references to implementation guides
- **✅ Dependency Management**: Clear prerequisite relationships

---

## 📋 **FRONTEND TEAM ACTION ITEMS**

1. **✅ Create Issues**: Use the script above to generate frontend integration issues
2. **✅ Assign Developers**: Assign appropriate team members to each issue  
3. **✅ Set Priorities**: Mark critical path items (real-time events, chat)
4. **✅ Plan Sprints**: Include these in upcoming sprint planning
5. **✅ Test Integration**: Validate against backend documentation
6. **✅ Close When Complete**: Close issues as frontend integration completes

**The backend is ready and waiting! All APIs, events, and documentation are complete and production-ready.** 🚀

---

**Created**: December 8, 2025  
**Backend Issues**: #55-59 (Completed & Closed)  
**Frontend Status**: Ready for Integration  
**Documentation**: Complete implementation guides provided