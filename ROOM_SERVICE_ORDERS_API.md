# Room Service Orders API - Frontend Integration Guide

## Overview

Complete API documentation for managing room service orders with real-time updates, pagination, and search capabilities.

---

## 📡 Real-Time Updates

### Pusher Notifications

When an order status changes, **ALL connected clients** receive a real-time update via Pusher.

**Channel Format:**
```
{hotel-slug}-room-{room-number}
```

**Event Name:**
```
order-status-update
```

**Payload:**
```javascript
{
  "updated_order_id": 505,
  "room_number": 101,
  "old_status": "pending",
  "new_status": "accepted",
  "updated_at": "2025-11-03T11:21:25.218875+00:00",
  "all_orders": [
    // ALL active orders for the hotel (not just this room)
    {
      "id": 505,
      "hotel": 1,
      "room_number": 101,
      "status": "accepted",
      "created_at": "2025-11-03T11:21:11.862395+00:00",
      "updated_at": "2025-11-03T11:21:25.218875+00:00",
      "total_price": 13.48,
      "items": [...]
    },
    {
      "id": 504,
      "room_number": 102,
      "status": "pending",
      ...
    }
  ]
}
```

**Frontend Implementation:**
```javascript
// Subscribe to guest room channel
const channel = pusher.subscribe(`hotel-killarney-room-101`);

channel.bind('order-status-update', (data) => {
  console.log('Order updated:', data.updated_order_id);
  console.log('New status:', data.new_status);
  
  // Update ALL orders in your state
  setAllOrders(data.all_orders);
  
  // Or filter for this room
  const myOrders = data.all_orders.filter(
    order => order.room_number === 101
  );
  setMyOrders(myOrders);
});
```

---

## � Active Orders (Staff/Guest)

**Endpoint:**
```
GET /api/room_services/{hotel_slug}/orders/
```

**Purpose:** Get active orders only (pending + accepted). Completed orders are automatically excluded.

**Use this for:**
- Staff dashboard showing current orders
- Kitchen display
- Guest view of their active orders

### Response Format

```json
[
  {
    "id": 505,
    "hotel": 1,
    "room_number": 101,
    "status": "accepted",
    "total_price": 13.48,
    "created_at": "2025-11-03T11:21:11.862395+00:00",
    "updated_at": "2025-11-03T11:21:25.218875+00:00",
    "items": [
      {
        "id": 123,
        "item": {
          "id": 5,
          "name": "Club Sandwich",
          "price": 8.99
        },
        "quantity": 1
      }
    ]
  }
]
```

---

## 📜 Order History (Completed Orders)

**Endpoint:**
```
GET /api/room_services/{hotel_slug}/orders/order-history/
```

**Purpose:** Get completed orders ONLY with filtering by room and date range

**Use this for:**
- Order history reports
- Room-specific order history
- Date-based filtering
- Historical data analysis

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `page_size` | integer | No | 20 | Orders per page |
| `room_number` | integer | No | - | Filter by specific room |
| `date_from` | string | No | - | Filter from date (YYYY-MM-DD) |
| `date_to` | string | No | - | Filter to date (YYYY-MM-DD) |

### Examples

**Get all completed orders:**
```javascript
GET /api/room_services/hotel-killarney/orders/order-history/
```

**Get room 101 history:**
```javascript
GET /api/room_services/hotel-killarney/orders/order-history/?room_number=101
```

**Get orders in date range:**
```javascript
GET /api/room_services/hotel-killarney/orders/order-history/?date_from=2025-11-01&date_to=2025-11-03
```

**Combined filters:**
```javascript
GET /api/room_services/hotel-killarney/orders/order-history/?room_number=101&date_from=2025-11-01&page=1&page_size=10
```

### Response Format

```json
{
  "pagination": {
    "total_orders": 7,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  },
  "filters": {
    "room_number": "101",
    "date_from": "2025-11-01",
    "date_to": "2025-11-03"
  },
  "orders": [
    {
      "id": 500,
      "hotel": 1,
      "room_number": 101,
      "status": "completed",
      "total_price": 25.50,
      "created_at": "2025-11-02T14:30:00.000000+00:00",
      "updated_at": "2025-11-02T15:00:00.000000+00:00",
      "items": [...]
    }
  ]
}
```

---

## �🔍 Get All Orders Summary (Staff)

**Endpoint:**
```
GET /api/room_services/{hotel_slug}/orders/all-orders-summary/
```

**Purpose:** Get paginated list of all orders with statistics for a specific hotel

**⚠️ Important:** This endpoint is hotel-scoped. Each hotel only sees their own orders.

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `page_size` | integer | No | 20 | Orders per page |
| `room_number` | integer | No | - | Filter by specific room |
| `status` | string | No | - | Filter by status (pending/accepted/completed) |
| `include_completed` | boolean | No | true | Include completed orders (true) or exclude them (false) |

### Examples

**Get all orders (first page, 20 per page):**
```javascript
GET /api/room_services/hotel-killarney/orders/all-orders-summary/
// Returns ALL orders including completed ones (default)
```

**Get only active orders (exclude completed):**
```javascript
GET /api/room_services/hotel-killarney/orders/all-orders-summary/?include_completed=false
```

**Search orders for room 101:**
```javascript
GET /api/room_services/hotel-killarney/orders/all-orders-summary/?room_number=101
```

**Get only pending orders:**
```javascript
GET /api/room_services/hotel-killarney/orders/all-orders-summary/?status=pending
```

**Pagination (page 2, 10 per page):**
```javascript
GET /api/room_services/hotel-killarney/orders/all-orders-summary/?page=2&page_size=10
```

**Combined filters:**
```javascript
GET /api/room_services/hotel-killarney/orders/all-orders-summary/?room_number=101&status=pending&page=1&page_size=5&include_completed=false
```

### Response Format

```json
{
  "pagination": {
    "total_orders": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  },
  "filters": {
    "room_number": null,
    "status": null,
    "include_completed": true
  },
  "status_breakdown": [
    { "status": "pending", "count": 12 },
    { "status": "accepted", "count": 8 },
    { "status": "completed", "count": 5 }
  ],
  "orders_by_room": [
    {
      "room_number": 101,
      "order_count": 2,
      "orders": [
        {
          "id": 505,
          "status": "accepted",
          "total_price": 13.48,
          "created_at": "2025-11-03T11:21:11.862395+00:00",
          "updated_at": "2025-11-03T11:21:25.218875+00:00"
        }
      ]
    },
    {
      "room_number": 102,
      "order_count": 1,
      "orders": [...]
    }
  ],
  "orders": [
    {
      "id": 505,
      "hotel": 1,
      "room_number": 101,
      "status": "accepted",
      "created_at": "2025-11-03T11:21:11.862395+00:00",
      "updated_at": "2025-11-03T11:21:25.218875+00:00",
      "total_price": 13.48,
      "items": [
        {
          "id": 1,
          "item": {
            "id": 10,
            "name": "Caesar Salad",
            "price": "8.99",
            "description": "Fresh romaine lettuce...",
            "category": "Starters",
            "image": "https://..."
          },
          "item_price": "8.99",
          "quantity": 1,
          "notes": "No croutons"
        }
      ]
    }
  ]
}
```

---

## 💻 Frontend Implementation Examples

### 1. Fetch All Orders with Pagination

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

const OrdersSummary = () => {
  const [orders, setOrders] = useState([]);
  const [pagination, setPagination] = useState({});
  const [statusBreakdown, setStatusBreakdown] = useState([]);
  const [filters, setFilters] = useState({
    room_number: '',
    status: '',
    page: 1,
    page_size: 20
  });
  const [loading, setLoading] = useState(false);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', filters.page);
      params.append('page_size', filters.page_size);
      
      if (filters.room_number) {
        params.append('room_number', filters.room_number);
      }
      if (filters.status) {
        params.append('status', filters.status);
      }

      const response = await axios.get(
        `/api/room_services/hotel-killarney/orders/all-orders-summary/?${params}`
      );

      setOrders(response.data.orders);
      setPagination(response.data.pagination);
      setStatusBreakdown(response.data.status_breakdown);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [filters]);

  return (
    <div>
      {/* Filters */}
      <div className="filters">
        <input
          type="number"
          placeholder="Room Number"
          value={filters.room_number}
          onChange={(e) => setFilters({
            ...filters, 
            room_number: e.target.value,
            page: 1
          })}
        />

        <select
          value={filters.status}
          onChange={(e) => setFilters({
            ...filters, 
            status: e.target.value,
            page: 1
          })}
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="completed">Completed</option>
        </select>

        <button onClick={fetchOrders}>
          🔍 Search
        </button>
      </div>

      {/* Status Summary */}
      <div className="status-summary">
        <h3>Status Breakdown</h3>
        {statusBreakdown.map(item => (
          <div key={item.status}>
            {item.status}: {item.count} orders
          </div>
        ))}
      </div>

      {/* Orders List */}
      <div className="orders-list">
        {loading ? (
          <p>Loading...</p>
        ) : (
          orders.map(order => (
            <div key={order.id} className="order-card">
              <h4>Order #{order.id} - Room {order.room_number}</h4>
              <p>Status: {order.status}</p>
              <p>Total: ${order.total_price}</p>
              <div className="items">
                {order.items.map(item => (
                  <div key={item.id}>
                    {item.quantity}x {item.item.name} - ${item.item_price}
                    {item.notes && <p>Note: {item.notes}</p>}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          disabled={!pagination.has_previous}
          onClick={() => setFilters({...filters, page: filters.page - 1})}
        >
          Previous
        </button>
        
        <span>
          Page {pagination.page} of {pagination.total_pages} 
          ({pagination.total_orders} total orders)
        </span>
        
        <button
          disabled={!pagination.has_next}
          onClick={() => setFilters({...filters, page: filters.page + 1})}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default OrdersSummary;
```

### 2. Real-Time Updates Integration

```javascript
import { useEffect, useState } from 'react';
import { useGuestPusher } from '@/hooks/useGuestPusher';

const OrdersWithRealTime = () => {
  const [orders, setOrders] = useState([]);
  
  // Subscribe to Pusher updates
  useEffect(() => {
    const channel = pusher.subscribe('hotel-killarney-room-101');
    
    channel.bind('order-status-update', (data) => {
      console.log('📦 Order status updated:', data);
      
      // Update all orders from real-time data
      setOrders(data.all_orders);
      
      // Show notification
      toast.success(
        `Order #${data.updated_order_id} is now ${data.new_status}`
      );
    });
    
    return () => {
      channel.unbind_all();
      pusher.unsubscribe('hotel-killarney-room-101');
    };
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchOrders();
  }, []);

  return (
    <div>
      {/* Display orders that auto-update via Pusher */}
      {orders.map(order => (
        <OrderCard key={order.id} order={order} />
      ))}
    </div>
  );
};
```

### 3. Staff Dashboard Button

```javascript
import { useState } from 'react';
import { Button, Modal } from '@/components/ui';

const StaffDashboard = () => {
  const [showOrdersSummary, setShowOrdersSummary] = useState(false);
  
  return (
    <div className="staff-dashboard">
      <Button onClick={() => setShowOrdersSummary(true)}>
        📊 View All Orders Summary
      </Button>
      
      <Modal 
        open={showOrdersSummary} 
        onClose={() => setShowOrdersSummary(false)}
        title="All Orders Summary"
      >
        <OrdersSummary />
      </Modal>
    </div>
  );
};
```

---

## 🎯 Use Cases

### For Guests
- View their own orders in real-time
- Get notifications when order status changes
- See order history

### For Staff (Porters/Waiters/Kitchen)
- View all pending orders across all rooms
- Filter orders by room number
- Filter orders by status
- Monitor order statistics
- Handle pagination for large order volumes

### For Managers
- See complete order overview
- Monitor order statistics by status
- Track orders by room
- Export data for analysis

---

## ⚡ Performance Notes

- **Default page size:** 20 orders
- **Maximum recommended page size:** 100 orders
- **Excludes completed orders** by default to reduce payload
- **Real-time updates** include ALL active orders (be mindful in large hotels)
- **Pagination info** helps build efficient UI

---

## 🔒 Security

- All endpoints respect hotel-level permissions
- Staff can only see orders for their assigned hotel
- Guests can only see orders for their room (via room number filtering)

---

## 📝 Summary

**All endpoints are hotel-scoped using `{hotel_slug}` in the URL:**

| Feature | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Get All Orders Summary | `/{hotel_slug}/orders/all-orders-summary/` | GET | Paginated list with filters |
| Get Order List | `/{hotel_slug}/orders/` | GET | List all orders for hotel |
| Create Order | `/{hotel_slug}/orders/` | POST | Create new order |
| Get Order Detail | `/{hotel_slug}/orders/{id}/` | GET | Get specific order |
| Update Order Status | `/{hotel_slug}/orders/{id}/` | PATCH | Update order (status change) |
| Get Pending Count | `/{hotel_slug}/orders/pending-count/` | GET | Count of pending orders |
| Real-time Updates | Pusher channel | - | Instant updates on status change |

**Hotel Isolation:**
- Each hotel only sees/manages their own orders
- Hotel slug is required in all URLs
- Orders are automatically filtered by hotel
- Real-time updates are scoped to specific hotel

---

## ✅ Testing Checklist

- [ ] Fetch orders without filters (default pagination)
- [ ] Search orders by room number
- [ ] Filter orders by status
- [ ] Navigate between pages
- [ ] Receive real-time Pusher updates
- [ ] Update order list when Pusher event received
- [ ] Display status breakdown statistics
- [ ] Show orders grouped by room

---

**Implementation Complete!** 🎉

Use this API to build a comprehensive orders management interface for both guests and staff.
