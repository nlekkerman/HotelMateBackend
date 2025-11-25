# Real-Time Image Updates with Pusher - FINAL

## Backend Implementation ✅ COMPLETE

### Architecture Overview

**Staff edits Hotel data** → **Saves to Hotel/HotelPublicSettings models** → **Broadcasts via Pusher** → **Public page updates instantly**

### What's Saved Where

| Data | Model | Edited By Staff | Displayed On Public |
|------|-------|----------------|---------------------|
| `hero_image` | **Hotel** | `/settings/` file upload | ✅ Yes |
| `landing_page_image` | **Hotel** | `/settings/` file upload | ✅ Yes |
| `logo` | **Hotel** | `/settings/` file upload | ✅ Yes |
| `gallery` | **HotelPublicSettings** | `/gallery/upload/` + `/gallery/reorder/` | ✅ Yes |
| `amenities` | **HotelPublicSettings** | `/settings/` PATCH | ✅ Yes |
| `room_types` | **RoomType** (separate model) | `/room-types/{id}/upload-image/` | ✅ Yes |
| `colors/theme` | **HotelPublicSettings** | `/settings/` PATCH | ✅ Yes |

### Pusher Events Broadcast

#### Channel: `hotel-{hotel_slug}` (e.g., `hotel-killarney`)

| Event | Triggered When | Payload | What Updates |
|-------|---------------|---------|--------------|
| `settings-updated` | Staff updates ANY hotel settings | `{ hero_image, hero_image_display, gallery, updated_at }` | Hero image, text, colors |
| `gallery-image-uploaded` | Staff uploads new gallery image | `{ url, public_id }` | Gallery array (add new) |
| `gallery-reordered` | Staff reorders gallery images | `{ gallery: [...urls] }` | Gallery order |
| `room-type-image-updated` | Staff uploads room type photo | `{ room_type_id, photo_url, timestamp }` | Room type card image |

---

## Frontend Implementation

### 1. Subscribe to Hotel Channel

```javascript
import Pusher from 'pusher-js';

// In your settings page component
const pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
  cluster: import.meta.env.VITE_PUSHER_CLUSTER,
});

const hotelSlug = 'hotel-killarney'; // Get from your app state
const channel = pusher.subscribe(`hotel-${hotelSlug}`);
```

### 2. Listen for Settings Updates

```javascript
// Update hero image in real-time
channel.bind('settings-updated', (data) => {
  console.log('Settings updated:', data);
  
  // Update your state
  setFormData(prev => ({
    ...prev,
    hero_image: data.hero_image,
    gallery: data.gallery
  }));
});
```

### 3. Listen for Gallery Updates

```javascript
// New image uploaded to gallery
channel.bind('gallery-image-uploaded', (data) => {
  console.log('New gallery image:', data.url);
  
  // Add to gallery array
  setFormData(prev => ({
    ...prev,
    gallery: [...prev.gallery, data.url]
  }));
});

// Gallery reordered
channel.bind('gallery-reordered', (data) => {
  console.log('Gallery reordered:', data.gallery);
  
  // Update gallery order
  setFormData(prev => ({
    ...prev,
    gallery: data.gallery
  }));
});
```

### 4. Listen for Room Type Image Updates

```javascript
// Room type photo updated
channel.bind('room-type-image-updated', (data) => {
  console.log('Room type image updated:', data);
  
  // Update specific room type in your list
  setRoomTypes(prev => prev.map(rt => 
    rt.id === data.room_type_id 
      ? { ...rt, photo_url: data.photo_url }
      : rt
  ));
});
```

### 5. Complete Example Hook

```javascript
// useHotelRealtime.js
import { useEffect } from 'react';
import Pusher from 'pusher-js';

export const useHotelRealtime = (hotelSlug, onSettingsUpdate, onGalleryUpdate, onRoomTypeUpdate) => {
  useEffect(() => {
    const pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
      cluster: import.meta.env.VITE_PUSHER_CLUSTER,
    });

    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    // Settings updates
    channel.bind('settings-updated', (data) => {
      console.log('🔄 Settings updated in real-time');
      onSettingsUpdate?.(data);
    });

    // Gallery uploads
    channel.bind('gallery-image-uploaded', (data) => {
      console.log('🖼️ Gallery image uploaded');
      onGalleryUpdate?.({ type: 'add', url: data.url });
    });

    // Gallery reorder
    channel.bind('gallery-reordered', (data) => {
      console.log('🔄 Gallery reordered');
      onGalleryUpdate?.({ type: 'reorder', gallery: data.gallery });
    });

    // Room type images
    channel.bind('room-type-image-updated', (data) => {
      console.log('🛏️ Room type image updated');
      onRoomTypeUpdate?.(data);
    });

    // Cleanup
    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
      pusher.disconnect();
    };
  }, [hotelSlug, onSettingsUpdate, onGalleryUpdate, onRoomTypeUpdate]);
};
```

### 6. Usage in Component

```javascript
// SettingsPage.jsx
import { useHotelRealtime } from './hooks/useHotelRealtime';

function SettingsPage() {
  const [formData, setFormData] = useState({...});
  const [roomTypes, setRoomTypes] = useState([]);
  const hotelSlug = useHotelSlug();

  // Subscribe to real-time updates
  useHotelRealtime(
    hotelSlug,
    // Settings update handler
    (data) => {
      setFormData(prev => ({
        ...prev,
        hero_image: data.hero_image || prev.hero_image,
        gallery: data.gallery || prev.gallery
      }));
    },
    // Gallery update handler
    (update) => {
      if (update.type === 'add') {
        setFormData(prev => ({
          ...prev,
          gallery: [...prev.gallery, update.url]
        }));
      } else if (update.type === 'reorder') {
        setFormData(prev => ({
          ...prev,
          gallery: update.gallery
        }));
      }
    },
    // Room type update handler
    (data) => {
      setRoomTypes(prev => prev.map(rt =>
        rt.id === data.room_type_id
          ? { ...rt, photo_url: data.photo_url }
          : rt
      ));
    }
  );

  return (
    // Your UI...
  );
}
```

---

## Testing

### 1. Open Two Browser Windows
- Window 1: Staff settings page
- Window 2: Same staff settings page (or public page)

### 2. Upload Image in Window 1
- Upload hero image or gallery image
- Watch Window 2 update **without refresh** ✨

### 3. Reorder Gallery in Window 1
- Drag and drop gallery images
- Watch Window 2 reflect changes **instantly** ✨

---

## Benefits

✅ **No page refresh needed** - Images update instantly
✅ **Multi-user collaboration** - Multiple staff can edit simultaneously
✅ **Real-time feedback** - See changes as they happen
✅ **Better UX** - Feels more responsive and modern
✅ **Sync across devices** - Edit on desktop, see on mobile instantly

---

## Environment Variables Needed

Add to your `.env` file:

```bash
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=your_pusher_cluster
```

---

## Channel Structure

```
hotel-{slug}/
├── settings-updated          # Hero image, general settings
├── gallery-image-uploaded    # New gallery image added
├── gallery-reordered         # Gallery order changed
└── room-type-image-updated   # Room type photo changed
```

All updates are broadcast on the **same channel** for easy subscription!
