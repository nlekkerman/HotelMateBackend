# Menu Item Staff Management - Frontend Integration Guide

**Last Updated:** December 11, 2025  
**Status:** ✅ Fully Implemented

## Overview

Complete CRUD management for menu items (Room Service & Breakfast) via staff dashboard with real-time Pusher notifications and Cloudinary image support.

---

## 🔗 API Endpoints

### Room Service Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/staff/hotel/{hotel_slug}/room-service-items/` | List all room service items |
| `POST` | `/api/staff/hotel/{hotel_slug}/room-service-items/` | Create new room service item |
| `GET` | `/api/staff/hotel/{hotel_slug}/room-service-items/{id}/` | Get specific item details |
| `PUT` | `/api/staff/hotel/{hotel_slug}/room-service-items/{id}/` | Update entire item |
| `PATCH` | `/api/staff/hotel/{hotel_slug}/room-service-items/{id}/` | Partial update |
| `DELETE` | `/api/staff/hotel/{hotel_slug}/room-service-items/{id}/` | Delete item |
| `POST` | `/api/staff/hotel/{hotel_slug}/room-service-items/{id}/upload-image/` | Upload item image |

### Breakfast Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/staff/hotel/{hotel_slug}/breakfast-items/` | List all breakfast items |
| `POST` | `/api/staff/hotel/{hotel_slug}/breakfast-items/` | Create new breakfast item |
| `GET` | `/api/staff/hotel/{hotel_slug}/breakfast-items/{id}/` | Get specific item details |
| `PUT` | `/api/staff/hotel/{hotel_slug}/breakfast-items/{id}/` | Update entire item |
| `PATCH` | `/api/staff/hotel/{hotel_slug}/breakfast-items/{id}/` | Partial update |
| `DELETE` | `/api/staff/hotel/{hotel_slug}/breakfast-items/{id}/` | Delete item |
| `POST` | `/api/staff/hotel/{hotel_slug}/breakfast-items/{id}/upload-image/` | Upload item image |

---

## 📋 Data Structures

### Room Service Item

```json
{
  "id": 1,
  "name": "Caesar Salad",
  "price": "12.50",
  "image": "https://res.cloudinary.com/...",
  "description": "Fresh romaine lettuce, croutons, parmesan cheese",
  "category": "Starters",
  "is_on_stock": true,
  "hotel": 1
}
```

**Fields:**
- `name` (string, required) - Item name
- `price` (decimal, required) - Item price in EUR
- `image` (string, optional) - Cloudinary image URL
- `description` (text, required) - Item description
- `category` (choices) - `Starters`, `Mains`, `Desserts`, `Drinks`, `Others`
- `is_on_stock` (boolean) - Availability status
- `hotel` (read-only) - Auto-assigned from staff profile

### Breakfast Item

```json
{
  "id": 1,
  "name": "Continental Breakfast",
  "image": "https://res.cloudinary.com/...",
  "description": "Toast, jam, coffee, juice",
  "category": "Hot Buffet",
  "quantity": 50,
  "is_on_stock": true,
  "hotel": 1
}
```

**Fields:**
- `name` (string, required) - Item name
- `image` (string, optional) - Cloudinary image URL
- `description` (text, required) - Item description
- `category` (choices) - `Mains`, `Hot Buffet`, `Cold Buffet`, `Breads`, `Condiments`, `Drinks`
- `quantity` (integer) - Default serving quantity
- `is_on_stock` (boolean) - Availability status
- `hotel` (read-only) - Auto-assigned from staff profile

---

## 🔐 Authentication & Headers

All endpoints require staff authentication:

```javascript
const headers = {
  'Authorization': `Token ${staffToken}`,
  'Content-Type': 'application/json'
};
```

**Permissions:**
- ✅ Must be authenticated staff member
- ✅ Must belong to same hotel as items
- ✅ Hotel scoping automatic (staff can only see/manage their hotel's items)

---

## 📡 Real-time Notifications (Pusher)

### Channel Subscription

```javascript
const pusher = new Pusher('your_pusher_key', {
  cluster: 'your_cluster'
});

const channel = pusher.subscribe(`${hotelSlug}.staff-menu-management`);
```

### Event Listener

```javascript
channel.bind('menu_item_updated', function(data) {
  const { payload } = data;
  
  console.log('Menu Update:', {
    action: payload.action,        // 'created', 'updated', 'deleted'
    menuType: payload.menu_type,   // 'room_service', 'breakfast'
    itemId: payload.item_id,
    itemName: payload.name,
    category: payload.category
  });
  
  // Update your UI based on the action
  switch(payload.action) {
    case 'created':
      addItemToUI(payload);
      break;
    case 'updated':
      updateItemInUI(payload);
      break;
    case 'deleted':
      removeItemFromUI(payload.item_id);
      break;
  }
});
```

### Event Data Structure

```json
{
  "category": "menu_management",
  "event_type": "menu_item_updated",
  "payload": {
    "menu_type": "room_service",
    "item_id": 1,
    "name": "Caesar Salad",
    "category": "Starters",
    "price": "12.50",
    "is_on_stock": true,
    "action": "created"
  },
  "hotel": "killarney-plaza",
  "timestamp": "2025-12-11T15:30:00Z"
}
```

---

## 🖼️ Image Upload

### Method 1: File Upload (Multipart)

```javascript
async function uploadItemImage(itemId, imageFile, menuType) {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/${menuType}-items/${itemId}/upload-image/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${staffToken}`
      },
      body: formData
    }
  );
  
  return response.json();
}
```

### Method 2: URL Upload (JSON)

```javascript
async function setItemImageURL(itemId, imageUrl, menuType) {
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/${menuType}-items/${itemId}/upload-image/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${staffToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image_url: imageUrl })
    }
  );
  
  return response.json();
}
```

---

## 💻 Frontend Implementation Examples

### 1. Fetch All Room Service Items

```javascript
async function fetchRoomServiceItems() {
  try {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/room-service-items/`,
      { headers }
    );
    
    if (response.ok) {
      const items = await response.json();
      displayMenuItems(items, 'room_service');
    }
  } catch (error) {
    console.error('Failed to fetch room service items:', error);
  }
}
```

### 2. Create New Menu Item

```javascript
async function createMenuItem(itemData, menuType) {
  try {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/${menuType}-items/`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(itemData)
      }
    );
    
    if (response.ok) {
      const newItem = await response.json();
      console.log('Item created:', newItem);
      // Real-time update will be received via Pusher
    }
  } catch (error) {
    console.error('Failed to create item:', error);
  }
}
```

### 3. Update Item Availability

```javascript
async function toggleItemAvailability(itemId, menuType, currentStatus) {
  try {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/${menuType}-items/${itemId}/`,
      {
        method: 'PATCH',
        headers,
        body: JSON.stringify({
          is_on_stock: !currentStatus
        })
      }
    );
    
    if (response.ok) {
      const updatedItem = await response.json();
      console.log('Availability updated:', updatedItem);
    }
  } catch (error) {
    console.error('Failed to update availability:', error);
  }
}
```

### 4. Delete Menu Item with Confirmation

```javascript
async function deleteMenuItem(itemId, itemName, menuType) {
  if (!confirm(`Are you sure you want to delete "${itemName}"?`)) {
    return;
  }
  
  try {
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/${menuType}-items/${itemId}/`,
      {
        method: 'DELETE',
        headers
      }
    );
    
    if (response.ok) {
      console.log('Item deleted successfully');
      // Real-time update will be received via Pusher
    }
  } catch (error) {
    console.error('Failed to delete item:', error);
  }
}
```

---

## 🏗️ Frontend Dashboard Components

### Menu Management Dashboard Structure

```
📁 MenuManagement/
├── 📄 MenuDashboard.jsx          # Main dashboard view
├── 📄 RoomServiceTab.jsx         # Room service items tab
├── 📄 BreakfastTab.jsx           # Breakfast items tab
├── 📄 MenuItemCard.jsx           # Individual item display
├── 📄 CreateItemModal.jsx        # Create/edit item form
├── 📄 ImageUploadComponent.jsx   # Image upload widget
└── 📄 MenuItemFilters.jsx        # Category/availability filters
```

### Suggested State Management

```javascript
// Menu items state
const [roomServiceItems, setRoomServiceItems] = useState([]);
const [breakfastItems, setBreakfastItems] = useState([]);
const [loading, setLoading] = useState(false);
const [selectedCategory, setSelectedCategory] = useState('all');
const [showOnlyInStock, setShowOnlyInStock] = useState(false);

// Real-time updates
useEffect(() => {
  const channel = pusher.subscribe(`${hotelSlug}.staff-menu-management`);
  
  channel.bind('menu_item_updated', (data) => {
    const { payload } = data;
    
    if (payload.menu_type === 'room_service') {
      updateRoomServiceItems(payload);
    } else if (payload.menu_type === 'breakfast') {
      updateBreakfastItems(payload);
    }
  });
  
  return () => {
    pusher.unsubscribe(`${hotelSlug}.staff-menu-management`);
  };
}, [hotelSlug]);
```

---

## 🎯 Key Features Implemented

### ✅ Complete CRUD Operations
- Create, Read, Update, Delete menu items
- Hotel-scoped security (staff only see their hotel's items)
- Automatic hotel assignment from staff profile

### ✅ Image Management
- File upload support (multipart/form-data)
- URL-based image setting
- Automatic Cloudinary integration
- Image preview in responses

### ✅ Real-time Updates
- Pusher notifications for all CRUD operations
- Standardized event structure
- Hotel-specific channels
- Action-based event handling

### ✅ Category Management
- Predefined category choices
- Separate categories for room service vs breakfast
- Category-based filtering support

### ✅ Stock Management
- `is_on_stock` availability toggle
- Real-time availability updates
- Stock status in all responses

---

## 🚀 Getting Started

1. **Setup Authentication:** Ensure staff token is available
2. **Subscribe to Pusher:** Connect to hotel's menu management channel
3. **Fetch Initial Data:** Load existing menu items on dashboard mount
4. **Implement CRUD UI:** Create forms for item management
5. **Handle Real-time Updates:** Update UI based on Pusher events
6. **Add Image Upload:** Implement file/URL upload components

---

## 📞 Support & Troubleshooting

### Common Issues

**403 Forbidden:** Staff member not associated with hotel or insufficient permissions  
**404 Not Found:** Invalid item ID or hotel slug  
**400 Bad Request:** Missing required fields or invalid data format  

### Debugging Tips

- Check staff authentication token validity
- Verify hotel slug matches staff's hotel
- Ensure required fields are included in requests
- Monitor Pusher connection status
- Check image file size limits for uploads

---

**Ready to implement? Your backend is fully configured for complete menu item management! 🍽️**