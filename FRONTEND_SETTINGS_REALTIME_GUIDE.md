# Hotel Settings Real-Time Updates Guide

## 🖼️ Overview

All hotel settings updates (images, branding colors, text fields, contact info, etc.) broadcast in real-time via Pusher so all connected staff and users see changes instantly. This includes:
- **Images:** hero_image, landing_page_image, logo
- **Branding:** All color fields (primary_color, secondary_color, etc.)
- **Content:** short_description, long_description, welcome_message
- **Contact:** contact_email, contact_phone, contact_address
- **Override fields:** name_override, tagline_override, city_override, etc.
- **All other settings fields**

When ANY field is updated via the settings endpoint, the backend broadcasts a `settings-updated` event with ALL current values.

---

## 📤 How to Update Hotel Settings

### **Endpoint:**
```http
PATCH /api/staff/hotel/<hotel_slug>/settings/
Content-Type: multipart/form-data (for images) OR application/json (for other fields)
```

### **Updatable Fields:**
- **Images:** `hero_image`, `landing_page_image`, `logo` (use multipart/form-data)
- **Branding Colors:** `primary_color`, `secondary_color`, `accent_color`, `background_color`, `button_color`, `button_text_color`, `button_hover_color`, `text_color`, `border_color`, `link_color`, `link_hover_color`
- **Content:** `short_description`, `long_description`, `welcome_message`
- **Contact:** `contact_email`, `contact_phone`, `contact_address`, `website`, `google_maps_link`
- **Override Fields:** `name_override`, `tagline_override`, `city_override`, `country_override`, `address_line_1_override`, `address_line_2_override`, `postal_code_override`, `latitude_override`, `longitude_override`, `phone_override`, `email_override`, `website_url_override`, `booking_url_override`
- **Other:** `amenities` (array), `slogan`, `favicon`, `theme_mode`

### **Important Notes:**
- Images are saved to the **Hotel model**, NOT HotelPublicSettings
- Use `multipart/form-data` (FormData) for image uploads
- Use `application/json` for text, color, and other non-file fields
- Can upload images along with other settings in same request
- **ALL updates broadcast in real-time via Pusher `settings-updated` event**

---

## 🔧 Frontend Implementation

### **React Example - Upload Hero Image**

```jsx
import { useState } from 'react';

function HeroImageUploader({ hotelSlug }) {
  const [uploading, setUploading] = useState(false);
  const [heroImage, setHeroImage] = useState(null);

  const handleImageUpload = async (file) => {
    setUploading(true);
    
    // Create FormData
    const formData = new FormData();
    formData.append('hero_image', file);
    
    try {
      const response = await fetch(
        `/api/staff/hotel/${hotelSlug}/settings/`,
        {
          method: 'PATCH',
          body: formData,
          // Don't set Content-Type header - browser sets it automatically
        }
      );
      
      const data = await response.json();
      
      if (response.ok) {
        // Update local state
        setHeroImage(data.hero_image_display);
        console.log('Hero image uploaded successfully!');
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="hero-image-uploader">
      <h3>Hero Image</h3>
      
      {heroImage && (
        <img src={heroImage} alt="Hero" className="preview" />
      )}
      
      <input
        type="file"
        accept="image/*"
        onChange={(e) => handleImageUpload(e.target.files[0])}
        disabled={uploading}
      />
      
      {uploading && <p>Uploading...</p>}
    </div>
  );
}
```

### **Upload Multiple Images at Once**

```jsx
async function uploadMultipleImages(hotelSlug, files) {
  const formData = new FormData();
  
  // Add multiple images
  if (files.hero) formData.append('hero_image', files.hero);
  if (files.landing) formData.append('landing_page_image', files.landing);
  if (files.logo) formData.append('logo', files.logo);
  
  // Can also update text fields in same request
  formData.append('short_description', 'Updated description');
  formData.append('primary_color', '#3B82F6');
  
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/settings/`,
    {
      method: 'PATCH',
      body: formData
    }
  );
  
  return await response.json();
}
```

### **Update Branding Colors (JSON)**

```jsx
async function updateColors(hotelSlug, colors) {
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/settings/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${authToken}`
      },
      body: JSON.stringify({
        primary_color: colors.primary,
        secondary_color: colors.secondary,
        accent_color: colors.accent,
        button_color: colors.button
      })
    }
  );
  
  if (response.ok) {
    const updated = await response.json();
    console.log('Colors updated! Real-time broadcast sent.');
    // Pusher will notify all connected users
    return updated;
  }
}

// Usage
await updateColors('hotel-killarney', {
  primary: '#3B82F6',
  secondary: '#10B981',
  accent: '#F59E0B',
  button: '#3B82F6'
});
```

### **Update Text Content (JSON)**

```jsx
async function updateContent(hotelSlug, content) {
  const response = await fetch(
    `/api/staff/hotel/${hotelSlug}/settings/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${authToken}`
      },
      body: JSON.stringify({
        short_description: content.shortDesc,
        long_description: content.longDesc,
        welcome_message: content.welcomeMsg
      })
    }
  );
  
  return await response.json();
}
```

### **Complete Settings Form with Images, Colors, and Text**

```jsx
function HotelSettingsForm({ hotelSlug }) {
  const [settings, setSettings] = useState(null);
  const [files, setFiles] = useState({});

  // Fetch current settings
  useEffect(() => {
    fetch(`/api/staff/hotel/${hotelSlug}/settings/`)
      .then(res => res.json())
      .then(data => setSettings(data));
  }, [hotelSlug]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    
    // Add files if selected
    if (files.hero_image) {
      formData.append('hero_image', files.hero_image);
    }
    if (files.landing_page_image) {
      formData.append('landing_page_image', files.landing_page_image);
    }
    if (files.logo) {
      formData.append('logo', files.logo);
    }
    
    // Add ALL text/color fields from form
    formData.append('short_description', settings.short_description);
    formData.append('long_description', settings.long_description);
    formData.append('welcome_message', settings.welcome_message);
    
    // Branding colors
    formData.append('primary_color', settings.primary_color);
    formData.append('secondary_color', settings.secondary_color);
    formData.append('accent_color', settings.accent_color);
    formData.append('background_color', settings.background_color);
    formData.append('button_color', settings.button_color);
    
    // Contact info
    formData.append('contact_email', settings.contact_email);
    formData.append('contact_phone', settings.contact_phone);
    formData.append('contact_address', settings.contact_address);
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/settings/`,
      {
        method: 'PATCH',
        body: formData
      }
    );
    
    if (response.ok) {
      const updated = await response.json();
      setSettings(updated);
      setFiles({});
      console.log('✅ Settings updated! Pusher broadcast sent to all users.');
    }
  };

  if (!settings) return <div>Loading...</div>;

  return (
    <form onSubmit={handleSubmit}>
      {/* Hero Image */}
      <div className="form-group">
        <label>Hero Image</label>
        {settings.hero_image_display && (
          <img 
            src={settings.hero_image_display} 
            alt="Current hero" 
            style={{ maxWidth: '300px' }}
          />
        )}
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFiles({
            ...files, 
            hero_image: e.target.files[0]
          })}
        />
      </div>

      {/* Landing Page Image */}
      <div className="form-group">
        <label>Landing Page Image</label>
        {settings.landing_page_image_display && (
          <img 
            src={settings.landing_page_image_display} 
            alt="Current landing" 
            style={{ maxWidth: '300px' }}
          />
        )}
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFiles({
            ...files, 
            landing_page_image: e.target.files[0]
          })}
        />
      </div>

      {/* Logo */}
      <div className="form-group">
        <label>Logo</label>
        {settings.logo_display && (
          <img 
            src={settings.logo_display} 
            alt="Current logo" 
            style={{ maxWidth: '150px' }}
          />
        )}
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFiles({
            ...files, 
            logo: e.target.files[0]
          })}
        />
      </div>

      {/* Text Fields */}
      <div className="form-group">
        <label>Short Description</label>
        <textarea
          value={settings.short_description}
          onChange={(e) => setSettings({
            ...settings,
            short_description: e.target.value
          })}
        />
      </div>

      <button type="submit">Save Settings</button>
    </form>
  );
}
```

---

## 🔴 Real-Time Updates with Pusher

### **What Gets Broadcast:**

When ANY settings field is updated (images, colors, text, contact, etc.), the backend broadcasts ALL current settings values:

**Channel:** `hotel-{hotel_slug}`  
**Event:** `settings-updated`

**Payload (Complete Settings Object):**
```json
{
  // Override fields
  "name_override": "...",
  "name_display": "...",
  "tagline_override": "...",
  "tagline_display": "...",
  "city_override": "...",
  "city_display": "...",
  "country_override": "...",
  "country_display": "...",
  "address_line_1_override": "...",
  "address_line_1_display": "...",
  "address_line_2_override": "...",
  "address_line_2_display": "...",
  "postal_code_override": "...",
  "postal_code_display": "...",
  "latitude_override": null,
  "latitude_display": 53.123,
  "longitude_override": null,
  "longitude_display": -6.456,
  "phone_override": "...",
  "phone_display": "...",
  "email_override": "...",
  "email_display": "...",
  "website_url_override": "...",
  "website_url_display": "...",
  "booking_url_override": "...",
  "booking_url_display": "...",
  
  // Content fields
  "short_description": "...",
  "long_description": "...",
  "welcome_message": "...",
  
  // Images
  "hero_image": "https://res.cloudinary.com/...",
  "hero_image_url": "https://res.cloudinary.com/...",
  "hero_image_display": "https://res.cloudinary.com/...",
  "landing_page_image": "https://res.cloudinary.com/...",
  "landing_page_image_url": "https://res.cloudinary.com/...",
  "landing_page_image_display": "https://res.cloudinary.com/...",
  "logo": "https://res.cloudinary.com/...",
  "logo_display": "https://res.cloudinary.com/...",
  "galleries": [...],
  "amenities": ["WiFi", "Pool", "Spa"],
  
  // Contact (legacy fields)
  "contact_email": "info@hotel.com",
  "contact_phone": "+353 1 234 5678",
  "contact_address": "123 Main St",
  "website": "https://hotel.com",
  "google_maps_link": "https://maps.google.com/...",
  "favicon": "https://res.cloudinary.com/...",
  "slogan": "Your home away from home",
  
  // Branding colors (ALL color fields)
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "accent_color": "#F59E0B",
  "background_color": "#FFFFFF",
  "button_color": "#3B82F6",
  "button_text_color": "#FFFFFF",
  "button_hover_color": "#2563EB",
  "text_color": "#1F2937",
  "border_color": "#E5E7EB",
  "link_color": "#3B82F6",
  "link_hover_color": "#2563EB",
  "theme_mode": "light",
  
  // Metadata
  "updated_at": "2025-11-25T12:00:00Z"
}
```

**Important:** The backend broadcasts the ENTIRE settings object whenever ANY field changes. Frontend should update ALL relevant UI elements, not just the changed field.

---

### **Listen for Updates:**

```javascript
import Pusher from 'pusher-js';

function useSettingsRealtime(hotelSlug, onUpdate) {
  useEffect(() => {
    // Initialize Pusher
    const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
      cluster: process.env.VITE_PUSHER_CLUSTER,
    });

    // Subscribe to hotel channel
    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    // Listen for settings updates
    channel.bind('settings-updated', (data) => {
      console.log('Settings updated in real-time:', data);
      
      // Update ALL settings in UI
      // Data contains complete settings object with all fields
      onUpdate({
        // Images
        heroImage: data.hero_image_display || data.hero_image,
        landingPageImage: data.landing_page_image_display || data.landing_page_image,
        logo: data.logo_display || data.logo,
        
        // Colors
        primaryColor: data.primary_color,
        secondaryColor: data.secondary_color,
        accentColor: data.accent_color,
        backgroundColor: data.background_color,
        buttonColor: data.button_color,
        buttonTextColor: data.button_text_color,
        buttonHoverColor: data.button_hover_color,
        textColor: data.text_color,
        borderColor: data.border_color,
        linkColor: data.link_color,
        linkHoverColor: data.link_hover_color,
        themeMode: data.theme_mode,
        
        // Content
        shortDescription: data.short_description,
        longDescription: data.long_description,
        welcomeMessage: data.welcome_message,
        
        // Contact
        contactEmail: data.contact_email,
        contactPhone: data.contact_phone,
        contactAddress: data.contact_address,
        
        // Override fields
        nameDisplay: data.name_display,
        taglineDisplay: data.tagline_display,
        cityDisplay: data.city_display,
        countryDisplay: data.country_display,
        
        // Metadata
        updatedAt: data.updated_at
      });
    });

    // Cleanup
    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
      pusher.disconnect();
    };
  }, [hotelSlug, onUpdate]);
}
```

### **Complete Example with Real-Time Updates:**

```jsx
import { useState, useEffect } from 'react';
import Pusher from 'pusher-js';

function HeroImageManager({ hotelSlug }) {
  const [settings, setSettings] = useState(null);
  const [uploading, setUploading] = useState(false);

  // Fetch initial settings
  useEffect(() => {
    fetchSettings();
  }, [hotelSlug]);

  const fetchSettings = async () => {
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/settings/`);
    const data = await response.json();
    setSettings(data);
  };

  // Setup real-time updates
  useEffect(() => {
    const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
      cluster: process.env.VITE_PUSHER_CLUSTER,
    });

    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    channel.bind('settings-updated', (data) => {
      console.log('🔄 Real-time settings update received!', data);
      
      // Update ALL settings in local state
      setSettings(prev => ({
        ...prev,
        // Images
        hero_image_display: data.hero_image_display || prev.hero_image_display,
        landing_page_image_display: data.landing_page_image_display || prev.landing_page_image_display,
        logo_display: data.logo_display || prev.logo_display,
        
        // Colors - update all color fields
        primary_color: data.primary_color || prev.primary_color,
        secondary_color: data.secondary_color || prev.secondary_color,
        accent_color: data.accent_color || prev.accent_color,
        background_color: data.background_color || prev.background_color,
        button_color: data.button_color || prev.button_color,
        button_text_color: data.button_text_color || prev.button_text_color,
        button_hover_color: data.button_hover_color || prev.button_hover_color,
        text_color: data.text_color || prev.text_color,
        border_color: data.border_color || prev.border_color,
        link_color: data.link_color || prev.link_color,
        link_hover_color: data.link_hover_color || prev.link_hover_color,
        theme_mode: data.theme_mode || prev.theme_mode,
        
        // Content
        short_description: data.short_description || prev.short_description,
        long_description: data.long_description || prev.long_description,
        welcome_message: data.welcome_message || prev.welcome_message,
        
        // Contact
        contact_email: data.contact_email || prev.contact_email,
        contact_phone: data.contact_phone || prev.contact_phone,
        contact_address: data.contact_address || prev.contact_address,
        
        // Override displays
        name_display: data.name_display || prev.name_display,
        tagline_display: data.tagline_display || prev.tagline_display,
        city_display: data.city_display || prev.city_display,
        country_display: data.country_display || prev.country_display,
        
        // Metadata
        updated_at: data.updated_at
      }));
      
      // Optional: Show notification
      console.log('✅ Settings updated in real-time!');
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
      pusher.disconnect();
    };
  }, [hotelSlug]);

  const handleUpload = async (file) => {
    setUploading(true);
    
    const formData = new FormData();
    formData.append('hero_image', file);
    
    try {
      const response = await fetch(
        `/api/staff/hotel/${hotelSlug}/settings/`,
        {
          method: 'PATCH',
          body: formData
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        
        // Update local state
        setSettings(data);
        
        // Pusher will broadcast to other users automatically
        console.log('✅ Upload complete! Other users will see update via Pusher');
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  if (!settings) return <div>Loading...</div>;

  return (
    <div className="hero-manager">
      <h2>Hero Image</h2>
      
      {/* Current Image */}
      {settings.hero_image_display && (
        <div className="current-image">
          <img 
            src={settings.hero_image_display} 
            alt="Hero" 
            style={{ maxWidth: '600px', border: '2px solid #ddd' }}
          />
          <p className="meta">
            Last updated: {new Date(settings.updated_at).toLocaleString()}
          </p>
        </div>
      )}
      
      {/* Upload Input */}
      <div className="upload-section">
        <input
          type="file"
          accept="image/*"
          onChange={(e) => handleUpload(e.target.files[0])}
          disabled={uploading}
        />
        {uploading && <span>⏳ Uploading...</span>}
      </div>
      
      <p className="info">
        💡 When you upload or change ANY settings, all connected users will see updates instantly!
      </p>
    </div>
  );
}
```

---

## 🚀 Real-Time Updates for ALL Settings Fields

### **Important: Complete Settings Broadcasting**

The backend broadcasts the **ENTIRE settings object** whenever ANY field is updated, including:

✅ **Images:** hero_image, landing_page_image, logo  
✅ **Branding Colors:** All 11 color fields (primary, secondary, accent, background, button, text, border, link colors, etc.)  
✅ **Content:** short_description, long_description, welcome_message  
✅ **Contact:** contact_email, contact_phone, contact_address, website  
✅ **Override Fields:** All _override and _display fields for hotel info  
✅ **Amenities:** amenities array  
✅ **Galleries:** galleries array with all gallery data  

**Why this matters:**
- When a staff member changes the primary color, all users see the color update instantly
- When someone uploads a hero image, everyone sees the new image without refresh
- When contact info is updated, all displays update in real-time
- **No field is left out** - the entire settings state is synchronized across all users

### **Frontend Implementation Pattern:**

```javascript
// Listen for settings-updated event
channel.bind('settings-updated', (data) => {
  // data contains ALL settings fields
  
  // Update your UI state with all fields
  setState(prevState => ({
    ...prevState,
    ...data  // Spread all updated fields
  }));
  
  // Trigger UI updates for:
  // - Color scheme changes (re-apply theme)
  // - Image updates (refresh image components)
  // - Text content changes (update displayed text)
  // - Contact info changes (update footer, etc.)
});
```

### **Example: Complete Settings Sync**

```jsx
function HotelSettings({ hotelSlug }) {
  const [settings, setSettings] = useState(null);

  useEffect(() => {
    const pusher = new Pusher(PUSHER_KEY, { cluster: PUSHER_CLUSTER });
    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    channel.bind('settings-updated', (data) => {
      console.log('Full settings update:', data);
      
      // Update ALL settings at once
      setSettings(prevSettings => ({
        ...prevSettings,
        ...data
      }));
      
      // Apply color theme updates
      if (data.primary_color) {
        document.documentElement.style.setProperty('--primary-color', data.primary_color);
      }
      if (data.secondary_color) {
        document.documentElement.style.setProperty('--secondary-color', data.secondary_color);
      }
      // ... apply all other colors
      
      // Show toast notification
      toast.success('Settings updated!');
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
    };
  }, [hotelSlug]);

  return (
    <div>
      {/* Hero Image */}
      <img src={settings?.hero_image_display} />
      
      {/* Branding Colors */}
      <button style={{ backgroundColor: settings?.button_color }}>
        Book Now
      </button>
      
      {/* Content */}
      <p>{settings?.short_description}</p>
      
      {/* Contact */}
      <a href={`mailto:${settings?.contact_email}`}>
        {settings?.contact_email}
      </a>
      
      {/* All fields update in real-time! */}
    </div>
  );
}
```

---

## 🎯 Best Practices

### **Settings Upload & Updates:**
1. **Show Preview** - Display current values before changes
2. **Progress Indicator** - Show loading state during updates
3. **Error Handling** - Handle update failures gracefully
4. **Optimistic Updates** - Update UI immediately, rollback on error

### **Real-Time Synchronization:**
1. **Show Notification** - Alert user when settings change
2. **Conflict Resolution** - If user is editing when update arrives, handle gracefully
3. **Auto-Refresh** - Update all UI elements without page reload
4. **Connection Status** - Show if Pusher disconnects
5. **Complete State Sync** - Don't just update one field, update ALL fields from the event

### **Performance:**
1. **Image Optimization** - Cloudinary handles this automatically
2. **Lazy Loading** - Use `loading="lazy"` on images
3. **Caching** - Browser caches Cloudinary URLs
4. **Debounce** - Prevent multiple rapid uploads

---

## 🔥 Advanced Examples

### **Drag & Drop Upload:**

```jsx
function DragDropHeroUpload({ hotelSlug }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      await uploadImage(file);
    }
  };

  const uploadImage = async (file) => {
    const formData = new FormData();
    formData.append('hero_image', file);
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/settings/`,
      { method: 'PATCH', body: formData }
    );
    
    if (response.ok) {
      console.log('Upload successful!');
    }
  };

  return (
    <div
      className={`drop-zone ${isDragging ? 'dragging' : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <p>Drag & Drop image here</p>
      <input
        type="file"
        onChange={(e) => uploadImage(e.target.files[0])}
      />
    </div>
  );
}
```

### **Multi-User Notification System:**

```jsx
function HeroImageWithNotifications({ hotelSlug }) {
  const [settings, setSettings] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
      cluster: process.env.VITE_PUSHER_CLUSTER,
    });

    const channel = pusher.subscribe(`hotel-${hotelSlug}`);

    channel.bind('settings-updated', (data) => {
      // Check if image actually changed
      if (data.hero_image_display !== settings?.hero_image_display) {
        // Show notification
        setNotification({
          message: 'Hero image was updated by another staff member',
          timestamp: new Date(),
          newImage: data.hero_image_display
        });
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => setNotification(null), 5000);
        
        // Update image
        setSettings(prev => ({
          ...prev,
          hero_image_display: data.hero_image_display
        }));
      }
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`hotel-${hotelSlug}`);
    };
  }, [hotelSlug, settings?.hero_image_display]);

  return (
    <div>
      {notification && (
        <div className="notification toast">
          <p>{notification.message}</p>
          <small>{notification.timestamp.toLocaleTimeString()}</small>
        </div>
      )}
      
      {settings?.hero_image_display && (
        <img src={settings.hero_image_display} alt="Hero" />
      )}
    </div>
  );
}
```

### **Image Comparison View:**

```jsx
function ImageComparisonView({ hotelSlug }) {
  const [currentImage, setCurrentImage] = useState(null);
  const [newImage, setNewImage] = useState(null);

  const handleFileSelect = (file) => {
    // Show preview before upload
    const reader = new FileReader();
    reader.onload = (e) => setNewImage(e.target.result);
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    // Upload logic here
  };

  return (
    <div className="comparison">
      <div className="current">
        <h3>Current</h3>
        <img src={currentImage} alt="Current" />
      </div>
      
      <div className="arrow">→</div>
      
      <div className="new">
        <h3>New</h3>
        {newImage ? (
          <>
            <img src={newImage} alt="New preview" />
            <button onClick={handleUpload}>Confirm Upload</button>
          </>
        ) : (
          <input type="file" onChange={(e) => handleFileSelect(e.target.files[0])} />
        )}
      </div>
    </div>
  );
}
```

---

## 📋 API Response Structure

### **GET /api/staff/hotel/{slug}/settings/**

```json
{
  "hero_image": null,                                    // Editable field (for upload)
  "hero_image_url": "https://res.cloudinary.com/...",   // Direct URL from HotelPublicSettings
  "hero_image_display": "https://res.cloudinary.com/...", // Current displayed image (Hotel model)
  
  "landing_page_image": null,
  "landing_page_image_url": "https://res.cloudinary.com/...",
  "landing_page_image_display": "https://res.cloudinary.com/...",
  
  "logo": null,
  "logo_display": "https://res.cloudinary.com/...",
  
  "galleries": [...],
  "updated_at": "2025-11-25T12:00:00Z"
}
```

### **PATCH /api/staff/hotel/{slug}/settings/**

**Request:**
```http
PATCH /api/staff/hotel/killarney/settings/
Content-Type: multipart/form-data

hero_image: [File]
short_description: "Updated text"
```

**Response:** Same as GET (full settings object)

---

## ✅ Checklist for Frontend

- [ ] Use `FormData` for image uploads
- [ ] Don't set `Content-Type` header (browser handles it)
- [ ] Show current image before upload
- [ ] Display loading state during upload
- [ ] Setup Pusher real-time listener
- [ ] Update UI when `settings-updated` event received
- [ ] Show notification when another user updates
- [ ] Handle upload errors gracefully
- [ ] Use `*_display` fields for showing current images
- [ ] Test with multiple browser tabs (simulate multi-user)

---

## 🐛 Troubleshooting

**Upload not working:**
- Verify `FormData` is used, not JSON
- Check file size (should be < 10MB)
- Ensure file input has `name="hero_image"` (or landing_page_image/logo)

**Real-time not updating:**
- Verify Pusher credentials are correct
- Check channel name matches: `hotel-{slug}`
- Ensure event name is `settings-updated`
- Check browser console for Pusher connection errors

**Wrong image displayed:**
- Use `*_display` fields, not base fields
- `hero_image_display` shows current (from Hotel model)
- `hero_image_url` shows override (from HotelPublicSettings)

---

## 🎨 Environment Variables Needed

```bash
# Frontend .env
VITE_PUSHER_KEY=your_pusher_key
VITE_PUSHER_CLUSTER=your_pusher_cluster
```

---

## 🚀 Summary

1. **Upload:** `PATCH /api/staff/hotel/{slug}/settings/` with FormData
2. **Display:** Use `*_display` fields from response
3. **Real-Time:** Listen to `settings-updated` on `hotel-{slug}` channel
4. **Update UI:** When Pusher event received, update image immediately
5. **Multi-User:** All staff see changes instantly via Pusher

Your hero images are now fully real-time! 🎉
