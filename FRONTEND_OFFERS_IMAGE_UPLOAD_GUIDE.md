# 🎁 Offer Image Upload & Real-Time Updates Guide

## 📋 Overview

This guide explains how to upload and update offer images with real-time Pusher broadcasting for the HotelMate Offers system.

**Current Status:** ⚠️ Offer image uploads work but **NO Pusher real-time broadcasting implemented yet**

This guide provides:
1. Current implementation details
2. How to upload offer images
3. How to add Pusher real-time updates (implementation needed)

---

## 🏗️ Current Implementation

### **Model: Offer**
Location: `hotel/models.py` (line 581)

```python
class Offer(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="offers")
    title = models.CharField(max_length=200)
    short_description = models.TextField()
    details_text = models.TextField(blank=True)
    details_html = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    tag = models.CharField(max_length=50, blank=True)
    book_now_url = models.URLField(blank=True)
    
    # Image field
    photo = CloudinaryField("offer_photo", blank=True, null=True)
    
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Field:**
- `photo`: CloudinaryField for offer promotional images

---

### **Serializers**

#### Staff Serializer (Full CRUD)
Location: `hotel/serializers.py` (line 878)

```python
class OfferStaffSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'short_description', 'details_text',
            'details_html', 'valid_from', 'valid_to', 'tag',
            'book_now_url', 'photo', 'photo_url', 'sort_order',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None
```

**Fields:**
- `photo`: For uploading images (write)
- `photo_url`: For displaying image URL (read)

#### Public Serializer (Read-only)
Location: `hotel/serializers.py` (line 121)

```python
class OfferSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'short_description', 'details_html',
            'valid_from', 'valid_to', 'tag', 'book_now_url',
            'photo_url'
        ]
    
    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None
```

---

### **ViewSet**
Location: `hotel/staff_views.py` (line 36)

```python
class StaffOfferViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for hotel offers.
    Scoped to staff's hotel only.
    """
    serializer_class = OfferStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return offers for staff's hotel"""
        staff = self.request.user.staff_profile
        return Offer.objects.filter(hotel=staff.hotel).order_by('sort_order', '-created_at')
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)
```

**⚠️ Missing:** No custom `upload_image` action like RoomType has

---

## 📤 How to Upload Offer Images

### **Method 1: Create Offer with Image (Recommended)**

**Endpoint:**
```http
POST /api/staff/hotel/<hotel_slug>/offers/
Content-Type: multipart/form-data
```

**Request (FormData):**
```javascript
const formData = new FormData();
formData.append('title', 'Weekend Getaway Package');
formData.append('short_description', 'Two nights with breakfast included');
formData.append('details_html', '<p>Enjoy a relaxing weekend...</p>');
formData.append('tag', 'Weekend Deal');
formData.append('sort_order', '0');
formData.append('is_active', 'true');
formData.append('photo', imageFile); // File object

const response = await fetch(`/api/staff/hotel/${hotelSlug}/offers/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const data = await response.json();
console.log('Created offer:', data);
console.log('Photo URL:', data.photo_url);
```

**Response:**
```json
{
  "id": 1,
  "title": "Weekend Getaway Package",
  "short_description": "Two nights with breakfast included",
  "details_text": "",
  "details_html": "<p>Enjoy a relaxing weekend...</p>",
  "valid_from": null,
  "valid_to": null,
  "tag": "Weekend Deal",
  "book_now_url": "",
  "photo": "https://res.cloudinary.com/..../offer_photo.jpg",
  "photo_url": "https://res.cloudinary.com/..../offer_photo.jpg",
  "sort_order": 0,
  "is_active": true,
  "created_at": "2025-11-25T12:00:00Z"
}
```

---

### **Method 2: Update Existing Offer Image**

**Endpoint:**
```http
PATCH /api/staff/hotel/<hotel_slug>/offers/<id>/
Content-Type: multipart/form-data
```

**Request:**
```javascript
const updateOfferImage = async (hotelSlug, offerId, imageFile) => {
  const formData = new FormData();
  formData.append('photo', imageFile);
  
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/offers/${offerId}/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  
  if (response.ok) {
    const data = await response.json();
    console.log('✅ Image updated:', data.photo_url);
    return data;
  } else {
    const error = await response.json();
    console.error('❌ Update failed:', error);
    throw error;
  }
};
```

---

### **Method 3: Update Only Text Fields (JSON)**

**Endpoint:**
```http
PATCH /api/staff/hotel/<hotel_slug>/offers/<id>/
Content-Type: application/json
```

**Request:**
```javascript
const updateOfferDetails = async (hotelSlug, offerId, updates) => {
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/offers/${offerId}/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );
  
  return await response.json();
};

// Usage
await updateOfferDetails('killarney', 1, {
  title: 'Updated Weekend Package',
  short_description: 'New description',
  is_active: true
});
```

---

## 🔴 Adding Pusher Real-Time Updates

### **⚠️ Current Status: NOT IMPLEMENTED**

The offer viewset does NOT broadcast Pusher events yet. Here's how to add it:

---

### **Step 1: Add Custom Upload Action to ViewSet**

Update `hotel/staff_views.py` - Add this to `StaffOfferViewSet`:

```python
from chat.utils import pusher_client
from rest_framework.decorators import action

class StaffOfferViewSet(viewsets.ModelViewSet):
    # ... existing code ...
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None, hotel_slug=None):
        """
        Upload or update offer image with Pusher broadcasting.
        
        POST /api/staff/hotel/{slug}/offers/{id}/upload-image/
        
        Body (multipart/form-data):
        - photo: file upload
        """
        try:
            offer = self.get_object()
            
            # Check for file upload
            if 'photo' not in request.FILES:
                return Response(
                    {'error': 'No photo file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            photo_file = request.FILES['photo']
            
            try:
                # Upload to Cloudinary
                offer.photo = photo_file
                offer.save()
                
                # Get photo URL
                photo_url = None
                if offer.photo:
                    try:
                        photo_url = offer.photo.url
                    except Exception:
                        photo_url = str(offer.photo)
                
                # ✅ Broadcast update via Pusher
                try:
                    hotel_slug = self.request.user.staff_profile.hotel.slug
                    pusher_client.trigger(
                        f'hotel-{hotel_slug}',
                        'offer-image-updated',
                        {
                            'offer_id': offer.id,
                            'offer_title': offer.title,
                            'photo_url': photo_url,
                            'timestamp': str(offer.created_at)
                        }
                    )
                    print(f"[Pusher] Broadcast offer-image-updated for offer {offer.id}")
                except Exception as e:
                    print(f"[Pusher] Broadcast failed: {e}")
                    pass  # Don't fail if Pusher fails
                
                return Response({
                    'message': 'Image uploaded successfully',
                    'photo_url': photo_url
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': f'Upload failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': f'Request failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

### **Step 2: Add Pusher to Create/Update Actions**

Override `perform_create` and `perform_update`:

```python
class StaffOfferViewSet(viewsets.ModelViewSet):
    # ... existing code ...
    
    def perform_create(self, serializer):
        """Automatically set hotel and broadcast creation"""
        staff = self.request.user.staff_profile
        offer = serializer.save(hotel=staff.hotel)
        
        # Broadcast new offer creation
        try:
            serializer_data = OfferStaffSerializer(offer).data
            pusher_client.trigger(
                f'hotel-{staff.hotel.slug}',
                'offer-created',
                {
                    'offer': serializer_data,
                    'action': 'created'
                }
            )
            print(f"[Pusher] Broadcast offer-created for offer {offer.id}")
        except Exception as e:
            print(f"[Pusher] Broadcast failed: {e}")
    
    def perform_update(self, serializer):
        """Broadcast offer updates"""
        offer = serializer.save()
        
        # Broadcast update
        try:
            staff = self.request.user.staff_profile
            serializer_data = OfferStaffSerializer(offer).data
            pusher_client.trigger(
                f'hotel-{staff.hotel.slug}',
                'offer-updated',
                {
                    'offer': serializer_data,
                    'action': 'updated'
                }
            )
            print(f"[Pusher] Broadcast offer-updated for offer {offer.id}")
        except Exception as e:
            print(f"[Pusher] Broadcast failed: {e}")
    
    def perform_destroy(self, instance):
        """Broadcast offer deletion"""
        offer_id = instance.id
        offer_title = instance.title
        hotel_slug = instance.hotel.slug
        
        instance.delete()
        
        # Broadcast deletion
        try:
            pusher_client.trigger(
                f'hotel-{hotel_slug}',
                'offer-deleted',
                {
                    'offer_id': offer_id,
                    'offer_title': offer_title,
                    'action': 'deleted'
                }
            )
            print(f"[Pusher] Broadcast offer-deleted for offer {offer_id}")
        except Exception as e:
            print(f"[Pusher] Broadcast failed: {e}")
```

---

## 🌐 Frontend Implementation with Pusher

### **Complete React Component Example**

```jsx
import { useState, useEffect } from 'react';
import Pusher from 'pusher-js';

function OfferImageManager({ hotelSlug }) {
  const [offers, setOffers] = useState([]);
  const [uploading, setUploading] = useState(false);

  // Fetch offers on mount
  useEffect(() => {
    const fetchOffers = async () => {
      const response = await fetch(`/api/staff/hotel/${hotelSlug}/offers/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setOffers(data);
    };
    
    fetchOffers();
  }, [hotelSlug]);

  // Setup Pusher real-time updates
  useEffect(() => {
    const pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
      cluster: import.meta.env.VITE_PUSHER_CLUSTER,
    });

    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    // Listen for image updates
    channel.bind('offer-image-updated', (data) => {
      console.log('🔄 Offer image updated:', data);
      
      setOffers(prevOffers => 
        prevOffers.map(offer => 
          offer.id === data.offer_id 
            ? { ...offer, photo_url: data.photo_url }
            : offer
        )
      );
    });

    // Listen for new offers
    channel.bind('offer-created', (data) => {
      console.log('✅ New offer created:', data);
      setOffers(prevOffers => [data.offer, ...prevOffers]);
    });

    // Listen for offer updates
    channel.bind('offer-updated', (data) => {
      console.log('🔄 Offer updated:', data);
      
      setOffers(prevOffers => 
        prevOffers.map(offer => 
          offer.id === data.offer.id 
            ? data.offer
            : offer
        )
      );
    });

    // Listen for offer deletions
    channel.bind('offer-deleted', (data) => {
      console.log('🗑️ Offer deleted:', data);
      
      setOffers(prevOffers => 
        prevOffers.filter(offer => offer.id !== data.offer_id)
      );
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
      pusher.disconnect();
    };
  }, [hotelSlug]);

  // Upload image handler
  const handleImageUpload = async (offerId, file) => {
    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('photo', file);
      
      const response = await fetch(
        `/api/staff/hotel/${hotelSlug}/offers/${offerId}/upload-image/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Upload successful:', data);
        
        // Update local state immediately (uploader's view)
        setOffers(prevOffers => 
          prevOffers.map(offer => 
            offer.id === offerId 
              ? { ...offer, photo_url: data.photo_url }
              : offer
          )
        );
      } else {
        const error = await response.json();
        console.error('❌ Upload failed:', error);
        alert(`Upload failed: ${error.error}`);
      }
    } catch (err) {
      console.error('❌ Network error:', err);
      alert('Network error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <h2>Offers</h2>
      
      {offers.map(offer => (
        <div key={offer.id} style={{ border: '1px solid #ddd', padding: '20px', marginBottom: '20px' }}>
          <h3>{offer.title}</h3>
          <p>{offer.short_description}</p>
          
          {offer.photo_url && (
            <img 
              src={offer.photo_url} 
              alt={offer.title}
              style={{ width: '100%', maxWidth: '400px', height: 'auto' }}
            />
          )}
          
          <div style={{ marginTop: '10px' }}>
            <label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files[0]) {
                    handleImageUpload(offer.id, e.target.files[0]);
                  }
                }}
                disabled={uploading}
              />
            </label>
            {uploading && <span> Uploading...</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

export default OfferImageManager;
```

---

## 📊 Pusher Events Reference

### **Events Broadcast:**

| Event | Trigger | Payload |
|-------|---------|---------|
| `offer-created` | New offer created | `{ offer: {...}, action: 'created' }` |
| `offer-updated` | Offer updated | `{ offer: {...}, action: 'updated' }` |
| `offer-deleted` | Offer deleted | `{ offer_id, offer_title, action: 'deleted' }` |
| `offer-image-updated` | Image uploaded via custom action | `{ offer_id, offer_title, photo_url, timestamp }` |

### **Channel:**
```
hotel-{hotel_slug}
```
Example: `hotel-killarney`

---

## 🧪 Testing Guide

### **1. Test Image Upload**

```bash
# Terminal 1: Run Django server with logging
python manage.py runserver

# Watch for:
# [Pusher] Broadcast offer-image-updated for offer 1
```

**Browser Console:**
```javascript
// Should see:
🔄 Offer image updated: {
  offer_id: 1,
  offer_title: "Weekend Getaway Package",
  photo_url: "https://res.cloudinary.com/...",
  timestamp: "2025-11-25T12:00:00Z"
}
```

---

### **2. Test Multi-Tab Real-Time**

1. Open **two browser tabs** with your app
2. In **Tab 1:** Upload offer image
3. In **Tab 2:** Should automatically see the new image
4. Check **Tab 2 console** for Pusher event

---

### **3. Test Create/Update/Delete**

```javascript
// Create new offer
const newOffer = await fetch(`/api/staff/hotel/${hotelSlug}/offers/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Test Offer',
    short_description: 'Test description',
    is_active: true
  })
});

// Watch all connected clients receive 'offer-created' event
```

---

## 🚨 Common Issues

### **Issue 1: Image uploads but no Pusher event**

**Cause:** Using standard PATCH instead of custom `upload-image` action

**Fix:** Use the custom endpoint:
```javascript
// ❌ WRONG - no Pusher broadcast
PATCH /api/staff/hotel/killarney/offers/1/

// ✅ CORRECT - broadcasts Pusher event
POST /api/staff/hotel/killarney/offers/1/upload-image/
```

---

### **Issue 2: Pusher not configured**

**Check backend:** `chat/utils.py`
```python
import pusher

pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)
```

**Check Django settings:**
```python
# settings.py
PUSHER_APP_ID = os.getenv('PUSHER_APP_ID')
PUSHER_KEY = os.getenv('PUSHER_KEY')
PUSHER_SECRET = os.getenv('PUSHER_SECRET')
PUSHER_CLUSTER = os.getenv('PUSHER_CLUSTER', 'eu')
```

---

### **Issue 3: Frontend not receiving events**

**Verify channel name:**
```javascript
// ❌ WRONG
pusher.subscribe('offers');

// ✅ CORRECT
pusher.subscribe(`hotel-${hotelSlug}`);
```

---

## 📝 Implementation Checklist

To add full Pusher support to Offers:

- [ ] Add `upload_image` action to `StaffOfferViewSet`
- [ ] Override `perform_create` with Pusher broadcast
- [ ] Override `perform_update` with Pusher broadcast
- [ ] Override `perform_destroy` with Pusher broadcast
- [ ] Test backend Pusher broadcasting
- [ ] Implement frontend Pusher listeners
- [ ] Test multi-tab real-time updates
- [ ] Test image uploads with real-time sync
- [ ] Update API documentation

---

## 🎯 Quick Start

### **Backend (Add to `hotel/staff_views.py`):**

```python
from chat.utils import pusher_client
from rest_framework.decorators import action

# Add upload_image action to StaffOfferViewSet (see Step 1 above)
# Add perform_create, perform_update, perform_destroy overrides (see Step 2 above)
```

### **Frontend (React):**

```javascript
// Use the complete OfferImageManager component above
import OfferImageManager from './components/OfferImageManager';

function App() {
  return <OfferImageManager hotelSlug="killarney" />;
}
```

---

## 📞 Support

**Backend files:**
- Model: `hotel/models.py` (line 581)
- Serializers: `hotel/serializers.py` (lines 121, 878)
- Views: `hotel/staff_views.py` (line 36)

**Frontend example:**
- Complete React component with Pusher (see above)

**Pusher setup:**
- Backend: `chat/utils.py`
- Settings: `HotelMateBackend/settings.py`

---

**Status:** ⚠️ Implementation needed for real-time updates. Current setup supports image uploads via standard REST API.
