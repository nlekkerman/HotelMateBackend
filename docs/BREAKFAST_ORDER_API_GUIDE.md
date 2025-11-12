# In-Room Breakfast Order API Guide

Complete API documentation for in-room breakfast order submission and management in HotelMate.

---

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Pusher Real-Time Notifications](#pusher-real-time-notifications)
- [Endpoints](#endpoints)
  - [List Breakfast Items](#list-breakfast-items)
  - [Create Breakfast Order](#create-breakfast-order)
  - [List Breakfast Orders](#list-breakfast-orders)
  - [Get Order Details](#get-order-details)
  - [Update Order Status](#update-order-status)
  - [Get Pending Count](#get-pending-count)
- [Data Models](#data-models)
- [Required Fields Summary](#required-fields-summary)
- [Examples](#examples)
- [Error Handling](#error-handling)
- [Pusher Events](#pusher-events)

---

## Overview

The Breakfast Order API allows guests to order in-room breakfast with delivery time slots. Orders are created and tracked in real-time using Pusher notifications to alert kitchen staff, room service waiters, and porters.

**Key Features:**
- ✅ Automatic hotel assignment via URL parameter
- ✅ Time slot delivery scheduling (7:00 AM - 10:30 AM)
- ✅ **Real-time Pusher notifications** to staff (kitchen, waiters, porters)
- ✅ Status workflow: pending → accepted → completed
- ✅ Room-based filtering and history
- ✅ Items with categories (Mains, Hot Buffet, Cold Buffet, Breads, Condiments, Drinks)

---

## Authentication

Most endpoints allow anonymous access for guests. Staff endpoints require authentication.

**For Anonymous Guests:**
- No authentication required for creating orders
- Validate room PIN before submission (recommended)

**For Staff:**
```http
Authorization: Bearer <your-token-here>
```

---

## Base URL

```
/api/room_services/{hotel_slug}/
```

---

## Pusher Real-Time Notifications

### ✅ Pusher Integration Confirmed

When a breakfast order is submitted, **Pusher notifications are automatically sent** to:

1. **Kitchen Staff** (on-duty only)
   - Channel: `{hotel_slug}-staff-kitchen-{staff_id}`
   - Event: `new-breakfast-order`
   - Purpose: Alert kitchen staff to prepare the order

2. **Room Service Waiters** (on-duty only)
   - Channel: `{hotel_slug}-staff-room_service_waiter-{staff_id}`
   - Event: `new-breakfast-order`
   - Purpose: Coordinate order delivery

3. **Porters** (on-duty only)
   - Channel: `{hotel_slug}-staff-porter-{staff_id}`
   - Event: `new-breakfast-delivery`
   - Purpose: Deliver order to guest room

### Notification Payload Example

```json
{
  "order_id": 42,
  "room_number": 305,
  "delivery_time": "08:00:00",
  "created_at": "2025-11-12T07:30:00Z",
  "status": "pending"
}
```

---

## Endpoints

### List Breakfast Items

Get all available breakfast items for a hotel (menu).

**Endpoint:** `GET /api/room_services/{hotel_slug}/breakfast_items/`

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel identifier

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "hotel": 5,
    "name": "Full English Breakfast",
    "image": "https://res.cloudinary.com/.../breakfast.jpg",
    "description": "Eggs, bacon, sausages, beans, mushrooms, toast",
    "category": "Mains",
    "quantity": 1,
    "is_on_stock": true
  },
  {
    "id": 2,
    "hotel": 5,
    "name": "Scrambled Eggs",
    "image": "https://res.cloudinary.com/.../eggs.jpg",
    "description": "Fresh scrambled eggs with herbs",
    "category": "Hot Buffet",
    "quantity": 1,
    "is_on_stock": true
  },
  {
    "id": 3,
    "hotel": 5,
    "name": "Orange Juice",
    "image": "https://res.cloudinary.com/.../juice.jpg",
    "description": "Freshly squeezed orange juice",
    "category": "Drinks",
    "quantity": 1,
    "is_on_stock": true
  }
]
```

**Categories:**
- `Mains` - Main breakfast dishes
- `Hot Buffet` - Hot buffet items
- `Cold Buffet` - Cold buffet items
- `Breads` - Bread and pastries
- `Condiments` - Jams, butter, spreads
- `Drinks` - Beverages

---

### Create Breakfast Order

Submit a new breakfast order for a room with delivery time slot.

**Endpoint:** `POST /api/room_services/{hotel_slug}/breakfast_orders/`

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel identifier

**Request Body:**

```json
{
  "room_number": 305,
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "item_id": 1,
      "quantity": 1,
      "notes": "No mushrooms please"
    },
    {
      "item_id": 3,
      "quantity": 2,
      "notes": "Extra ice"
    },
    {
      "item_id": 5,
      "quantity": 1
    }
  ]
}
```

**Required Fields:**
- `room_number` (integer) - Room number for delivery
- `items` (array) - List of ordered items
  - `item_id` (integer) - ID of the breakfast item
  - `quantity` (integer) - Quantity ordered

**Optional Fields:**
- `delivery_time` (string) - Delivery time slot (see choices below)
- `items[].notes` (string) - Special instructions or preferences for the item

**Delivery Time Slot Choices:**
- `"7:00-8:00"` - 7:00 - 8:00 AM
- `"8:00-8:30"` - 8:00 - 8:30 AM
- `"8:30-9:00"` - 8:30 - 9:00 AM
- `"9:00-9:30"` - 9:00 - 9:30 AM
- `"9:30-10:00"` - 9:30 - 10:00 AM
- `"10:00-10:30"` - 10:00 - 10:30 AM

**Response (201 Created):**

```json
{
  "id": 42,
  "hotel": 5,
  "room_number": 305,
  "status": "pending",
  "created_at": "2025-11-12T07:30:00Z",
  "updated_at": "2025-11-12T07:30:00Z",
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "id": 101,
      "item": {
        "id": 1,
        "hotel": 5,
        "name": "Full English Breakfast",
        "image": "https://res.cloudinary.com/.../breakfast.jpg",
        "description": "Eggs, bacon, sausages, beans, mushrooms, toast",
        "category": "Mains",
        "quantity": 1,
        "is_on_stock": true
      },
      "quantity": 1,
      "notes": "No mushrooms please"
    },
    {
      "id": 102,
      "item": {
        "id": 3,
        "hotel": 5,
        "name": "Orange Juice",
        "image": "https://res.cloudinary.com/.../juice.jpg",
        "description": "Freshly squeezed orange juice",
        "category": "Drinks",
        "quantity": 1,
        "is_on_stock": true
      },
      "quantity": 2,
      "notes": "Extra ice"
    }
  ]
}
```

**Automatic Actions After Creation:**

1. ✅ **Pusher Notification to Kitchen Staff**
   - Event: `new-breakfast-order`
   - Notifies all on-duty kitchen staff

2. ✅ **Pusher Notification to Room Service Waiters**
   - Event: `new-breakfast-order`
   - Notifies all on-duty waiters

3. ✅ **Pusher Notification to Porters**
   - Event: `new-breakfast-delivery`
   - Notifies all on-duty porters

---

### List Breakfast Orders

Get all active breakfast orders (pending/accepted) for a hotel.

**Endpoint:** `GET /api/room_services/{hotel_slug}/breakfast_orders/`

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel identifier

**Query Parameters:**
- `room_number` (integer, optional) - Filter by specific room

**Response (200 OK):**

```json
[
  {
    "id": 42,
    "hotel": 5,
    "room_number": 305,
    "status": "pending",
    "created_at": "2025-11-12T07:30:00Z",
    "delivery_time": "8:00-8:30",
    "items": [
      {
        "id": 101,
        "item": {
          "id": 1,
          "name": "Full English Breakfast",
          "category": "Mains"
        },
        "quantity": 1
      }
    ]
  },
  {
    "id": 43,
    "hotel": 5,
    "room_number": 412,
    "status": "accepted",
    "created_at": "2025-11-12T07:45:00Z",
    "delivery_time": "9:00-9:30",
    "items": [
      {
        "id": 103,
        "item": {
          "id": 2,
          "name": "Scrambled Eggs",
          "category": "Hot Buffet"
        },
        "quantity": 2
      }
    ]
  }
]
```

**Note:** Completed orders are excluded from this list.

---

### Get Order Details

Retrieve details of a specific breakfast order.

**Endpoint:** `GET /api/room_services/{hotel_slug}/breakfast_orders/{order_id}/`

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel identifier
- `order_id` (integer, required) - Order ID

**Response (200 OK):**

```json
{
  "id": 42,
  "hotel": 5,
  "room_number": 305,
  "status": "pending",
  "created_at": "2025-11-12T07:30:00Z",
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "id": 101,
      "item": {
        "id": 1,
        "hotel": 5,
        "name": "Full English Breakfast",
        "image": "https://res.cloudinary.com/.../breakfast.jpg",
        "description": "Eggs, bacon, sausages, beans, mushrooms, toast",
        "category": "Mains",
        "quantity": 1,
        "is_on_stock": true
      },
      "quantity": 1
    }
  ]
}
```

---

### Update Order Status

Update the status of a breakfast order (staff only).

**Endpoint:** `PATCH /api/room_services/{hotel_slug}/breakfast_orders/{order_id}/`

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel identifier
- `order_id` (integer, required) - Order ID

**Request Body:**

```json
{
  "status": "accepted"
}
```

**Status Workflow (Enforced):**
- `pending` → `accepted` ✅
- `accepted` → `completed` ✅
- `completed` → (no further changes) ❌

**Invalid Transitions:**
- `pending` → `completed` ❌ (must go through "accepted" first)
- `accepted` → `pending` ❌ (cannot go backwards)

**Response (200 OK):**

```json
{
  "id": 42,
  "hotel": 5,
  "room_number": 305,
  "status": "accepted",
  "created_at": "2025-11-12T07:30:00Z",
  "delivery_time": "8:00-8:30",
  "items": [...]
}
```

**Error Response (400 Bad Request):**

```json
{
  "error": "Invalid status transition from 'pending' to 'completed'."
}
```

---

### Get Pending Count

Get the count of pending breakfast orders for a hotel.

**Endpoint:** `GET /api/room_services/{hotel_slug}/breakfast_orders/breakfast-pending-count/`

**URL Parameters:**
- `hotel_slug` (string, required) - Hotel identifier

**Response (200 OK):**

```json
{
  "count": 5
}
```

---

## Data Models

### BreakfastItem Model

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | integer | Auto | - | Unique identifier |
| `hotel` | integer | Auto | - | Foreign key to Hotel |
| `name` | string | Yes | - | Item name |
| `image` | string/url | No | null | Cloudinary image URL |
| `description` | string | Yes | - | Item description |
| `category` | string | No | "Mains" | Category (see choices above) |
| `quantity` | integer | No | 1 | Default quantity |
| `is_on_stock` | boolean | No | true | Item availability |

### BreakfastOrder Model

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | integer | Auto | - | Unique identifier |
| `hotel` | integer | Auto | - | Foreign key to Hotel (auto-assigned) |
| `room_number` | integer | Yes | - | Room for delivery |
| `status` | string | Auto | "pending" | Order status |
| `created_at` | datetime | Auto | - | Creation timestamp |
| `updated_at` | datetime | Auto | - | Last update timestamp |
| `delivery_time` | string | No | null | Delivery time slot |
| `items` | array | Yes | - | List of ordered items |

### BreakfastOrderItem Model (Nested)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | integer | Auto | - | Unique identifier |
| `item_id` | integer | Yes | - | Foreign key to BreakfastItem |
| `quantity` | integer | Yes | 1 | Quantity ordered |
| `notes` | string | No | null | Special instructions or preferences |

---

## Required Fields Summary

### To Create a Breakfast Order:

**Minimum Required:**
```json
{
  "room_number": 305,
  "items": [
    {
      "item_id": 1,
      "quantity": 1
    }
  ]
}
```

**Recommended (with delivery time):**
```json
{
  "room_number": 305,
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "item_id": 1,
      "quantity": 1
    }
  ]
}
```

**With Special Instructions (notes):**
```json
{
  "room_number": 305,
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "item_id": 1,
      "quantity": 1,
      "notes": "Extra crispy bacon, no mushrooms"
    },
    {
      "item_id": 3,
      "quantity": 2,
      "notes": "With ice"
    }
  ]
}
```

---

## Examples

### Frontend Implementation (React/JavaScript)

#### 1. Fetch Breakfast Menu

```javascript
const fetchBreakfastMenu = async (hotelSlug) => {
  const response = await fetch(
    `/api/room_services/${hotelSlug}/breakfast_items/`
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch breakfast menu');
  }
  
  return await response.json();
};

// Usage
const menu = await fetchBreakfastMenu('grand-hotel');
console.log('Breakfast menu:', menu);
```

#### 2. Submit Breakfast Order

```javascript
const submitBreakfastOrder = async (hotelSlug, orderData) => {
  const response = await fetch(
    `/api/room_services/${hotelSlug}/breakfast_orders/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(orderData)
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to submit order');
  }
  
  return await response.json();
};

// Usage
const newOrder = {
  room_number: 305,
  delivery_time: "8:00-8:30",
  items: [
    { 
      item_id: 1, 
      quantity: 1,
      notes: "No mushrooms please"
    },  // Full English Breakfast
    { 
      item_id: 3, 
      quantity: 2,
      notes: "Extra ice"
    },  // Orange Juice x2
    { 
      item_id: 5, 
      quantity: 1 
    }   // Toast
  ]
};

try {
  const order = await submitBreakfastOrder('grand-hotel', newOrder);
  console.log('Order created:', order);
  // Show success message to guest
  alert(`Breakfast order #${order.id} submitted successfully!`);
} catch (error) {
  console.error('Error:', error.message);
  alert('Failed to submit order. Please try again.');
}
```

#### 3. Get Breakfast Orders for Room

```javascript
const getRoomBreakfastOrders = async (hotelSlug, roomNumber) => {
  const response = await fetch(
    `/api/room_services/${hotelSlug}/breakfast_orders/?room_number=${roomNumber}`
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch orders');
  }
  
  return await response.json();
};

// Usage
const orders = await getRoomBreakfastOrders('grand-hotel', 305);
console.log('Room 305 breakfast orders:', orders);
```

#### 4. Update Order Status (Staff Only)

```javascript
const updateOrderStatus = async (hotelSlug, orderId, newStatus, token) => {
  const response = await fetch(
    `/api/room_services/${hotelSlug}/breakfast_orders/${orderId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ status: newStatus })
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to update order');
  }
  
  return await response.json();
};

// Usage (Kitchen staff accepting order)
try {
  const updated = await updateOrderStatus(
    'grand-hotel',
    42,
    'accepted',
    staffToken
  );
  console.log('Order accepted:', updated);
} catch (error) {
  console.error('Error:', error.message);
}
```

#### 5. Subscribe to Pusher Notifications (Kitchen Staff)

```javascript
import Pusher from 'pusher-js';

// Initialize Pusher
const pusher = new Pusher('YOUR_PUSHER_KEY', {
  cluster: 'YOUR_CLUSTER',
  encrypted: true
});

// Subscribe to kitchen staff channel
const staffId = getCurrentStaffId(); // Your staff ID
const hotelSlug = 'grand-hotel';
const channelName = `${hotelSlug}-staff-kitchen-${staffId}`;
const channel = pusher.subscribe(channelName);

// Listen for new breakfast orders
channel.bind('new-breakfast-order', (data) => {
  console.log('New breakfast order received:', data);
  
  // Show notification
  showNotification({
    title: '🍳 New Breakfast Order',
    body: `Room ${data.room_number} - Delivery at ${data.delivery_time}`,
    data: data
  });
  
  // Play sound alert
  playNotificationSound();
  
  // Update order list
  refreshOrderList();
});

console.log(`Subscribed to ${channelName}`);
```

#### 6. Complete Order Form Component (React)

```javascript
import React, { useState, useEffect } from 'react';

function BreakfastOrderForm({ hotelSlug, roomNumber }) {
  const [menu, setMenu] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [deliveryTime, setDeliveryTime] = useState('8:00-8:30');
  const [loading, setLoading] = useState(false);

  const timeSlots = [
    '7:00-8:00',
    '8:00-8:30',
    '8:30-9:00',
    '9:00-9:30',
    '9:30-10:00',
    '10:00-10:30'
  ];

  useEffect(() => {
    // Fetch menu
    fetch(`/api/room_services/${hotelSlug}/breakfast_items/`)
      .then(res => res.json())
      .then(data => setMenu(data))
      .catch(err => console.error('Failed to load menu:', err));
  }, [hotelSlug]);

  const handleItemToggle = (itemId) => {
    setSelectedItems(prev => {
      const exists = prev.find(i => i.item_id === itemId);
      if (exists) {
        return prev.filter(i => i.item_id !== itemId);
      } else {
        return [...prev, { item_id: itemId, quantity: 1, notes: '' }];
      }
    });
  };

  const handleQuantityChange = (itemId, quantity) => {
    setSelectedItems(prev =>
      prev.map(i =>
        i.item_id === itemId ? { ...i, quantity: parseInt(quantity) } : i
      )
    );
  };

  const handleNotesChange = (itemId, notes) => {
    setSelectedItems(prev =>
      prev.map(i =>
        i.item_id === itemId ? { ...i, notes: notes } : i
      )
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (selectedItems.length === 0) {
      alert('Please select at least one item');
      return;
    }

    setLoading(true);
    
    try {
      const orderData = {
        room_number: roomNumber,
        delivery_time: deliveryTime,
        items: selectedItems
      };

      const response = await fetch(
        `/api/room_services/${hotelSlug}/breakfast_orders/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(orderData)
        }
      );

      if (!response.ok) throw new Error('Failed to submit order');

      const order = await response.json();
      alert(`Order #${order.id} submitted successfully!`);
      
      // Reset form
      setSelectedItems([]);
      setDeliveryTime('8:00-8:30');
      
    } catch (error) {
      alert('Failed to submit order: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>In-Room Breakfast Order</h2>
      <p>Room: {roomNumber}</p>

      <div>
        <label>Delivery Time:</label>
        <select
          value={deliveryTime}
          onChange={(e) => setDeliveryTime(e.target.value)}
        >
          {timeSlots.map(slot => (
            <option key={slot} value={slot}>{slot}</option>
          ))}
        </select>
      </div>

      <div>
        <h3>Select Items:</h3>
        {menu.map(item => (
          <div key={item.id}>
            <label>
              <input
                type="checkbox"
                checked={selectedItems.some(i => i.item_id === item.id)}
                onChange={() => handleItemToggle(item.id)}
              />
              {item.name} - {item.category}
            </label>
            
            {selectedItems.some(i => i.item_id === item.id) && (
              <div>
                <input
                  type="number"
                  min="1"
                  placeholder="Qty"
                  value={selectedItems.find(i => i.item_id === item.id)?.quantity || 1}
                  onChange={(e) => handleQuantityChange(item.id, e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Special instructions (optional)"
                  value={selectedItems.find(i => i.item_id === item.id)?.notes || ''}
                  onChange={(e) => handleNotesChange(item.id, e.target.value)}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Order'}
      </button>
    </form>
  );
}

export default BreakfastOrderForm;
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request - Validation Error

```json
{
  "room_number": ["This field is required."],
  "items": ["This field is required."]
}
```

#### 400 Bad Request - Invalid Status Transition

```json
{
  "error": "Invalid status transition from 'accepted' to 'pending'."
}
```

#### 400 Bad Request - Invalid Item

```json
{
  "items": [
    {
      "item": ["This breakfast item does not belong to your hotel."]
    }
  ]
}
```

#### 404 Not Found - Hotel Not Found

```json
{
  "detail": "Not found."
}
```

#### 404 Not Found - Order Not Found

```json
{
  "detail": "Not found."
}
```

---

## Pusher Events

### Event: `new-breakfast-order`

**Sent to:** Kitchen Staff, Room Service Waiters

**Channel Pattern:**
- Kitchen: `{hotel_slug}-staff-kitchen-{staff_id}`
- Waiters: `{hotel_slug}-staff-room_service_waiter-{staff_id}`

**Payload:**
```json
{
  "order_id": 42,
  "room_number": 305,
  "delivery_time": "08:00:00",
  "created_at": "2025-11-12T07:30:00Z",
  "status": "pending"
}
```

### Event: `new-breakfast-delivery`

**Sent to:** Porters

**Channel Pattern:** `{hotel_slug}-staff-porter-{staff_id}`

**Payload:**
```json
{
  "order_id": 42,
  "room_number": 305,
  "delivery_time": "08:00:00",
  "created_at": "2025-11-12T07:30:00Z",
  "status": "pending"
}
```

---

## Best Practices

### 1. Validate Room Number Before Submission

```javascript
// Validate room PIN first
const validateRoomPin = async (hotelSlug, roomNumber, pin) => {
  const response = await fetch(
    `/api/room_services/${hotelSlug}/room/${roomNumber}/validate-pin/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin })
    }
  );
  
  const result = await response.json();
  return result.valid;
};

// Then submit order if valid
if (await validateRoomPin(hotelSlug, roomNumber, pin)) {
  await submitBreakfastOrder(hotelSlug, orderData);
}
```

### 2. Handle Time Slots Properly

Always use exact time slot format from the choices:

```javascript
// ✅ Correct
const deliveryTime = "8:00-8:30";

// ❌ Incorrect
const deliveryTime = "8:00 AM - 8:30 AM";
const deliveryTime = "08:00-08:30";
```

### 3. Show Order Confirmation

```javascript
const confirmOrder = (order) => {
  const itemList = order.items
    .map(i => `${i.quantity}x ${i.item.name}`)
    .join(', ');
    
  alert(
    `Order #${order.id} confirmed!\n` +
    `Room: ${order.room_number}\n` +
    `Delivery: ${order.delivery_time}\n` +
    `Items: ${itemList}`
  );
};
```

### 4. Filter Out-of-Stock Items

```javascript
const availableItems = menu.filter(item => item.is_on_stock);
```

### 5. Staff Dashboard - Real-Time Updates

```javascript
// Subscribe to multiple channels for comprehensive coverage
const subscribeToAllChannels = (hotelSlug, staffId, role) => {
  const pusher = new Pusher('YOUR_KEY', { cluster: 'YOUR_CLUSTER' });
  
  // Staff-specific channel
  const staffChannel = pusher.subscribe(
    `${hotelSlug}-staff-${role}-${staffId}`
  );
  
  staffChannel.bind('new-breakfast-order', handleNewOrder);
  staffChannel.bind('new-breakfast-delivery', handleNewDelivery);
  
  return () => {
    pusher.unsubscribe(`${hotelSlug}-staff-${role}-${staffId}`);
  };
};
```

---

## Notes

- **Hotel Context:** The hotel is automatically assigned from the URL `hotel_slug` parameter
- **Status Workflow:** Orders must progress through the workflow: pending → accepted → completed
- **Real-Time Notifications:** Pusher notifications are sent immediately after order creation
- **Staff Filtering:** Only on-duty staff members receive Pusher notifications
- **Time Slots:** Delivery times are optional but recommended for better service coordination
- **Item Validation:** Items are validated to ensure they belong to the correct hotel
- **Special Instructions:** Use the `notes` field in each item to add dietary restrictions, preferences, or special requests
- **Updated Timestamp:** The `updated_at` field is automatically updated when order status changes

---

## Related Documentation

- [Room Service Order API](./ROOM_SERVICE_ORDER_API_GUIDE.md)
- [Pusher Integration Guide](./PUSHER_INTEGRATION_GUIDE.md)
- [Staff Notification System](./STAFF_NOTIFICATIONS_GUIDE.md)

---

**Last Updated:** November 12, 2025  
**API Version:** v1  
**Maintained by:** HotelMate Backend Team
