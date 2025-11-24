# Frontend Settings Workflow Guide

## How to Fetch and Update Hotel Settings

This guide explains how the frontend should fetch existing hotel settings from the database and populate forms for editing.

---

## Overview

The workflow has 3 main steps:

1. **Fetch existing settings** from the database (GET request)
2. **Populate form fields** with the fetched data
3. **Save changes** back to the database (PATCH/PUT request)

---

## Step 1: Fetch Existing Settings

### Endpoint
```
GET /api/staff/hotel/{hotel_slug}/settings/
```

### Request Example
```javascript
async function fetchHotelSettings(hotelSlug, authToken) {
  const response = await fetch(`/api/staff/hotel/${hotelSlug}/settings/`, {
    method: 'GET',
    headers: {
      'Authorization': `Token ${authToken}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch settings');
  }
  
  const settings = await response.json();
  return settings;
}
```

### Response Format
```json
{
  "short_description": "Experience luxury in the heart of Killarney",
  "long_description": "Our hotel offers world-class amenities...",
  "welcome_message": "Welcome to Grand Hotel Killarney!",
  "hero_image": "https://res.cloudinary.com/.../hero.jpg",
  "gallery": [
    "https://res.cloudinary.com/.../img1.jpg",
    "https://res.cloudinary.com/.../img2.jpg",
    "https://res.cloudinary.com/.../img3.jpg"
  ],
  "amenities": [
    "Free WiFi",
    "Swimming Pool",
    "Spa & Wellness",
    "Restaurant",
    "Bar",
    "Gym"
  ],
  "contact_email": "info@grandhotelkillarney.com",
  "contact_phone": "+353 64 123 4567",
  "contact_address": "123 Main Street, Killarney, Co. Kerry, Ireland",
  "primary_color": "#2C3E50",
  "secondary_color": "#3498DB",
  "accent_color": "#E74C3C",
  "background_color": "#ECF0F1",
  "button_color": "#E67E22",
  "theme_mode": "light",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-24T15:30:00Z"
}
```

**Important Notes:**
- If settings don't exist in the database, the backend automatically creates default values
- All fields will always be present in the response
- Empty fields return empty strings `""` or empty arrays `[]`

---

## Step 2: Populate Form Fields

### React Example
```javascript
import { useState, useEffect } from 'react';

function HotelSettingsEditor({ hotelSlug, authToken }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Fetch settings when component mounts
  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await fetchHotelSettings(hotelSlug, authToken);
        setSettings(data);
      } catch (error) {
        console.error('Error loading settings:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadSettings();
  }, [hotelSlug, authToken]);
  
  if (loading) return <div>Loading settings...</div>;
  
  return (
    <form>
      {/* Content Section */}
      <section>
        <h2>Content</h2>
        
        <label>Short Description</label>
        <textarea 
          value={settings.short_description}
          onChange={(e) => setSettings({...settings, short_description: e.target.value})}
          rows={3}
        />
        
        <label>Long Description</label>
        <textarea 
          value={settings.long_description}
          onChange={(e) => setSettings({...settings, long_description: e.target.value})}
          rows={8}
        />
        
        <label>Welcome Message</label>
        <input 
          type="text"
          value={settings.welcome_message}
          onChange={(e) => setSettings({...settings, welcome_message: e.target.value})}
        />
      </section>
      
      {/* Images Section */}
      <section>
        <h2>Images</h2>
        
        <label>Hero Image URL</label>
        <input 
          type="url"
          value={settings.hero_image}
          onChange={(e) => setSettings({...settings, hero_image: e.target.value})}
        />
        
        <label>Gallery Images (one URL per line)</label>
        <textarea 
          value={settings.gallery.join('\n')}
          onChange={(e) => setSettings({
            ...settings, 
            gallery: e.target.value.split('\n').filter(url => url.trim())
          })}
          rows={5}
        />
      </section>
      
      {/* Amenities Section */}
      <section>
        <h2>Amenities</h2>
        
        <label>Amenities (one per line)</label>
        <textarea 
          value={settings.amenities.join('\n')}
          onChange={(e) => setSettings({
            ...settings, 
            amenities: e.target.value.split('\n').filter(a => a.trim())
          })}
          rows={5}
        />
      </section>
      
      {/* Contact Section */}
      <section>
        <h2>Contact Information</h2>
        
        <label>Contact Email</label>
        <input 
          type="email"
          value={settings.contact_email}
          onChange={(e) => setSettings({...settings, contact_email: e.target.value})}
        />
        
        <label>Contact Phone</label>
        <input 
          type="tel"
          value={settings.contact_phone}
          onChange={(e) => setSettings({...settings, contact_phone: e.target.value})}
        />
        
        <label>Contact Address</label>
        <textarea 
          value={settings.contact_address}
          onChange={(e) => setSettings({...settings, contact_address: e.target.value})}
          rows={3}
        />
      </section>
      
      {/* Branding Section */}
      <section>
        <h2>Branding & Theme</h2>
        
        <label>Primary Color</label>
        <input 
          type="color"
          value={settings.primary_color}
          onChange={(e) => setSettings({...settings, primary_color: e.target.value})}
        />
        
        <label>Secondary Color</label>
        <input 
          type="color"
          value={settings.secondary_color}
          onChange={(e) => setSettings({...settings, secondary_color: e.target.value})}
        />
        
        <label>Accent Color</label>
        <input 
          type="color"
          value={settings.accent_color}
          onChange={(e) => setSettings({...settings, accent_color: e.target.value})}
        />
        
        <label>Background Color</label>
        <input 
          type="color"
          value={settings.background_color}
          onChange={(e) => setSettings({...settings, background_color: e.target.value})}
        />
        
        <label>Button Color</label>
        <input 
          type="color"
          value={settings.button_color}
          onChange={(e) => setSettings({...settings, button_color: e.target.value})}
        />
        
        <label>Theme Mode</label>
        <select 
          value={settings.theme_mode}
          onChange={(e) => setSettings({...settings, theme_mode: e.target.value})}
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </section>
      
      <button type="button" onClick={() => saveSettings(settings)}>
        Save Settings
      </button>
    </form>
  );
}
```

### Vue Example
```vue
<template>
  <div v-if="loading">Loading settings...</div>
  
  <form v-else @submit.prevent="saveSettings">
    <!-- Content Section -->
    <section>
      <h2>Content</h2>
      
      <label>Short Description</label>
      <textarea v-model="settings.short_description" rows="3"></textarea>
      
      <label>Long Description</label>
      <textarea v-model="settings.long_description" rows="8"></textarea>
      
      <label>Welcome Message</label>
      <input v-model="settings.welcome_message" type="text" />
    </section>
    
    <!-- Images Section -->
    <section>
      <h2>Images</h2>
      
      <label>Hero Image URL</label>
      <input v-model="settings.hero_image" type="url" />
      
      <label>Gallery Images (JSON array)</label>
      <textarea v-model="galleryText" rows="5"></textarea>
    </section>
    
    <!-- Contact Section -->
    <section>
      <h2>Contact Information</h2>
      
      <label>Contact Email</label>
      <input v-model="settings.contact_email" type="email" />
      
      <label>Contact Phone</label>
      <input v-model="settings.contact_phone" type="tel" />
      
      <label>Contact Address</label>
      <textarea v-model="settings.contact_address" rows="3"></textarea>
    </section>
    
    <!-- Branding Section -->
    <section>
      <h2>Branding & Theme</h2>
      
      <label>Primary Color</label>
      <input v-model="settings.primary_color" type="color" />
      
      <label>Theme Mode</label>
      <select v-model="settings.theme_mode">
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </section>
    
    <button type="submit">Save Settings</button>
  </form>
</template>

<script>
export default {
  props: ['hotelSlug', 'authToken'],
  
  data() {
    return {
      settings: null,
      loading: true
    };
  },
  
  computed: {
    galleryText: {
      get() {
        return this.settings?.gallery.join('\n') || '';
      },
      set(value) {
        this.settings.gallery = value.split('\n').filter(url => url.trim());
      }
    }
  },
  
  async mounted() {
    try {
      const response = await fetch(`/api/staff/hotel/${this.hotelSlug}/settings/`, {
        headers: { 'Authorization': `Token ${this.authToken}` }
      });
      this.settings = await response.json();
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      this.loading = false;
    }
  },
  
  methods: {
    async saveSettings() {
      // See Step 3 below
    }
  }
};
</script>
```

### Vanilla JavaScript Example
```javascript
// Load settings when page loads
document.addEventListener('DOMContentLoaded', async () => {
  const hotelSlug = 'hotel-killarney';
  const authToken = localStorage.getItem('authToken');
  
  try {
    // Fetch existing settings
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/settings/`, {
      headers: { 'Authorization': `Token ${authToken}` }
    });
    
    const settings = await response.json();
    
    // Populate form fields
    document.getElementById('short_description').value = settings.short_description;
    document.getElementById('long_description').value = settings.long_description;
    document.getElementById('welcome_message').value = settings.welcome_message;
    document.getElementById('hero_image').value = settings.hero_image;
    document.getElementById('gallery').value = settings.gallery.join('\n');
    document.getElementById('amenities').value = settings.amenities.join('\n');
    document.getElementById('contact_email').value = settings.contact_email;
    document.getElementById('contact_phone').value = settings.contact_phone;
    document.getElementById('contact_address').value = settings.contact_address;
    document.getElementById('primary_color').value = settings.primary_color;
    document.getElementById('secondary_color').value = settings.secondary_color;
    document.getElementById('accent_color').value = settings.accent_color;
    document.getElementById('background_color').value = settings.background_color;
    document.getElementById('button_color').value = settings.button_color;
    document.getElementById('theme_mode').value = settings.theme_mode;
    
  } catch (error) {
    console.error('Error loading settings:', error);
    alert('Failed to load hotel settings');
  }
});
```

---

## Step 3: Save Changes

### Using PATCH (Recommended for Partial Updates)

Only send fields that were changed:

```javascript
async function saveSettings(hotelSlug, updatedFields, authToken) {
  const response = await fetch(`/api/staff/hotel/${hotelSlug}/settings/`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updatedFields)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to save settings');
  }
  
  const saved = await response.json();
  return saved;
}

// Example: Only update colors
const colorUpdates = {
  primary_color: '#FF0000',
  secondary_color: '#00FF00'
};

await saveSettings('hotel-killarney', colorUpdates, authToken);
```

### Using PUT (Full Replacement)

Send all fields (replaces entire settings object):

```javascript
async function saveAllSettings(hotelSlug, completeSettings, authToken) {
  const response = await fetch(`/api/staff/hotel/${hotelSlug}/settings/`, {
    method: 'PUT',
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(completeSettings)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to save settings');
  }
  
  const saved = await response.json();
  return saved;
}
```

### Complete Save Handler Example
```javascript
async function handleSaveButton(hotelSlug, authToken) {
  // Get all form values
  const updatedSettings = {
    short_description: document.getElementById('short_description').value,
    long_description: document.getElementById('long_description').value,
    welcome_message: document.getElementById('welcome_message').value,
    hero_image: document.getElementById('hero_image').value,
    gallery: document.getElementById('gallery').value.split('\n').filter(url => url.trim()),
    amenities: document.getElementById('amenities').value.split('\n').filter(a => a.trim()),
    contact_email: document.getElementById('contact_email').value,
    contact_phone: document.getElementById('contact_phone').value,
    contact_address: document.getElementById('contact_address').value,
    primary_color: document.getElementById('primary_color').value,
    secondary_color: document.getElementById('secondary_color').value,
    accent_color: document.getElementById('accent_color').value,
    background_color: document.getElementById('background_color').value,
    button_color: document.getElementById('button_color').value,
    theme_mode: document.getElementById('theme_mode').value
  };
  
  try {
    const result = await fetch(`/api/staff/hotel/${hotelSlug}/settings/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updatedSettings)
    });
    
    if (result.ok) {
      const saved = await result.json();
      alert('Settings saved successfully!');
      console.log('Updated settings:', saved);
    } else {
      const error = await result.json();
      alert(`Error: ${error.error || 'Failed to save'}`);
    }
  } catch (error) {
    console.error('Save error:', error);
    alert('Network error: Could not save settings');
  }
}

// Attach to save button
document.getElementById('save-btn').addEventListener('click', () => {
  const hotelSlug = 'hotel-killarney';
  const authToken = localStorage.getItem('authToken');
  handleSaveButton(hotelSlug, authToken);
});
```

---

## Complete Workflow Example

### Full Page Implementation
```javascript
class HotelSettingsManager {
  constructor(hotelSlug, authToken) {
    this.hotelSlug = hotelSlug;
    this.authToken = authToken;
    this.apiUrl = `/api/staff/hotel/${hotelSlug}/settings/`;
  }
  
  // 1. Fetch existing settings
  async fetchSettings() {
    const response = await fetch(this.apiUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Token ${this.authToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch settings');
    }
    
    return await response.json();
  }
  
  // 2. Populate form with settings
  populateForm(settings) {
    // Content
    this.setFieldValue('short_description', settings.short_description);
    this.setFieldValue('long_description', settings.long_description);
    this.setFieldValue('welcome_message', settings.welcome_message);
    
    // Images
    this.setFieldValue('hero_image', settings.hero_image);
    this.setFieldValue('gallery', settings.gallery.join('\n'));
    
    // Amenities
    this.setFieldValue('amenities', settings.amenities.join('\n'));
    
    // Contact
    this.setFieldValue('contact_email', settings.contact_email);
    this.setFieldValue('contact_phone', settings.contact_phone);
    this.setFieldValue('contact_address', settings.contact_address);
    
    // Branding
    this.setFieldValue('primary_color', settings.primary_color);
    this.setFieldValue('secondary_color', settings.secondary_color);
    this.setFieldValue('accent_color', settings.accent_color);
    this.setFieldValue('background_color', settings.background_color);
    this.setFieldValue('button_color', settings.button_color);
    this.setFieldValue('theme_mode', settings.theme_mode);
  }
  
  // 3. Save updated settings
  async saveSettings(updates) {
    const response = await fetch(this.apiUrl, {
      method: 'PATCH',
      headers: {
        'Authorization': `Token ${this.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to save');
    }
    
    return await response.json();
  }
  
  // Helper method
  setFieldValue(fieldId, value) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.value = value || '';
    }
  }
  
  // Initialize the page
  async initialize() {
    try {
      // Show loading state
      this.showLoading(true);
      
      // Fetch and populate
      const settings = await this.fetchSettings();
      this.populateForm(settings);
      
      // Set up save handler
      document.getElementById('save-btn').addEventListener('click', async () => {
        await this.handleSave();
      });
      
    } catch (error) {
      console.error('Initialization error:', error);
      alert('Failed to load settings');
    } finally {
      this.showLoading(false);
    }
  }
  
  async handleSave() {
    try {
      this.showLoading(true);
      
      // Collect form data
      const updates = {
        short_description: document.getElementById('short_description').value,
        long_description: document.getElementById('long_description').value,
        welcome_message: document.getElementById('welcome_message').value,
        hero_image: document.getElementById('hero_image').value,
        gallery: document.getElementById('gallery').value.split('\n').filter(u => u.trim()),
        amenities: document.getElementById('amenities').value.split('\n').filter(a => a.trim()),
        contact_email: document.getElementById('contact_email').value,
        contact_phone: document.getElementById('contact_phone').value,
        contact_address: document.getElementById('contact_address').value,
        primary_color: document.getElementById('primary_color').value,
        secondary_color: document.getElementById('secondary_color').value,
        accent_color: document.getElementById('accent_color').value,
        background_color: document.getElementById('background_color').value,
        button_color: document.getElementById('button_color').value,
        theme_mode: document.getElementById('theme_mode').value
      };
      
      const saved = await this.saveSettings(updates);
      alert('Settings saved successfully!');
      console.log('Saved:', saved);
      
    } catch (error) {
      console.error('Save error:', error);
      alert(`Error: ${error.message}`);
    } finally {
      this.showLoading(false);
    }
  }
  
  showLoading(isLoading) {
    const loader = document.getElementById('loader');
    const form = document.getElementById('settings-form');
    
    if (loader) loader.style.display = isLoading ? 'block' : 'none';
    if (form) form.style.opacity = isLoading ? '0.5' : '1';
  }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
  const hotelSlug = 'hotel-killarney'; // Get from URL or context
  const authToken = localStorage.getItem('authToken');
  
  const manager = new HotelSettingsManager(hotelSlug, authToken);
  manager.initialize();
});
```

---

## Key Points to Remember

1. **Always GET first** - Fetch existing settings before showing the form
2. **Auto-created defaults** - If no settings exist, the backend creates defaults automatically
3. **Use PATCH for efficiency** - Only send changed fields to reduce payload size
4. **Use PUT for full updates** - Send all fields when doing a complete save
5. **Handle arrays properly** - Gallery and amenities are arrays, convert to/from newline-separated strings for textareas
6. **Colors are hex strings** - Use `<input type="color">` for better UX
7. **Authentication required** - All staff endpoints need the `Authorization: Token` header
8. **Error handling** - Always check `response.ok` and handle errors gracefully

---

## Testing Checklist

- [ ] Form loads with existing data from database
- [ ] Empty fields show empty strings (not null/undefined)
- [ ] Gallery array displays properly (multiple images)
- [ ] Amenities array displays properly (multiple items)
- [ ] Color pickers work with hex values
- [ ] Theme mode dropdown shows correct selection
- [ ] Save button sends PATCH request
- [ ] Success message displays after save
- [ ] Error message displays on failure
- [ ] Loading states display during fetch/save
- [ ] Authentication token is included in requests
- [ ] 401 errors redirect to login
- [ ] 403 errors show permission denied message

---

## See Also

- [PHASE1_FRONTEND_API_GUIDE.md](./PHASE1_FRONTEND_API_GUIDE.md) - Complete API documentation
- [PHASE1_IMPLEMENTATION_STATUS.md](./PHASE1_IMPLEMENTATION_STATUS.md) - Implementation status
