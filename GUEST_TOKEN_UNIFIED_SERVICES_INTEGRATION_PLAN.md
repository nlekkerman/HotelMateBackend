# Guest Token Unified Integration Plan
## Single Token Access for Room Services, Chat & Breakfast Orders

### 🎯 **Vision**
Use the existing `GuestBookingToken` as a **single source of truth** for all guest services:
- ✅ Booking status & management 
- 🛎️ Room services & breakfast orders
- 💬 Guest chat with staff
- 🔄 Real-time notifications via Pusher

---

## 🏗️ **Current State Analysis**

### ✅ **Already Implemented**
- `GuestBookingToken` model with secure token generation
- Pusher authentication for booking channels 
- Token validation with `validate_token()` method
- Booking management functionality

### 🚧 **Needs Integration**
- Room service orders
- Breakfast orders  
- Guest chat system
- Cross-service token validation

---

## 📋 **Implementation Plan**

### **Phase 1: Extend GuestBookingToken Model**

#### **File**: `hotel/models.py`
```python
class GuestBookingToken(models.Model):
    # ... existing fields ...
    
    # Extended purposes
    PURPOSE_CHOICES = [
        ('STATUS', 'Booking Status Access'),
        ('PRECHECKIN', 'Pre-checkin Process'),
        ('ROOM_SERVICES', 'Room Service Orders'),  # NEW
        ('CHAT', 'Guest Chat Access'),            # NEW
        ('FULL_ACCESS', 'All Guest Services'),    # NEW - Recommended
    ]
    
    # New permission fields
    can_order_services = models.BooleanField(
        default=True,
        help_text="Allow guest to place room service orders"
    )
    can_chat = models.BooleanField(
        default=True, 
        help_text="Allow guest to chat with staff"
    )
    
    @classmethod
    def generate_full_access_token(cls, booking, expires_days=None):
        """Generate token with access to all guest services"""
        return cls.generate_token(
            booking=booking,
            purpose='FULL_ACCESS',
            expires_days=expires_days
        )
```

### **Phase 2: Room Service Integration**

#### **File**: `room_services/guest_views.py` (NEW)
```python
class GuestRoomServiceOrderView(APIView):
    """
    Guest endpoint to place room service orders using booking token
    POST /api/public/hotel/{hotel_slug}/room-services/order/
    """
    permission_classes = [AllowAny]
    
    def post(self, request, hotel_slug):
        # Validate guest token
        raw_token = request.data.get('guest_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not raw_token:
            return Response({'error': 'Guest token required'}, status=401)
        
        # Get booking from token
        token_obj = GuestBookingToken.validate_token(raw_token)
        if not token_obj or token_obj.hotel.slug != hotel_slug:
            return Response({'error': 'Invalid token'}, status=403)
        
        # Check permissions
        if not token_obj.can_order_services:
            return Response({'error': 'Room service access disabled'}, status=403)
        
        booking = token_obj.booking
        
        # Validate guest can order (must be checked in)
        if not booking.checked_in_at or booking.checked_out_at:
            return Response({'error': 'Room service only available during stay'}, status=400)
        
        # Process order
        items = request.data.get('items', [])
        order = self._create_room_service_order(booking, items)
        
        # Send real-time notification to staff
        from notifications.notification_manager import notification_manager
        notification_manager.notify_room_service_order_created(order)
        
        return Response({
            'success': True,
            'order_id': order.id,
            'total_amount': str(order.total_amount),
            'estimated_delivery': order.estimated_delivery_time
        })
```

#### **File**: `room_services/models.py` (EXTEND)
```python
class RoomServiceOrder(models.Model):
    # ... existing fields ...
    
    # Link to booking instead of just room
    booking = models.ForeignKey(
        'hotel.RoomBooking',
        on_delete=models.CASCADE,
        related_name='room_service_orders',
        help_text="Guest booking that placed this order"
    )
    
    # Token tracking
    ordered_via_token = models.ForeignKey(
        'hotel.GuestBookingToken',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="Token used to place this order"
    )
```

### **Phase 3: Breakfast Order Integration**

#### **File**: `room_services/breakfast_views.py` (NEW)
```python
class GuestBreakfastOrderView(APIView):
    """
    Guest endpoint for breakfast orders using booking token
    POST /api/public/hotel/{hotel_slug}/breakfast/order/
    """
    
    def post(self, request, hotel_slug):
        # Same token validation pattern
        token_obj = self._validate_guest_token(request, hotel_slug)
        booking = token_obj.booking
        
        # Breakfast-specific validation
        delivery_date = request.data.get('delivery_date')
        if not self._can_order_breakfast(booking, delivery_date):
            return Response({'error': 'Breakfast not available for selected date'}, status=400)
        
        # Create breakfast order
        breakfast_items = request.data.get('items', [])
        order = BreakfastOrder.objects.create(
            booking=booking,
            delivery_date=delivery_date,
            ordered_via_token=token_obj,
            status='PENDING'
        )
        
        # Add items
        for item_data in breakfast_items:
            BreakfastOrderItem.objects.create(
                order=order,
                item_id=item_data['item_id'],
                quantity=item_data['quantity'],
                special_instructions=item_data.get('instructions', '')
            )
        
        # Real-time notification
        notification_manager.notify_breakfast_order_created(order)
        
        return Response({
            'success': True,
            'order_id': order.id,
            'delivery_date': str(order.delivery_date),
            'items_count': order.items.count()
        })
```

### **Phase 4: Guest Chat Integration**

#### **File**: `chat/guest_views.py` (NEW)
```python
class GuestChatSessionView(APIView):
    """
    Create/join chat session using booking token
    POST /api/public/hotel/{hotel_slug}/chat/start/
    """
    
    def post(self, request, hotel_slug):
        token_obj = self._validate_guest_token(request, hotel_slug)
        booking = token_obj.booking
        
        # Check chat permissions
        if not token_obj.can_chat:
            return Response({'error': 'Chat access disabled'}, status=403)
        
        # Find or create chat conversation
        conversation, created = GuestChatConversation.objects.get_or_create(
            booking=booking,
            defaults={
                'guest_name': booking.primary_guest_name,
                'room_number': booking.assigned_room.room_number if booking.assigned_room else None,
                'status': 'ACTIVE'
            }
        )
        
        # Generate Pusher channel info
        chat_channel = f"private-guest-chat.{booking.booking_id}"
        
        return Response({
            'conversation_id': conversation.id,
            'pusher_channel': chat_channel,
            'guest_token': token_obj.token_hash[:16],  # Partial for logging
            'staff_online': self._get_online_staff_count(booking.hotel)
        })

class GuestChatMessageView(APIView):
    """Send message in chat using booking token"""
    
    def post(self, request, hotel_slug):
        token_obj = self._validate_guest_token(request, hotel_slug)
        booking = token_obj.booking
        
        conversation = get_object_or_404(
            GuestChatConversation,
            booking=booking
        )
        
        message_text = request.data.get('message', '').strip()
        if not message_text:
            return Response({'error': 'Message cannot be empty'}, status=400)
        
        # Create message
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender_type='GUEST',
            sender_name=booking.primary_guest_name,
            message=message_text
        )
        
        # Real-time notification to staff
        notification_manager.notify_guest_chat_message(message)
        
        return Response({
            'message_id': message.id,
            'sent_at': message.created_at.isoformat()
        })
```

### **Phase 5: Unified Pusher Channel Access**

#### **File**: `notifications/views.py` (EXTEND)
```python
class PusherAuthView(APIView):
    def _handle_guest_auth(self, socket_id, channel_name, guest_token):
        """Extended guest auth for multiple channel types"""
        
        # Validate channel patterns
        allowed_patterns = [
            'private-guest-booking.',
            'private-guest-chat.',
            'private-room-service.',
        ]
        
        if not any(channel_name.startswith(pattern) for pattern in allowed_patterns):
            return Response({"error": "Invalid channel for guest token"}, status=403)
        
        # Extract booking ID from channel
        booking_id = self._extract_booking_id_from_channel(channel_name)
        
        # Validate token
        token_obj = GuestBookingToken.validate_token(guest_token, booking_id)
        if not token_obj:
            return Response({"error": "UNAUTHORIZED"}, status=403)
        
        # Channel-specific permission checks
        if channel_name.startswith('private-guest-chat.') and not token_obj.can_chat:
            return Response({"error": "Chat access disabled"}, status=403)
        
        if channel_name.startswith('private-room-service.') and not token_obj.can_order_services:
            return Response({"error": "Room service access disabled"}, status=403)
        
        # Generate auth
        auth = self._generate_pusher_auth(socket_id, channel_name, {
            "user_id": f"guest-{token_obj.booking.booking_id}",
            "user_info": {
                "type": "guest",
                "booking_id": token_obj.booking.booking_id,
                "hotel": token_obj.hotel.slug,
                "permissions": {
                    "can_chat": token_obj.can_chat,
                    "can_order_services": token_obj.can_order_services
                }
            }
        })
        
        return Response(auth)
```

---

## 🔄 **Real-time Event Integration**

### **File**: `notifications/notification_manager.py` (EXTEND)
```python
class NotificationManager:
    
    def notify_room_service_order_created(self, order):
        """Notify staff about new room service order"""
        # Staff notification
        self.realtime_room_service_order_created(order)
        
        # Guest confirmation
        self.realtime_guest_order_confirmed(order)
    
    def notify_breakfast_order_created(self, order):
        """Notify kitchen staff about breakfast order"""
        self.realtime_breakfast_order_created(order)
        
        # Guest confirmation
        self.realtime_guest_breakfast_confirmed(order)
    
    def notify_guest_chat_message(self, message):
        """Notify staff about guest chat message"""
        # Staff notification
        staff_channel = f"{message.conversation.booking.hotel.slug}.staff-chat"
        self._safe_pusher_trigger(staff_channel, "guest_message", {
            "conversation_id": message.conversation.id,
            "booking_id": message.conversation.booking.booking_id,
            "guest_name": message.sender_name,
            "message": message.message,
            "room_number": message.conversation.room_number
        })
```

---

## 🌐 **Frontend Integration Guide**

### **1. Initialize Guest Session**
```javascript
class GuestSession {
  constructor(bookingId, guestToken) {
    this.bookingId = bookingId;
    this.token = guestToken;
    this.pusher = null;
    this.channels = {};
  }
  
  async initialize() {
    // Initialize Pusher with guest token auth
    this.pusher = new Pusher(PUSHER_KEY, {
      cluster: 'your-cluster',
      authEndpoint: '/api/notifications/pusher/auth/',
      auth: {
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      }
    });
    
    // Subscribe to all guest channels
    await this.subscribeToChannels();
  }
  
  async subscribeToChannels() {
    // Booking updates
    this.channels.booking = this.pusher.subscribe(`private-guest-booking.${this.bookingId}`);
    
    // Chat
    this.channels.chat = this.pusher.subscribe(`private-guest-chat.${this.bookingId}`);
    
    // Room service
    this.channels.roomService = this.pusher.subscribe(`private-room-service.${this.bookingId}`);
  }
}
```

### **2. Unified API Service**
```javascript
class GuestAPIService {
  constructor(token, hotelSlug) {
    this.token = token;
    this.hotelSlug = hotelSlug;
    this.baseURL = '/api/public';
  }
  
  // Room service orders
  async orderRoomService(items) {
    return this.post('/room-services/order/', { 
      items, 
      guest_token: this.token 
    });
  }
  
  // Breakfast orders
  async orderBreakfast(deliveryDate, items) {
    return this.post('/breakfast/order/', {
      delivery_date: deliveryDate,
      items,
      guest_token: this.token
    });
  }
  
  // Chat
  async startChat() {
    return this.post('/chat/start/', { guest_token: this.token });
  }
  
  async sendMessage(message) {
    return this.post('/chat/message/', { 
      message, 
      guest_token: this.token 
    });
  }
  
  // Helper method
  async post(endpoint, data) {
    const response = await fetch(`${this.baseURL}/hotel/${this.hotelSlug}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}
```

---

## 🔒 **Security Considerations**

### **Token Scope Control**
```python
# Create tokens with specific permissions
limited_token = GuestBookingToken.generate_token(
    booking=booking,
    purpose='ROOM_SERVICES'  # Only room service access
)

full_token = GuestBookingToken.generate_token(
    booking=booking,
    purpose='FULL_ACCESS'    # All services
)
```

### **Time-based Restrictions**
```python
def can_order_services(self):
    """Check if guest can currently order services"""
    if not self.booking.checked_in_at:
        return False
    if self.booking.checked_out_at:
        return False
    # Only during stay
    return True
```

---

## 📈 **Migration Strategy**

### **Phase 1**: Extend existing GuestBookingToken model
### **Phase 2**: Implement room service guest views
### **Phase 3**: Add breakfast ordering
### **Phase 4**: Integrate guest chat
### **Phase 5**: Update frontend to use unified token
### **Phase 6**: Real-time notifications across all services

---

## 🎯 **Benefits**

✅ **Single Token** - One source of truth for all guest services  
✅ **Secure** - Existing token validation patterns  
✅ **Real-time** - Pusher integration across all services  
✅ **Trackable** - All guest actions linked to booking  
✅ **Scalable** - Easy to add new services  
✅ **Consistent** - Same auth pattern everywhere