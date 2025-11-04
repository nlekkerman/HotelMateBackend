# Breakfast Room Service API - Quick Reference

## 🚀 Quick Start

### Base URL
```
https://your-backend.com/room_services/
```

---

## 📋 Guest Endpoints (No Authentication Required)

### 1. Get Breakfast Menu
```http
GET /{hotel_slug}/room/{room_number}/breakfast/
```
**Returns**: List of available breakfast items

### 2. Validate PIN
```http
POST /{hotel_slug}/room/{room_number}/validate-pin/
Content-Type: application/json

{
  "pin": "abc1"
}
```
**Returns**: `{"valid": true}` or `{"valid": false}`

### 3. Save FCM Token
```http
POST /{hotel_slug}/room/{room_number}/save-fcm-token/
Content-Type: application/json

{
  "fcm_token": "firebase_device_token"
}
```

### 4. Create Order
```http
POST /{hotel_slug}/breakfast-orders/
Content-Type: application/json

{
  "room_number": 101,
  "delivery_time": "8:00-8:30",
  "items": [
    {"item_id": 1, "quantity": 2},
    {"item_id": 3, "quantity": 1}
  ]
}
```

### 5. View Guest Orders
```http
GET /{hotel_slug}/breakfast-orders/?room_number=101
```

### 6. Get Order Details
```http
GET /{hotel_slug}/breakfast-orders/{order_id}/
```

---

## 👨‍💼 Staff Endpoints

### 7. List All Pending Orders
```http
GET /{hotel_slug}/breakfast-orders/
Authorization: Bearer {staff_token}
```

### 8. Update Order Status
```http
PATCH /{hotel_slug}/breakfast-orders/{order_id}/
Content-Type: application/json
Authorization: Bearer {staff_token}

{
  "status": "accepted"
}
```
**Valid transitions**: 
- `pending` → `accepted`
- `accepted` → `completed`

### 9. Get Pending Count
```http
GET /{hotel_slug}/breakfast-orders/breakfast-pending-count/
Authorization: Bearer {staff_token}
```

---

## 📝 Request/Response Examples

### Create Order Request
```json
{
  "room_number": 101,
  "delivery_time": "8:00-8:30",
  "items": [
    {
      "item_id": 5,
      "quantity": 2
    },
    {
      "item_id": 12,
      "quantity": 1
    }
  ]
}
```

### Create Order Response (201)
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
        "id": 5,
        "name": "Scrambled Eggs",
        "image": "https://res.cloudinary.com/...",
        "description": "Fluffy scrambled eggs",
        "category": "Mains",
        "is_on_stock": true
      },
      "quantity": 2
    },
    {
      "id": 2,
      "item": {
        "id": 12,
        "name": "Orange Juice",
        "image": "https://res.cloudinary.com/...",
        "description": "Fresh orange juice",
        "category": "Drinks",
        "is_on_stock": true
      },
      "quantity": 1
    }
  ]
}
```

### Menu Response
```json
[
  {
    "id": 1,
    "hotel": 1,
    "name": "Scrambled Eggs",
    "image": "https://res.cloudinary.com/...",
    "description": "Fluffy scrambled eggs with butter",
    "category": "Mains",
    "quantity": 1,
    "is_on_stock": true
  },
  {
    "id": 2,
    "name": "Pancakes",
    "image": "https://res.cloudinary.com/...",
    "category": "Mains",
    "is_on_stock": true
  }
]
```

---

## ⏰ Delivery Time Slots

```javascript
const TIME_SLOTS = [
  "7:00-8:00",
  "8:00-8:30",
  "8:30-9:00",
  "9:00-9:30",
  "9:30-10:00",
  "10:00-10:30"
];
```

---

## 🏷️ Order Status Values

- `pending` - Order placed, waiting for staff
- `accepted` - Order accepted, being prepared
- `completed` - Order delivered to room

---

## 📱 Real-Time Channels (Pusher)

### Guest Channel
```
{hotel_slug}-room-{room_number}
```
**Events**:
- `order-status-update` - When staff changes order status

### Staff Channel (Kitchen)
```
{hotel_slug}-staff-{staff_id}-kitchen
```
**Events**:
- `new-breakfast-order` - New order received

### Staff Channel (Porter)
```
{hotel_slug}-staff-{staff_id}-porter
```
**Events**:
- `new-breakfast-delivery` - New order for delivery
- `breakfast-count-update` - Updated order count

---

## 🔔 FCM Push Notification Data

### Order Status Update (to Guest)
```json
{
  "type": "order_status_update",
  "order_id": "42",
  "room_number": "101",
  "new_status": "accepted",
  "old_status": "pending",
  "updated_at": "2025-11-04T10:35:00Z"
}
```

### New Breakfast Order (to Staff)
```json
{
  "type": "breakfast_order",
  "order_id": "42",
  "room_number": "101",
  "delivery_time": "8:00-8:30",
  "status": "pending",
  "click_action": "FLUTTER_NOTIFICATION_CLICK",
  "route": "/orders/breakfast"
}
```

---

## ❌ Error Responses

### Invalid PIN (401)
```json
{
  "valid": false
}
```

### Invalid Status Transition (400)
```json
{
  "error": "Invalid status transition from 'pending' to 'completed'."
}
```

### Room Not Found (404)
```json
{
  "detail": "Not found."
}
```

### Missing Required Fields (400)
```json
{
  "items": ["This field is required."],
  "delivery_time": ["This field is required."]
}
```

---

## 🔐 Authentication Notes

- **Guest endpoints**: No authentication required (PIN validation only)
- **Staff endpoints**: Requires Bearer token authentication
- **PIN format**: 4 characters (lowercase letters + digits)
- **Room validation**: PIN must match room's `guest_id_pin`

---

## 🎯 Frontend Integration Checklist

### Guest Flow
1. ✅ Scan QR code → extract `hotel_slug` and `room_number`
2. ✅ Fetch breakfast menu
3. ✅ Guest selects items (add to cart)
4. ✅ Validate PIN before checkout
5. ✅ Request FCM token permission
6. ✅ Save FCM token to backend
7. ✅ Select delivery time
8. ✅ Submit order
9. ✅ Show confirmation
10. ✅ Subscribe to Pusher channel for updates
11. ✅ Display order status in real-time

### Staff Flow
1. ✅ Authenticate staff member
2. ✅ Fetch pending breakfast orders
3. ✅ Subscribe to staff Pusher channel
4. ✅ Display order list with details
5. ✅ Allow status updates (Accept/Complete)
6. ✅ Show order count badge
7. ✅ Receive FCM notifications when app closed

---

## 🧪 Test with cURL

### Get Menu
```bash
curl -X GET \
  "https://your-backend.com/room_services/grand-hotel/room/101/breakfast/"
```

### Validate PIN
```bash
curl -X POST \
  "https://your-backend.com/room_services/grand-hotel/room/101/validate-pin/" \
  -H "Content-Type: application/json" \
  -d '{"pin": "abc1"}'
```

### Create Order
```bash
curl -X POST \
  "https://your-backend.com/room_services/grand-hotel/breakfast-orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "room_number": 101,
    "delivery_time": "8:00-8:30",
    "items": [
      {"item_id": 1, "quantity": 2}
    ]
  }'
```

### Update Status (Staff)
```bash
curl -X PATCH \
  "https://your-backend.com/room_services/grand-hotel/breakfast-orders/42/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_STAFF_TOKEN" \
  -d '{"status": "accepted"}'
```

---

## 📞 Need Help?

- **Full Implementation Guide**: See `FRONTEND_BREAKFAST_IMPLEMENTATION.md`
- **Backend Issues**: Check Django logs
- **Pusher Issues**: Verify credentials in settings
- **FCM Issues**: Check Firebase console and credentials

---

**Last Updated**: November 4, 2025
