# Frontend Implementation Guide: Breakfast Room Service Ordering System

## 📋 Overview

This guide provides complete instructions for implementing the breakfast ordering system in your frontend application. The backend API is fully functional with CRUD operations, QR code support, real-time notifications (Pusher), and push notifications (FCM).

---

## 🔗 API Endpoints Reference

### Base URL Pattern
```
https://your-backend.com/room_services/{hotel_slug}/
```

### Available Endpoints

#### 1. Breakfast Menu (Guest Access)
```http
GET /room_services/{hotel_slug}/room/{room_number}/breakfast/
```
**Description**: Retrieve all available breakfast items for a specific hotel  
**Authentication**: None required  
**Response**:
```json
[
  {
    "id": 1,
    "hotel": 1,
    "name": "Scrambled Eggs",
    "image": "https://cloudinary.com/...",
    "description": "Fluffy scrambled eggs with butter",
    "category": "Mains",
    "quantity": 1,
    "is_on_stock": true
  },
  {
    "id": 2,
    "name": "Orange Juice",
    "image": "https://cloudinary.com/...",
    "category": "Drinks",
    "is_on_stock": true
  }
]
```

#### 2. Validate Guest PIN
```http
POST /room_services/{hotel_slug}/room/{room_number}/validate-pin/
```
**Request Body**:
```json
{
  "pin": "abc123"
}
```
**Response**:
```json
{
  "valid": true
}
```
**Error Response** (401):
```json
{
  "valid": false
}
```

#### 3. Save Guest FCM Token
```http
POST /room_services/{hotel_slug}/room/{room_number}/save-fcm-token/
```
**Request Body**:
```json
{
  "fcm_token": "firebase_device_token_here"
}
```
**Response**:
```json
{
  "success": true,
  "message": "FCM token saved successfully"
}
```

#### 4. Create Breakfast Order
```http
POST /room_services/{hotel_slug}/breakfast-orders/
```
**Request Body**:
```json
{
  "room_number": 101,
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "item_id": 1,
      "quantity": 2
    },
    {
      "item_id": 3,
      "quantity": 1
    }
  ]
}
```
**Response** (201 Created):
```json
{
  "id": 42,
  "hotel": 1,
  "room_number": 101,
  "status": "pending",
  "created_at": "2025-11-04T10:30:00Z",
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "id": 1,
      "item": {
        "id": 1,
        "name": "Scrambled Eggs",
        "image": "https://...",
        "category": "Mains"
      },
      "quantity": 2
    }
  ]
}
```

#### 5. Get Order Details
```http
GET /room_services/{hotel_slug}/breakfast-orders/{order_id}/
```

#### 6. List Guest's Orders
```http
GET /room_services/{hotel_slug}/breakfast-orders/?room_number={room_number}
```

#### 7. Update Order Status (Staff Only)
```http
PATCH /room_services/{hotel_slug}/breakfast-orders/{order_id}/
```
**Request Body**:
```json
{
  "status": "accepted"
}
```
**Valid Status Transitions**:
- `pending` → `accepted`
- `accepted` → `completed`

#### 8. Get Pending Order Count (Staff)
```http
GET /room_services/{hotel_slug}/breakfast-orders/breakfast-pending-count/
```
**Response**:
```json
{
  "count": 5
}
```

---

## 🎨 Frontend Implementation Guide

### **Step 1: QR Code Scanning Flow**

```javascript
// When QR code is scanned, extract hotel_slug and room_number from URL
// URL format: https://hotelsmates.com/room_services/{hotel_slug}/room/{room_number}/breakfast/

const parseQRCodeURL = (url) => {
  const match = url.match(/room_services\/([^/]+)\/room\/(\d+)\/breakfast/);
  return {
    hotelSlug: match[1],
    roomNumber: match[2]
  };
};

// Example:
const scannedURL = "https://hotelsmates.com/room_services/grand-hotel/room/101/breakfast/";
const { hotelSlug, roomNumber } = parseQRCodeURL(scannedURL);
```

### **Step 2: Fetch Breakfast Menu**

```javascript
const fetchBreakfastMenu = async (hotelSlug, roomNumber) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/room/${roomNumber}/breakfast/`
    );
    
    if (!response.ok) throw new Error('Failed to fetch menu');
    
    const items = await response.json();
    
    // Filter out items not in stock
    const availableItems = items.filter(item => item.is_on_stock);
    
    // Group by category
    const groupedItems = availableItems.reduce((acc, item) => {
      if (!acc[item.category]) acc[item.category] = [];
      acc[item.category].push(item);
      return acc;
    }, {});
    
    return groupedItems;
  } catch (error) {
    console.error('Error fetching menu:', error);
    throw error;
  }
};
```

### **Step 3: Display Menu UI**

```jsx
// React Example
import React, { useState, useEffect } from 'react';

const BreakfastMenu = ({ hotelSlug, roomNumber }) => {
  const [menuItems, setMenuItems] = useState({});
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMenu();
  }, [hotelSlug, roomNumber]);

  const loadMenu = async () => {
    try {
      const items = await fetchBreakfastMenu(hotelSlug, roomNumber);
      setMenuItems(items);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (item, quantity = 1) => {
    setCart(prev => {
      const existing = prev.find(i => i.item_id === item.id);
      if (existing) {
        return prev.map(i => 
          i.item_id === item.id 
            ? { ...i, quantity: i.quantity + quantity }
            : i
        );
      }
      return [...prev, { item_id: item.id, quantity, item }];
    });
  };

  const removeFromCart = (itemId) => {
    setCart(prev => prev.filter(i => i.item_id !== itemId));
  };

  const updateQuantity = (itemId, newQuantity) => {
    if (newQuantity === 0) {
      removeFromCart(itemId);
      return;
    }
    setCart(prev => prev.map(i => 
      i.item_id === itemId ? { ...i, quantity: newQuantity } : i
    ));
  };

  if (loading) return <div>Loading menu...</div>;

  return (
    <div className="breakfast-menu">
      <h1>Breakfast Menu - Room {roomNumber}</h1>
      
      {Object.entries(menuItems).map(([category, items]) => (
        <div key={category} className="menu-category">
          <h2>{category}</h2>
          <div className="items-grid">
            {items.map(item => (
              <MenuItemCard 
                key={item.id}
                item={item}
                onAdd={addToCart}
              />
            ))}
          </div>
        </div>
      ))}

      <CartSummary 
        cart={cart}
        onUpdateQuantity={updateQuantity}
        onRemove={removeFromCart}
        onCheckout={() => handleCheckout()}
      />
    </div>
  );
};
```

### **Step 4: PIN Validation**

```javascript
const validatePIN = async (hotelSlug, roomNumber, pin) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/room/${roomNumber}/validate-pin/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pin })
      }
    );

    const data = await response.json();
    
    if (data.valid) {
      // Store PIN locally for session
      sessionStorage.setItem('guestPIN', pin);
      sessionStorage.setItem('validatedRoom', roomNumber);
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('PIN validation error:', error);
    return false;
  }
};

// PIN Input Component
const PINValidation = ({ hotelSlug, roomNumber, onValidated }) => {
  const [pin, setPIN] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const isValid = await validatePIN(hotelSlug, roomNumber, pin);
    
    if (isValid) {
      onValidated();
    } else {
      setError('Invalid PIN. Please try again.');
      setPIN('');
    }
    
    setLoading(false);
  };

  return (
    <div className="pin-validation">
      <h2>Verify Your Room</h2>
      <p>Please enter your 4-character room PIN</p>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={pin}
          onChange={(e) => setPIN(e.target.value.toLowerCase())}
          maxLength={4}
          placeholder="Enter PIN"
          className="pin-input"
        />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading || pin.length !== 4}>
          {loading ? 'Validating...' : 'Verify'}
        </button>
      </form>
    </div>
  );
};
```

### **Step 5: Delivery Time Selection**

```javascript
const DELIVERY_TIME_SLOTS = [
  { value: '7:00-8:00', label: '7:00 AM - 8:00 AM' },
  { value: '8:00-8:30', label: '8:00 AM - 8:30 AM' },
  { value: '8:30-9:00', label: '8:30 AM - 9:00 AM' },
  { value: '9:00-9:30', label: '9:00 AM - 9:30 AM' },
  { value: '9:30-10:00', label: '9:30 AM - 10:00 AM' },
  { value: '10:00-10:30', label: '10:00 AM - 10:30 AM' },
];

const DeliveryTimeSelector = ({ selectedTime, onChange }) => {
  return (
    <div className="delivery-time-selector">
      <h3>Select Delivery Time</h3>
      <select 
        value={selectedTime} 
        onChange={(e) => onChange(e.target.value)}
        required
      >
        <option value="">Choose a time slot</option>
        {DELIVERY_TIME_SLOTS.map(slot => (
          <option key={slot.value} value={slot.value}>
            {slot.label}
          </option>
        ))}
      </select>
    </div>
  );
};
```

### **Step 6: Submit Order**

```javascript
const submitBreakfastOrder = async (hotelSlug, roomNumber, cart, deliveryTime) => {
  try {
    // Validate cart is not empty
    if (cart.length === 0) {
      throw new Error('Cart is empty');
    }

    // Validate delivery time is selected
    if (!deliveryTime) {
      throw new Error('Please select a delivery time');
    }

    // Format items for API
    const items = cart.map(cartItem => ({
      item_id: cartItem.item_id,
      quantity: cartItem.quantity
    }));

    const orderData = {
      room_number: parseInt(roomNumber),
      delivery_time: deliveryTime,
      items: items
    };

    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/breakfast-orders/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to submit order');
    }

    const order = await response.json();
    return order;
  } catch (error) {
    console.error('Error submitting order:', error);
    throw error;
  }
};

// Checkout Component
const CheckoutForm = ({ hotelSlug, roomNumber, cart, onSuccess }) => {
  const [deliveryTime, setDeliveryTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const order = await submitBreakfastOrder(
        hotelSlug, 
        roomNumber, 
        cart, 
        deliveryTime
      );
      
      // Success!
      onSuccess(order);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="checkout-form">
      <h2>Complete Your Order</h2>
      
      <DeliveryTimeSelector 
        selectedTime={deliveryTime}
        onChange={setDeliveryTime}
      />

      <div className="order-summary">
        <h3>Order Summary</h3>
        {cart.map(item => (
          <div key={item.item_id} className="order-item">
            <span>{item.item.name}</span>
            <span>x{item.quantity}</span>
          </div>
        ))}
      </div>

      {error && <p className="error">{error}</p>}

      <button 
        type="submit" 
        disabled={loading || !deliveryTime}
        className="submit-order-btn"
      >
        {loading ? 'Placing Order...' : 'Place Order'}
      </button>
    </form>
  );
};
```

### **Step 7: Order Confirmation & Tracking**

```javascript
const OrderConfirmation = ({ order }) => {
  return (
    <div className="order-confirmation">
      <div className="success-icon">✓</div>
      <h2>Order Confirmed!</h2>
      <p>Order #{order.id}</p>
      <p>Delivery Time: {order.delivery_time}</p>
      <p>Status: {order.status}</p>
      
      <div className="order-items">
        <h3>Your Items:</h3>
        {order.items.map(item => (
          <div key={item.id}>
            <span>{item.item.name}</span>
            <span>x{item.quantity}</span>
          </div>
        ))}
      </div>

      <p className="info-message">
        Your breakfast will be delivered to Room {order.room_number} 
        between {order.delivery_time}
      </p>
    </div>
  );
};

// View Guest Orders
const fetchGuestOrders = async (hotelSlug, roomNumber) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/breakfast-orders/?room_number=${roomNumber}`
    );
    
    if (!response.ok) throw new Error('Failed to fetch orders');
    
    const orders = await response.json();
    return orders;
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

const MyOrders = ({ hotelSlug, roomNumber }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, [hotelSlug, roomNumber]);

  const loadOrders = async () => {
    try {
      const data = await fetchGuestOrders(hotelSlug, roomNumber);
      setOrders(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading orders...</div>;

  return (
    <div className="my-orders">
      <h2>My Orders</h2>
      {orders.length === 0 ? (
        <p>No active orders</p>
      ) : (
        orders.map(order => (
          <OrderCard key={order.id} order={order} />
        ))
      )}
    </div>
  );
};
```

---

## 🔔 Real-Time Updates with Pusher

### **Step 8: Setup Pusher Client**

```javascript
// Install Pusher
// npm install pusher-js

import Pusher from 'pusher-js';

// Initialize Pusher
const pusher = new Pusher('YOUR_PUSHER_KEY', {
  cluster: 'YOUR_PUSHER_CLUSTER',
  encrypted: true
});

// Subscribe to guest room channel for order updates
const subscribeToOrderUpdates = (hotelSlug, roomNumber, onUpdate) => {
  const channelName = `${hotelSlug}-room-${roomNumber}`;
  const channel = pusher.subscribe(channelName);

  channel.bind('order-status-update', (data) => {
    console.log('Order status updated:', data);
    onUpdate(data);
  });

  return () => {
    channel.unbind_all();
    pusher.unsubscribe(channelName);
  };
};

// Usage in React Component
const OrderTracking = ({ hotelSlug, roomNumber, orderId }) => {
  const [orderStatus, setOrderStatus] = useState('pending');

  useEffect(() => {
    const unsubscribe = subscribeToOrderUpdates(
      hotelSlug, 
      roomNumber, 
      (data) => {
        if (data.updated_order_id === orderId) {
          setOrderStatus(data.new_status);
          
          // Show notification
          showNotification(`Order ${data.new_status}`);
        }
      }
    );

    return unsubscribe;
  }, [hotelSlug, roomNumber, orderId]);

  return (
    <div className="order-tracking">
      <h3>Order Status</h3>
      <StatusBadge status={orderStatus} />
    </div>
  );
};
```

---

## 📱 Push Notifications with Firebase

### **Step 9: Setup Firebase Cloud Messaging**

```javascript
// Install Firebase
// npm install firebase

import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_STORAGE_BUCKET",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Request permission and get FCM token
const requestNotificationPermission = async () => {
  try {
    const permission = await Notification.requestPermission();
    
    if (permission === 'granted') {
      const token = await getToken(messaging, {
        vapidKey: 'YOUR_VAPID_KEY'
      });
      
      console.log('FCM Token:', token);
      return token;
    }
    
    console.log('Notification permission denied');
    return null;
  } catch (error) {
    console.error('Error getting FCM token:', error);
    return null;
  }
};

// Save FCM token to backend
const saveFCMToken = async (hotelSlug, roomNumber, token) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/room/${roomNumber}/save-fcm-token/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fcm_token: token })
      }
    );

    if (!response.ok) throw new Error('Failed to save FCM token');
    
    const data = await response.json();
    console.log('FCM token saved:', data);
    return true;
  } catch (error) {
    console.error('Error saving FCM token:', error);
    return false;
  }
};

// Listen for foreground messages
onMessage(messaging, (payload) => {
  console.log('Foreground message:', payload);
  
  const { notification, data } = payload;
  
  // Show custom notification
  showCustomNotification(notification.title, notification.body, data);
});

// Setup notifications after PIN validation
const setupGuestNotifications = async (hotelSlug, roomNumber) => {
  const token = await requestNotificationPermission();
  
  if (token) {
    await saveFCMToken(hotelSlug, roomNumber, token);
    console.log('Push notifications enabled');
  }
};
```

---

## 👨‍💼 Staff Dashboard Implementation

### **Step 10: Staff Order Management**

```javascript
// Fetch all pending breakfast orders
const fetchStaffBreakfastOrders = async (hotelSlug) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/breakfast-orders/`,
      {
        headers: {
          'Authorization': `Bearer ${staffToken}` // If using auth
        }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch orders');
    
    const orders = await response.json();
    return orders;
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

// Update order status
const updateOrderStatus = async (hotelSlug, orderId, newStatus) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/room_services/${hotelSlug}/breakfast-orders/${orderId}/`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${staffToken}`
        },
        body: JSON.stringify({ status: newStatus })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update order');
    }

    const updatedOrder = await response.json();
    return updatedOrder;
  } catch (error) {
    console.error('Error updating order:', error);
    throw error;
  }
};

// Staff Dashboard Component
const StaffBreakfastDashboard = ({ hotelSlug, staffId }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
    subscribeToStaffUpdates();
  }, [hotelSlug, staffId]);

  const loadOrders = async () => {
    try {
      const data = await fetchStaffBreakfastOrders(hotelSlug);
      setOrders(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const subscribeToStaffUpdates = () => {
    // Subscribe to staff channel for new orders
    const channelName = `${hotelSlug}-staff-${staffId}-kitchen`;
    const channel = pusher.subscribe(channelName);

    channel.bind('new-breakfast-order', (data) => {
      console.log('New breakfast order:', data);
      loadOrders(); // Refresh orders
      showNotification('New breakfast order received!');
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(channelName);
    };
  };

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(hotelSlug, orderId, newStatus);
      loadOrders(); // Refresh list
    } catch (error) {
      alert(error.message);
    }
  };

  if (loading) return <div>Loading orders...</div>;

  return (
    <div className="staff-dashboard">
      <h1>Breakfast Orders</h1>
      
      <div className="orders-list">
        {orders.map(order => (
          <StaffOrderCard 
            key={order.id}
            order={order}
            onStatusChange={handleStatusChange}
          />
        ))}
      </div>
    </div>
  );
};

const StaffOrderCard = ({ order, onStatusChange }) => {
  const canAccept = order.status === 'pending';
  const canComplete = order.status === 'accepted';

  return (
    <div className={`order-card status-${order.status}`}>
      <div className="order-header">
        <h3>Order #{order.id}</h3>
        <StatusBadge status={order.status} />
      </div>
      
      <div className="order-info">
        <p><strong>Room:</strong> {order.room_number}</p>
        <p><strong>Delivery Time:</strong> {order.delivery_time}</p>
        <p><strong>Created:</strong> {new Date(order.created_at).toLocaleString()}</p>
      </div>

      <div className="order-items">
        <h4>Items:</h4>
        {order.items.map(item => (
          <div key={item.id} className="item">
            <span>{item.item.name}</span>
            <span>x{item.quantity}</span>
          </div>
        ))}
      </div>

      <div className="actions">
        {canAccept && (
          <button 
            onClick={() => onStatusChange(order.id, 'accepted')}
            className="btn-accept"
          >
            Accept Order
          </button>
        )}
        {canComplete && (
          <button 
            onClick={() => onStatusChange(order.id, 'completed')}
            className="btn-complete"
          >
            Mark as Completed
          </button>
        )}
      </div>
    </div>
  );
};
```

---

## 🎯 Complete User Flow Example

```javascript
// Main App Component
const BreakfastOrderApp = () => {
  const [step, setStep] = useState('scan'); // scan, menu, checkout, confirmation
  const [hotelSlug, setHotelSlug] = useState(null);
  const [roomNumber, setRoomNumber] = useState(null);
  const [isValidated, setIsValidated] = useState(false);
  const [cart, setCart] = useState([]);
  const [currentOrder, setCurrentOrder] = useState(null);

  // Step 1: QR Code Scan
  const handleQRScan = (url) => {
    const { hotelSlug, roomNumber } = parseQRCodeURL(url);
    setHotelSlug(hotelSlug);
    setRoomNumber(roomNumber);
    setStep('pin');
  };

  // Step 2: PIN Validation
  const handlePINValidated = async () => {
    setIsValidated(true);
    // Setup notifications
    await setupGuestNotifications(hotelSlug, roomNumber);
    setStep('menu');
  };

  // Step 3: Browse Menu & Add to Cart
  const handleAddToCart = (item, quantity) => {
    setCart(prev => [...prev, { item_id: item.id, quantity, item }]);
  };

  // Step 4: Checkout
  const handleCheckout = () => {
    setStep('checkout');
  };

  // Step 5: Submit Order
  const handleOrderSubmit = async (deliveryTime) => {
    try {
      const order = await submitBreakfastOrder(
        hotelSlug, 
        roomNumber, 
        cart, 
        deliveryTime
      );
      setCurrentOrder(order);
      setCart([]);
      setStep('confirmation');
    } catch (error) {
      alert(error.message);
    }
  };

  return (
    <div className="breakfast-order-app">
      {step === 'scan' && (
        <QRScanner onScan={handleQRScan} />
      )}
      
      {step === 'pin' && (
        <PINValidation 
          hotelSlug={hotelSlug}
          roomNumber={roomNumber}
          onValidated={handlePINValidated}
        />
      )}
      
      {step === 'menu' && isValidated && (
        <BreakfastMenu 
          hotelSlug={hotelSlug}
          roomNumber={roomNumber}
          cart={cart}
          onAddToCart={handleAddToCart}
          onCheckout={handleCheckout}
        />
      )}
      
      {step === 'checkout' && (
        <CheckoutForm 
          hotelSlug={hotelSlug}
          roomNumber={roomNumber}
          cart={cart}
          onSuccess={(order) => {
            setCurrentOrder(order);
            setStep('confirmation');
          }}
        />
      )}
      
      {step === 'confirmation' && currentOrder && (
        <OrderConfirmation order={currentOrder} />
      )}
    </div>
  );
};
```

---

## 📊 Status Workflow

```
┌─────────┐
│ PENDING │ ← Order created
└────┬────┘
     │
     │ Staff accepts
     ↓
┌──────────┐
│ ACCEPTED │ ← Order being prepared
└────┬─────┘
     │
     │ Staff marks complete
     ↓
┌───────────┐
│ COMPLETED │ ← Order delivered
└───────────┘
```

**Important**: 
- Only `pending` → `accepted` transition is allowed
- Only `accepted` → `completed` transition is allowed
- Backend enforces these rules

---

## 🔧 Error Handling

```javascript
// Common error scenarios
const handleAPIError = (error, context) => {
  console.error(`Error in ${context}:`, error);
  
  if (error.message.includes('404')) {
    return 'Hotel or room not found';
  }
  
  if (error.message.includes('401')) {
    return 'Invalid PIN or unauthorized';
  }
  
  if (error.message.includes('400')) {
    return 'Invalid request. Please check your input.';
  }
  
  if (error.message.includes('500')) {
    return 'Server error. Please try again later.';
  }
  
  return 'An unexpected error occurred';
};
```

---

## ✅ Testing Checklist

- [ ] QR code scanning works
- [ ] Menu loads correctly with all categories
- [ ] Items can be added/removed from cart
- [ ] PIN validation works
- [ ] Invalid PIN shows error
- [ ] Delivery time selection required
- [ ] Order submission successful
- [ ] Order confirmation displays
- [ ] Pusher real-time updates work
- [ ] FCM push notifications work (browser closed)
- [ ] Staff can view orders
- [ ] Staff can update order status
- [ ] Status transitions validated correctly
- [ ] Guest can view their order history

---

## 🚀 Deployment Notes

1. **Environment Variables**:
   - `REACT_APP_API_BASE_URL`
   - `REACT_APP_PUSHER_KEY`
   - `REACT_APP_PUSHER_CLUSTER`
   - `REACT_APP_FIREBASE_CONFIG` (JSON string)

2. **Service Worker**: Register Firebase messaging service worker for background notifications

3. **HTTPS Required**: FCM requires HTTPS in production

4. **CORS**: Backend already configured to allow frontend origin

---

## 📞 Support

For backend API issues or questions:
- Check backend logs
- Verify Pusher/FCM credentials in settings
- Test endpoints with Postman/curl first
- Check that room has valid `guest_id_pin` generated

---

**Happy Coding! 🎉**
