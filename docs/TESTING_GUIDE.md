# 🧪 Testing Guide - Breakfast Ordering System

## Complete Testing Checklist for Frontend & Backend

---

## 🎯 Test Environment Setup

### Prerequisites
- Backend server running
- Database populated with test data
- Pusher credentials configured
- Firebase project set up
- Test hotel and rooms created

### Test Data Requirements

**Hotel:**
- Slug: `test-hotel`
- Name: Test Hotel

**Room:**
- Room number: `101`
- Guest PIN: `abc1`
- Hotel: test-hotel

**Breakfast Items:**
- At least 2 items per category
- Mix of in-stock and out-of-stock items
- Valid images (Cloudinary URLs)

---

## 📋 Backend API Testing

### Test 1: Get Breakfast Menu

**Endpoint**: `GET /room_services/test-hotel/room/101/breakfast/`

**Expected Response (200)**:
```json
[
  {
    "id": 1,
    "hotel": 1,
    "name": "Scrambled Eggs",
    "image": "https://...",
    "description": "...",
    "category": "Mains",
    "is_on_stock": true
  }
]
```

**Test Cases**:
- ✅ Returns all breakfast items for hotel
- ✅ Only returns items with `is_on_stock=true`
- ✅ Includes all required fields
- ✅ Works without authentication
- ❌ Returns 404 for invalid hotel slug
- ❌ Returns 404 for non-existent room

**cURL Test**:
```bash
curl -X GET "http://localhost:8000/room_services/test-hotel/room/101/breakfast/"
```

---

### Test 2: Validate PIN (Valid)

**Endpoint**: `POST /room_services/test-hotel/room/101/validate-pin/`

**Request**:
```json
{
  "pin": "abc1"
}
```

**Expected Response (200)**:
```json
{
  "valid": true
}
```

**Test Cases**:
- ✅ Returns valid=true for correct PIN
- ✅ Case-insensitive (ABC1 = abc1)
- ❌ Returns valid=false for wrong PIN
- ❌ Returns 404 for invalid room

**cURL Test**:
```bash
curl -X POST "http://localhost:8000/room_services/test-hotel/room/101/validate-pin/" \
  -H "Content-Type: application/json" \
  -d '{"pin": "abc1"}'
```

---

### Test 3: Validate PIN (Invalid)

**Request**:
```json
{
  "pin": "wrong"
}
```

**Expected Response (401)**:
```json
{
  "valid": false
}
```

---

### Test 4: Save FCM Token

**Endpoint**: `POST /room_services/test-hotel/room/101/save-fcm-token/`

**Request**:
```json
{
  "fcm_token": "test_fcm_token_123"
}
```

**Expected Response (200)**:
```json
{
  "success": true,
  "message": "FCM token saved successfully"
}
```

**Test Cases**:
- ✅ Saves FCM token to room
- ✅ Updates existing token if called again
- ❌ Returns 400 if fcm_token missing
- ❌ Returns 404 for invalid room

**cURL Test**:
```bash
curl -X POST "http://localhost:8000/room_services/test-hotel/room/101/save-fcm-token/" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token": "test_token_123"}'
```

---

### Test 5: Create Breakfast Order

**Endpoint**: `POST /room_services/test-hotel/breakfast-orders/`

**Request**:
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

**Expected Response (201)**:
```json
{
  "id": 1,
  "hotel": 1,
  "room_number": 101,
  "status": "pending",
  "created_at": "2025-11-04T10:30:00Z",
  "delivery_time": "8:00-8:30",
  "items": [...]
}
```

**Test Cases**:
- ✅ Creates order with pending status
- ✅ Saves all order items with quantities
- ✅ Returns complete order with nested items
- ✅ Triggers notifications (Pusher + FCM)
- ❌ Returns 400 if items array empty
- ❌ Returns 400 if delivery_time missing
- ❌ Returns 400 if room_number missing
- ❌ Returns 404 if item_id doesn't exist

**cURL Test**:
```bash
curl -X POST "http://localhost:8000/room_services/test-hotel/breakfast-orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "room_number": 101,
    "delivery_time": "8:00-8:30",
    "items": [
      {"item_id": 1, "quantity": 2}
    ]
  }'
```

---

### Test 6: Get Guest Orders

**Endpoint**: `GET /room_services/test-hotel/breakfast-orders/?room_number=101`

**Expected Response (200)**:
```json
[
  {
    "id": 1,
    "room_number": 101,
    "status": "pending",
    "delivery_time": "8:00-8:30",
    "items": [...]
  }
]
```

**Test Cases**:
- ✅ Returns only orders for specified room
- ✅ Excludes completed orders by default
- ✅ Returns empty array if no orders
- ✅ Includes all order details

---

### Test 7: Get Order Details

**Endpoint**: `GET /room_services/test-hotel/breakfast-orders/1/`

**Expected Response (200)**:
```json
{
  "id": 1,
  "hotel": 1,
  "room_number": 101,
  "status": "pending",
  "created_at": "2025-11-04T10:30:00Z",
  "delivery_time": "8:00-8:30",
  "items": [...]
}
```

**Test Cases**:
- ✅ Returns complete order details
- ✅ Includes nested items with quantities
- ❌ Returns 404 for non-existent order ID

---

### Test 8: Update Order Status (Staff)

**Endpoint**: `PATCH /room_services/test-hotel/breakfast-orders/1/`

**Request**:
```json
{
  "status": "accepted"
}
```

**Expected Response (200)**:
```json
{
  "id": 1,
  "status": "accepted",
  ...
}
```

**Test Cases**:
- ✅ Updates status from pending to accepted
- ✅ Updates status from accepted to completed
- ✅ Triggers guest notification (Pusher + FCM)
- ❌ Returns 400 for invalid transition (pending→completed)
- ❌ Returns 400 for invalid status value

**Valid Transitions**:
- `pending` → `accepted` ✅
- `accepted` → `completed` ✅
- `pending` → `completed` ❌
- `completed` → anything ❌

**cURL Test**:
```bash
curl -X PATCH "http://localhost:8000/room_services/test-hotel/breakfast-orders/1/" \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted"}'
```

---

### Test 9: Get Pending Count (Staff)

**Endpoint**: `GET /room_services/test-hotel/breakfast-orders/breakfast-pending-count/`

**Expected Response (200)**:
```json
{
  "count": 3
}
```

**Test Cases**:
- ✅ Returns accurate count of pending orders
- ✅ Updates in real-time as orders change
- ✅ Only counts orders for specified hotel

---

## 🔔 Pusher Real-Time Testing

### Test 10: Guest Order Status Updates

**Setup**:
1. Create an order (Order #1)
2. Subscribe to channel: `test-hotel-room-101`
3. Listen for event: `order-status-update`

**Actions**:
1. Staff updates order status to "accepted"

**Expected Event**:
```json
{
  "updated_order_id": 1,
  "room_number": 101,
  "old_status": "pending",
  "new_status": "accepted",
  "updated_at": "2025-11-04T10:35:00Z"
}
```

**Test Cases**:
- ✅ Guest receives real-time update
- ✅ Correct order details in payload
- ✅ Event fires immediately after update
- ✅ Multiple subscribers receive same event

---

### Test 11: Staff New Order Notifications

**Setup**:
1. Subscribe as kitchen staff
2. Channel: `test-hotel-staff-{staff_id}-kitchen`
3. Listen for event: `new-breakfast-order`

**Actions**:
1. Guest creates new order

**Expected Event**:
```json
{
  "order_id": 1,
  "room_number": 101,
  "delivery_time": "8:00-8:30",
  "created_at": "2025-11-04T10:30:00Z",
  "status": "pending"
}
```

**Test Cases**:
- ✅ Kitchen staff receives notification
- ✅ Porters receive notification
- ✅ Waiters receive notification
- ✅ Only on-duty staff notified

---

## 📱 Firebase FCM Testing

### Test 12: Guest Push Notification

**Setup**:
1. Guest device with FCM token saved
2. Browser/app closed (background)

**Actions**:
1. Staff updates order status

**Expected**:
- Push notification appears on device
- Title: "🔔 Order Status Update"
- Body: "Your order #1 is now accepted"
- Clicking opens app to order details

**Test Cases**:
- ✅ Notification received in background
- ✅ Notification received when app closed
- ✅ Correct title and body text
- ✅ Data payload correct
- ✅ Click action works

---

### Test 13: Staff Push Notification

**Setup**:
1. Staff device with FCM token
2. App closed

**Actions**:
1. Guest creates new order

**Expected**:
- Push notification appears
- Title: "🍳 New Breakfast Order"
- Body: "Room 101 - Delivery: 8:00-8:30"
- Route to orders screen

**Test Cases**:
- ✅ Kitchen staff receives notification
- ✅ Porters receive notification
- ✅ Only on-duty staff notified
- ✅ Correct order details in notification

---

## 🖥️ Frontend UI Testing

### Test 14: QR Code Scanning

**Test Cases**:
- ✅ Camera permission requested
- ✅ QR code correctly parsed
- ✅ Extracts hotel_slug and room_number
- ✅ Redirects to PIN screen
- ❌ Shows error for invalid QR format
- ✅ Works on mobile and desktop

**Manual Test**:
1. Scan test QR code
2. Verify correct hotel and room extracted
3. Verify navigation to PIN screen

---

### Test 15: PIN Validation UI

**Test Cases**:
- ✅ Input accepts 4 characters max
- ✅ Submit button disabled until 4 chars entered
- ✅ Shows error for invalid PIN
- ✅ Clears input after error
- ✅ Proceeds to menu on valid PIN
- ✅ Loading state during validation
- ✅ Case-insensitive input

**Manual Test**:
1. Enter wrong PIN → See error
2. Enter correct PIN → Go to menu

---

### Test 16: Menu Display

**Test Cases**:
- ✅ All categories displayed
- ✅ Items grouped by category
- ✅ Images load correctly
- ✅ Only in-stock items shown
- ✅ Add to cart button works
- ✅ Cart icon updates with count
- ✅ Responsive on mobile

**Manual Test**:
1. Browse all categories
2. Verify images load
3. Add items to cart
4. Check cart count updates

---

### Test 17: Cart Management

**Test Cases**:
- ✅ Items added to cart
- ✅ Quantity can be updated
- ✅ Items can be removed (quantity = 0)
- ✅ Cart persists during session
- ✅ Cart total calculated correctly
- ✅ Empty cart shows message

**Manual Test**:
1. Add 3 items to cart
2. Update quantity of item
3. Remove item by setting quantity to 0
4. Verify cart updates correctly

---

### Test 18: Checkout Flow

**Test Cases**:
- ✅ Delivery time required
- ✅ All time slots available
- ✅ Order summary shows correct items
- ✅ Submit button disabled until time selected
- ✅ Loading state during submission
- ✅ Success message after submission
- ✅ Cart cleared after order

**Manual Test**:
1. Proceed to checkout with items
2. Try to submit without time → Disabled
3. Select time slot
4. Submit order → Success

---

### Test 19: Order Tracking

**Test Cases**:
- ✅ Order confirmation displayed
- ✅ Order number shown
- ✅ Status badge visible
- ✅ Real-time status updates work
- ✅ Status changes reflected in UI
- ✅ Correct status colors/labels

**Manual Test**:
1. Create order
2. Have staff update status
3. Verify UI updates without refresh
4. Check status badge changes

---

### Test 20: Error Handling

**Test Cases**:
- ✅ Network error shows message
- ✅ Invalid PIN shows error
- ✅ Empty cart prevents checkout
- ✅ API error shows user-friendly message
- ✅ Retry option available
- ✅ Loading states everywhere

**Manual Test**:
1. Disconnect network → See error
2. Enter wrong PIN → See error
3. Try checkout with empty cart → Blocked
4. Retry after error → Works

---

## 🔐 Security Testing

### Test 21: PIN Security

**Test Cases**:
- ✅ PIN validated on backend only
- ✅ Cannot bypass PIN validation
- ✅ Cannot access other rooms' orders
- ✅ Cannot modify other rooms' orders
- ❌ Direct API call without PIN fails

**Manual Test**:
1. Try to access API without PIN validation
2. Try to get orders for different room
3. Verify all blocked

---

### Test 22: Multi-Tenancy

**Test Cases**:
- ✅ Orders scoped to correct hotel
- ✅ Cannot access other hotels' data
- ✅ Menu items filtered by hotel
- ✅ Staff sees only their hotel's orders

**Manual Test**:
1. Create orders in Hotel A
2. Try to access from Hotel B context
3. Verify isolation

---

## 📊 Performance Testing

### Test 23: Load Time

**Metrics**:
- Menu load: < 2 seconds
- Order submission: < 1 second
- PIN validation: < 500ms
- Image load: Progressive

**Test**:
1. Measure API response times
2. Check image loading
3. Test on slow network (3G)

---

### Test 24: Concurrent Orders

**Test**:
1. Create 10 orders simultaneously
2. Verify all saved correctly
3. Check notifications sent to all staff
4. No duplicate notifications

---

## ✅ Checklist Summary

### Backend API
- [ ] All endpoints return correct status codes
- [ ] Request validation works
- [ ] Error messages clear and helpful
- [ ] CORS configured correctly
- [ ] Database transactions work
- [ ] Signals trigger correctly

### Real-Time (Pusher)
- [ ] Channels connect successfully
- [ ] Events trigger immediately
- [ ] Correct data in payloads
- [ ] Only intended recipients notified
- [ ] Reconnection works after disconnect

### Push Notifications (FCM)
- [ ] Tokens saved correctly
- [ ] Notifications delivered
- [ ] Correct title and body
- [ ] Data payload correct
- [ ] Click actions work

### Frontend
- [ ] QR scanning works
- [ ] PIN validation works
- [ ] Menu displays correctly
- [ ] Cart management works
- [ ] Orders submit successfully
- [ ] Real-time updates work
- [ ] Push notifications work
- [ ] Error handling complete
- [ ] Loading states everywhere
- [ ] Mobile responsive

### Security
- [ ] PIN validated on backend
- [ ] Data scoped to correct hotel/room
- [ ] No unauthorized access
- [ ] FCM tokens secure

### Performance
- [ ] Fast load times
- [ ] Handles concurrent users
- [ ] Images optimized
- [ ] No memory leaks

---

## 🐛 Bug Report Template

When reporting issues:

```markdown
**Environment**: Production / Staging / Development
**User Type**: Guest / Kitchen Staff / Porter / Waiter
**Device**: Desktop / Mobile / Tablet
**Browser**: Chrome / Safari / Firefox / etc.

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:


**Actual Behavior**:


**Screenshots**:


**Console Errors**:


**API Response** (if applicable):

```

---

## 🎯 Acceptance Criteria

### MVP Launch Checklist
- [ ] Guests can scan QR and order breakfast
- [ ] Staff receive real-time notifications
- [ ] Orders display correctly in dashboard
- [ ] Status updates work and notify guests
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Security validated

---

**Testing Complete! Ready for production when all tests pass ✅**
