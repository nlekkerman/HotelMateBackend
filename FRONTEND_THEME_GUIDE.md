# Frontend Theme Application Guide

## Overview
This guide explains how to fetch hotel settings (including all theme colors) and apply them globally across your entire frontend application.

---

## API Endpoint

### Get Hotel Settings & Theme
```
GET /api/staff/hotel/{hotel_slug}/settings/
```

**Authentication:** Required (Staff Token)

**Response:**
```json
{
  "id": 1,
  "name": "Hotel Killarney",
  "slug": "hotel-killarney",
  "tagline": "Luxury in the heart of Killarney",
  "city": "Killarney",
  "country": "Ireland",
  "address_line_1": "123 Main Street",
  "address_line_2": "Suite 100",
  "postal_code": "V93 X2Y4",
  "phone": "+353 64 123 4567",
  "email": "info@hotelkillarney.com",
  "website_url": "https://hotelkillarney.com",
  "booking_url": "https://booking.hotelkillarney.com",
  "short_description": "Brief hotel description",
  "long_description": "Detailed hotel description",
  
  "main_color": "#3498db",
  "secondary_color": "#2ecc71",
  "background_color": "#ffffff",
  "text_color": "#333333",
  "border_color": "#dddddd",
  "button_color": "#2980b9",
  "button_text_color": "#ffffff",
  "button_hover_color": "#1f6391",
  "link_color": "#2980b9",
  "link_hover_color": "#1f6391"
}
```

### Update Hotel Settings & Theme
```
PATCH /api/staff/hotel/{hotel_slug}/settings/
```

**Request Body (update any fields):**
```json
{
  "name": "Updated Hotel Name",
  "main_color": "#3B82F6",
  "secondary_color": "#10B981",
  "button_color": "#F59E0B"
}
```

---

## Frontend Implementation

### 1. Fetch Settings on App Load

```javascript
// services/themeService.js
const API_BASE_URL = 'https://hotel-porter-d25ad83b12cf.herokuapp.com';

export async function fetchHotelSettings(hotelSlug, authToken) {
  const response = await fetch(
    `${API_BASE_URL}/api/staff/hotel/${hotelSlug}/settings/`,
    {
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch hotel settings');
  }
  
  return await response.json();
}
```

### 2. Apply Theme Globally Using CSS Variables

**Option A: Apply to Document Root (Recommended)**

```javascript
// utils/applyTheme.js
export function applyThemeToApp(settings) {
  const root = document.documentElement;
  
  // Apply all theme colors as CSS variables
  root.style.setProperty('--color-primary', settings.main_color);
  root.style.setProperty('--color-secondary', settings.secondary_color);
  root.style.setProperty('--color-background', settings.background_color);
  root.style.setProperty('--color-text', settings.text_color);
  root.style.setProperty('--color-border', settings.border_color);
  root.style.setProperty('--color-button', settings.button_color);
  root.style.setProperty('--color-button-text', settings.button_text_color);
  root.style.setProperty('--color-button-hover', settings.button_hover_color);
  root.style.setProperty('--color-link', settings.link_color);
  root.style.setProperty('--color-link-hover', settings.link_hover_color);
  
  console.log('✅ Theme applied globally');
}
```

**Usage in App Component:**

```javascript
// App.jsx (React example)
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchHotelSettings } from './services/themeService';
import { applyThemeToApp } from './utils/applyTheme';

function App() {
  const { hotelSlug } = useParams();
  
  useEffect(() => {
    async function loadTheme() {
      try {
        const authToken = localStorage.getItem('authToken');
        const settings = await fetchHotelSettings(hotelSlug, authToken);
        
        // Apply theme colors globally
        applyThemeToApp(settings);
        
        // Optionally store settings in state/context
        // setHotelSettings(settings);
      } catch (error) {
        console.error('Failed to load theme:', error);
      }
    }
    
    loadTheme();
  }, [hotelSlug]);
  
  return <YourAppContent />;
}
```

### 3. Use Theme Colors in Your CSS

**In your global CSS file:**

```css
/* styles/global.css */

/* Set defaults */
:root {
  --color-primary: #3498db;
  --color-secondary: #2ecc71;
  --color-background: #ffffff;
  --color-text: #333333;
  --color-border: #dddddd;
  --color-button: #2980b9;
  --color-button-text: #ffffff;
  --color-button-hover: #1f6391;
  --color-link: #2980b9;
  --color-link-hover: #1f6391;
}

/* Apply theme colors throughout your app */
body {
  background-color: var(--color-background);
  color: var(--color-text);
}

/* Buttons */
.btn-primary {
  background-color: var(--color-button);
  color: var(--color-button-text);
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: var(--color-button-hover);
}

/* Links */
a {
  color: var(--color-link);
  text-decoration: none;
}

a:hover {
  color: var(--color-link-hover);
}

/* Primary colored elements */
.header {
  background-color: var(--color-primary);
  color: white;
}

.accent-text {
  color: var(--color-secondary);
}

/* Borders */
.card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
}

/* Input fields */
input, textarea, select {
  border: 1px solid var(--color-border);
  color: var(--color-text);
  padding: 8px 12px;
}

input:focus, textarea:focus, select:focus {
  border-color: var(--color-primary);
  outline: none;
}
```

### 4. Using with Tailwind CSS

If you're using Tailwind, you can still use CSS variables:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        background: 'var(--color-background)',
        textMain: 'var(--color-text)',
        border: 'var(--color-border)',
        button: 'var(--color-button)',
        buttonText: 'var(--color-button-text)',
        buttonHover: 'var(--color-button-hover)',
        link: 'var(--color-link)',
        linkHover: 'var(--color-link-hover)',
      }
    }
  }
}
```

Then use in your components:
```jsx
<button className="bg-button text-buttonText hover:bg-buttonHover">
  Click Me
</button>

<div className="border border-border bg-background text-textMain">
  Content
</div>
```

### 5. Update Theme Colors

```javascript
// services/themeService.js
export async function updateHotelTheme(hotelSlug, authToken, updates) {
  const response = await fetch(
    `${API_BASE_URL}/api/staff/hotel/${hotelSlug}/settings/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to update theme');
  }
  
  const updated = await response.json();
  
  // Re-apply theme after update
  applyThemeToApp(updated);
  
  return updated;
}
```

**Usage:**
```javascript
// Update only colors
await updateHotelTheme('hotel-killarney', token, {
  main_color: '#3B82F6',
  secondary_color: '#10B981',
  button_color: '#F59E0B'
});

// Update hotel info and colors together
await updateHotelTheme('hotel-killarney', token, {
  name: 'New Hotel Name',
  tagline: 'New tagline',
  main_color: '#3B82F6',
  button_color: '#F59E0B'
});
```

---

## Complete React Example with Context

```javascript
// contexts/ThemeContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchHotelSettings } from '../services/themeService';
import { applyThemeToApp } from '../utils/applyTheme';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const { hotelSlug } = useParams();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    async function loadSettings() {
      try {
        const authToken = localStorage.getItem('authToken');
        const data = await fetchHotelSettings(hotelSlug, authToken);
        
        setSettings(data);
        applyThemeToApp(data);
      } catch (error) {
        console.error('Failed to load settings:', error);
      } finally {
        setLoading(false);
      }
    }
    
    if (hotelSlug) {
      loadSettings();
    }
  }, [hotelSlug]);
  
  const updateSettings = (newSettings) => {
    setSettings(newSettings);
    applyThemeToApp(newSettings);
  };
  
  return (
    <ThemeContext.Provider value={{ settings, loading, updateSettings }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
```

**Use in your app:**
```javascript
// App.jsx
import { ThemeProvider } from './contexts/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <YourRoutes />
    </ThemeProvider>
  );
}

// Any component
import { useTheme } from '../contexts/ThemeContext';

function MyComponent() {
  const { settings, loading } = useTheme();
  
  if (loading) return <div>Loading theme...</div>;
  
  return (
    <div>
      <h1>{settings.name}</h1>
      <p style={{ color: settings.main_color }}>
        Themed text
      </p>
    </div>
  );
}
```

---

## Theme Color Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `main_color` | Primary branding color | `#3498db` |
| `secondary_color` | Secondary accent color | `#2ecc71` |
| `background_color` | Main background | `#ffffff` |
| `text_color` | Default text color | `#333333` |
| `border_color` | Default border color | `#dddddd` |
| `button_color` | Button background | `#2980b9` |
| `button_text_color` | Button text color | `#ffffff` |
| `button_hover_color` | Button hover state | `#1f6391` |
| `link_color` | Default link color | `#2980b9` |
| `link_hover_color` | Link hover color | `#1f6391` |

---

## Best Practices

1. **Load theme early** - Fetch and apply theme colors as early as possible in your app initialization
2. **Use CSS variables** - This allows instant theme updates without reloading
3. **Fallback values** - Always set default values in CSS for when theme hasn't loaded yet
4. **Cache settings** - Consider caching settings in localStorage for faster subsequent loads
5. **Update globally** - When theme changes, re-apply using `applyThemeToApp()` to update entire app

---

## Troubleshooting

**Q: Colors not applying?**
- Check if CSS variables are defined in `:root`
- Verify `applyThemeToApp()` is being called after fetch
- Check browser console for fetch errors

**Q: Colors reset on page reload?**
- Make sure theme is loaded in your App component's `useEffect`
- Consider caching in localStorage

**Q: Want to preview color before saving?**
```javascript
// Temporary preview without saving
function previewColor(colorType, value) {
  document.documentElement.style.setProperty(`--color-${colorType}`, value);
}

// Revert to saved theme
applyThemeToApp(savedSettings);
```
