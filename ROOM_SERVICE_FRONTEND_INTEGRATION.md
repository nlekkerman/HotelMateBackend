# Room Service Frontend Integration Guide

## 🏨 Room Service Status Updates & Pusher Integration

### **Status Flow**
```
📋 pending → ✅ accepted → 🏁 completed
```

**Status Validation**: Orders must follow the proper sequence. No skipping or going backwards!

---

## 📡 **Pusher Real-time Events**

### **Channel**: `{hotel_slug}.room-service`

### **Events**: `order_created` & `order_updated`

**Triggered When**: 
- `order_created` - New order is placed by guest
- `order_updated` - Staff updates order status (pending → accepted → completed)

### **Event Data Structure**:
```json
{
  "category": "room_service",
  "type": "order_created", 
  "payload": {
    "order_id": 123,
    "room_number": 101,
    "status": "pending",
    "total_price": 25.50,
    "created_at": "2025-12-11T10:30:00Z",
    "updated_at": "2025-12-11T10:30:00Z", 
    "items": [
      {
        "id": 1,
        "name": "Cheeseburger",
        "quantity": 1,
        "price": 15.50,
        "total": 15.50
      },
      {
        "id": 2,
        "name": "French Fries", 
        "quantity": 1,
        "price": 8.00,
        "total": 8.00
      }
    ],
    "special_instructions": "No pickles, extra sauce",
    "estimated_delivery": "2025-12-11T11:00:00Z",
    "priority": "normal"
  },
  "meta": {
    "hotel_slug": "hotel-killarney",
    "event_id": "uuid-12345",
    "ts": "2025-12-11T10:30:00Z",
    "scope": {
      "order_id": 123,
      "room_number": 101, 
      "status": "pending"
    }
  }
}
```

---

## 🖥️ **Frontend Implementation**

### **1. Subscribe to Room Service Channel**

```javascript
// Initialize Pusher connection
const pusher = new Pusher('your-pusher-key', {
  cluster: 'your-cluster',
  encrypted: true
});

// Subscribe to hotel's room service channel
const hotelSlug = 'hotel-killarney'; // Get from hotel context
const roomServiceChannel = pusher.subscribe(`${hotelSlug}.room-service`);
```

### **2. Listen for Order Events**

```javascript
// Listen for new orders
roomServiceChannel.bind('order_created', function(eventData) {
  console.log('🆕 New room service order:', eventData);
  
  const order = eventData.payload;
  const meta = eventData.meta;
  
  // Add new order to your state/store
  addNewOrder(order);
  
  // Show notification for new order
  showNewOrderNotification(order);
  
  // Update UI elements
  refreshOrderList();
});

// Listen for order status updates
roomServiceChannel.bind('order_updated', function(eventData) {
  console.log('🔄 Room service order updated:', eventData);
  
  const order = eventData.payload;
  const meta = eventData.meta;
  
  // Update order in your state/store
  updateOrderStatus(order.order_id, order.status);
  
  // Show notification based on status
  showOrderStatusNotification(order);
  
  // Update UI elements
  refreshOrderList();
});
```

### **3. Handle Status Updates in UI**

```javascript
function updateOrderStatus(orderId, newStatus) {
  // Find order in your state/store
  const orderElement = document.getElementById(`order-${orderId}`);
  
  if (orderElement) {
    // Update status badge
    const statusBadge = orderElement.querySelector('.status-badge');
    statusBadge.className = `status-badge status-${newStatus}`;
    statusBadge.textContent = capitalizeStatus(newStatus);
    
    // Update progress indicator
    updateProgressBar(orderElement, newStatus);
  }
}

function capitalizeStatus(status) {
  const statusMap = {
    'pending': 'Pending',
    'accepted': 'Accepted', 
    'completed': 'Completed'
  };
  return statusMap[status] || status;
}

function updateProgressBar(orderElement, status) {
  const progressBar = orderElement.querySelector('.progress-bar');
  const progressMap = {
    'pending': '33%',
    'accepted': '66%', 
    'completed': '100%'
  };
  
  if (progressBar) {
    progressBar.style.width = progressMap[status];
  }
}
```

### **4. Show Real-time Notifications**

```javascript
function showNewOrderNotification(order) {
  const message = `🆕 New Order #${order.order_id} from Room ${order.room_number}`;
  
  // Show toast/snackbar notification for new orders
  showToast(message, {
    type: 'info',
    duration: 5000,
    action: {
      text: 'View Order',
      onClick: () => navigateToOrder(order.order_id)
    }
  });
  
  // Play notification sound for new orders (staff dashboard)
  playNotificationSound();
}

function showOrderStatusNotification(order) {
  const statusMessages = {
    'pending': `📋 Order #${order.order_id} is pending`,
    'accepted': `✅ Order #${order.order_id} has been accepted!`,
    'completed': `🏁 Order #${order.order_id} is ready for delivery!`
  };
  
  const message = statusMessages[order.status];
  
  // Show toast/snackbar notification
  showToast(message, {
    type: order.status === 'completed' ? 'success' : 'info',
    duration: 4000,
    action: {
      text: 'View Order',
      onClick: () => navigateToOrder(order.order_id)
    }
  });
  
  // Play notification sound for completed orders
  if (order.status === 'completed') {
    playNotificationSound();
  }
}
```

---

## 🎯 **Room-Specific Updates (Guest App)**

### **For Guest Mobile App / Room Interface**

```javascript
// Subscribe to guest's specific room updates
const roomNumber = getCurrentRoomNumber(); // e.g., 101
const guestChannel = pusher.subscribe(`${hotelSlug}.room-${roomNumber}`);

// Listen for new orders for this room
roomServiceChannel.bind('order_created', function(eventData) {
  const order = eventData.payload;
  
  // Only show updates for current room
  if (order.room_number === roomNumber) {
    showGuestOrderConfirmation(order);
  }
});

// Listen for order updates that affect this room
roomServiceChannel.bind('order_updated', function(eventData) {
  const order = eventData.payload;
  
  // Only show updates for current room
  if (order.room_number === roomNumber) {
    updateGuestOrderStatus(order);
  }
});

function showGuestOrderConfirmation(order) {
  // Show order confirmation when order is first created
  const confirmationMessage = `Order #${order.order_id} confirmed! Your ${order.items.length} item(s) have been sent to the kitchen.`;
  showToast(confirmationMessage, { type: 'success', duration: 4000 });
  
  // Initialize order tracker
  initializeOrderTracker(order);
}

function updateGuestOrderStatus(order) {
  // Update guest's order tracking screen
  const orderTracker = document.getElementById('order-tracker');
  
  if (orderTracker && orderTracker.dataset.orderId == order.order_id) {
    // Update status steps
    updateOrderSteps(order.status);
    
    // Update estimated delivery time
    if (order.estimated_delivery) {
      updateDeliveryTime(order.estimated_delivery);
    }
    
    // Show status-specific messages
    const guestMessages = {
      'pending': 'Your order is being reviewed by our kitchen staff',
      'accepted': 'Great! Your order is being prepared',
      'completed': 'Your order is ready and on its way to your room!'
    };
    
    updateStatusMessage(guestMessages[order.status]);
  }
}
```

---

## 🛠️ **Staff Dashboard Integration**

### **For Kitchen Staff / Room Service Staff**

```javascript
// Staff dashboard - listen for new orders
roomServiceChannel.bind('order_created', function(eventData) {
  const order = eventData.payload;
  
  // Add new order to staff dashboard
  addOrderToStaffDashboard(order);
  
  // Update pending orders counter
  updatePendingCount();
  
  // Show notification to staff
  showStaffNotification(`New Order #${order.order_id} from Room ${order.room_number}`);
  
  // Highlight urgent orders
  if (order.priority === 'urgent') {
    highlightUrgentOrder(order.order_id);
  }
});

// Staff dashboard - listen for order updates
roomServiceChannel.bind('order_updated', function(eventData) {
  const order = eventData.payload;
  
  // Update order in staff dashboard
  updateStaffDashboard(order);
  
  // Update pending orders counter
  updatePendingCount();
  
  // Highlight urgent orders
  if (order.status === 'accepted' && isOrderUrgent(order)) {
    highlightUrgentOrder(order.order_id);
  }
});

function updateStaffDashboard(order) {
  // Update order card in dashboard
  const orderCard = document.getElementById(`staff-order-${order.order_id}`);
  
  if (orderCard) {
    // Update status
    orderCard.querySelector('.order-status').textContent = order.status;
    orderCard.querySelector('.order-status').className = `order-status ${order.status}`;
    
    // Update timestamp
    orderCard.querySelector('.last-updated').textContent = 
      `Updated: ${formatTime(order.updated_at)}`;
    
    // Show/hide action buttons based on status
    updateActionButtons(orderCard, order.status);
  }
}

function updateActionButtons(orderCard, status) {
  const acceptBtn = orderCard.querySelector('.accept-btn');
  const completeBtn = orderCard.querySelector('.complete-btn');
  
  if (status === 'pending') {
    acceptBtn.style.display = 'block';
    completeBtn.style.display = 'none';
  } else if (status === 'accepted') {
    acceptBtn.style.display = 'none';
    completeBtn.style.display = 'block';
  } else if (status === 'completed') {
    acceptBtn.style.display = 'none';
    completeBtn.style.display = 'none';
  }
}
```

---

## 🔄 **API Endpoints for Status Updates**

### **Update Order Status**
```http
PATCH /room_services/{hotel_slug}/orders/{order_id}/
Content-Type: application/json

{
  "status": "accepted"  // or "completed"
}
```

### **Response**:
```json
{
  "id": 123,
  "room_number": 101,
  "status": "accepted",
  "total_price": "25.50",
  "created_at": "2025-12-11T10:30:00Z",
  "updated_at": "2025-12-11T10:35:00Z",
  "orderitem_set": [...]
}
```

### **Error Response** (Invalid Transition):
```json
{
  "error": "Invalid status transition from 'pending' to 'completed'. Allowed: ['accepted']"
}
```

---

## 🎨 **CSS Status Styling**

```css
/* Status badges */
.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-pending {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.status-accepted {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #74c0fc;
}

.status-completed {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #51cf66;
}

/* Progress bar */
.order-progress {
  width: 100%;
  height: 6px;
  background-color: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #ffd43b 0%, #74c0fc 50%, #51cf66 100%);
  transition: width 0.3s ease;
}
```

---

## 🔍 **Testing & Debugging**

### **Test Order Status Updates**:

1. **Create Order**: POST to `/room_services/{hotel_slug}/orders/`
2. **Update Status**: PATCH to `/room_services/{hotel_slug}/orders/{id}/`
3. **Monitor Pusher**: Check browser dev tools → Network → WS for Pusher events
4. **Check Console**: Look for `🔄 Room service order updated:` logs

### **Common Issues**:

- **No Pusher Events**: Check hotel_slug matches subscription
- **Status Not Updating**: Verify order ID exists and status transition is valid
- **Permission Errors**: Ensure proper API authentication

### **Debug Pusher Events**:
```javascript
// Enable Pusher logging
Pusher.logToConsole = true;

// Log all events for debugging
roomServiceChannel.bind_global(function(eventName, data) {
  console.log('Pusher Event:', eventName, data);
});
```

---

## 📱 **Mobile App Integration**

### **React Native / Flutter**

```javascript
// Subscribe to channel
const channel = pusher.subscribe(`${hotelSlug}.room-service`);

// Handle new orders
channel.bind('order_created', (data) => {
  // Add new order to Redux/state management
  dispatch(addNewOrder(data.payload));
  
  // Show push notification if app is backgrounded
  if (AppState.currentState === 'background') {
    showLocalNotification({
      title: 'New Room Service Order',
      body: `Order #${data.payload.order_id} from Room ${data.payload.room_number}`,
      data: data.payload
    });
  }
});

// Handle order updates
channel.bind('order_updated', (data) => {
  // Update Redux/state management
  dispatch(updateOrder(data.payload));
  
  // Show push notification if app is backgrounded
  if (AppState.currentState === 'background') {
    const statusMessage = {
      'accepted': 'has been accepted',
      'completed': 'is ready for delivery'
    }[data.payload.status] || 'has been updated';
    
    showLocalNotification({
      title: 'Order Update',
      body: `Order #${data.payload.order_id} ${statusMessage}`,
      data: data.payload
    });
  }
});
```

---

## 🚀 **Key Benefits**

✅ **Real-time Updates**: Instant status changes across all devices  
✅ **Consistent Data**: Normalized event structure  
✅ **Better UX**: No page refresh needed  
✅ **Error Handling**: Proper validation and error messages  
✅ **Scalable**: Works across multiple hotel properties  

---

**Questions?** Check the main notification manager at `notifications/notification_manager.py` line 625+ for implementation details.