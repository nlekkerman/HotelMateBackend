# Frontend Hotel Creation Implementation Guide

## 🎯 Overview

This guide explains how to implement hotel creation functionality in the Frontend for super users. The super user will have access to a dedicated component that allows creating new hotels with all necessary setup.

## 🔑 Authentication & Permissions

### Required Permission Level
- **Django Superuser** (`is_superuser=True`) - Full system access
- **Alternative**: Staff with superuser privileges

### Authentication Flow
```javascript
// Check if user has hotel creation permissions
const canCreateHotel = user.is_superuser;

if (!canCreateHotel) {
  // Redirect or show access denied
  return <AccessDenied />;
}
```

## 🌐 API Endpoints

### Primary Hotel Creation Endpoint
```http
POST /api/hotel/hotels/
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Grand Hotel Dublin",
  "slug": "grand-hotel-dublin",
  "subdomain": "grand-hotel-dublin",
  "city": "Dublin",
  "country": "Ireland",
  "short_description": "Luxury hotel in the heart of Dublin",
  "tagline": "Experience Dublin's finest hospitality",
  "address_line_1": "123 O'Connell Street",
  "address_line_2": "City Centre",
  "postal_code": "D01 F5P2",
  "phone": "+353 1 234 5678",
  "email": "info@grandhoteldublin.com",
  "website_url": "https://grandhoteldublin.com",
  "is_active": true,
  "sort_order": 0
}
```

### Response Format
```json
{
  "id": 123,
  "name": "Grand Hotel Dublin",
  "slug": "grand-hotel-dublin",
  "subdomain": "grand-hotel-dublin",
  "logo": null,
  "city": "Dublin",
  "country": "Ireland",
  "is_active": true,
  "sort_order": 0,
  "created_at": "2026-01-10T12:00:00Z"
}
```

## 📝 Required Fields

### Mandatory Fields
- `name` (string) - Hotel display name
- `slug` (string) - URL-friendly identifier (unique)
- `subdomain` (string) - Subdomain for hotel access (unique)

### Recommended Fields
- `city` (string) - Hotel location city
- `country` (string) - Hotel location country
- `short_description` (text) - Brief marketing description
- `tagline` (string) - Marketing tagline
- `address_line_1` (string) - Primary address
- `phone` (string) - Contact phone number
- `email` (string) - Contact email
- `website` (string) - Hotel website URL

### Optional Fields
- `logo` (file) - Hotel logo image (Cloudinary)
- `hero_image` (file) - Banner image for public page
- `landing_page_image` (file) - Image for landing page card
- `long_description` (text) - Detailed description
- `address_line_2` (string) - Secondary address line
- `postal_code` (string) - Postal/ZIP code
- `latitude` (decimal) - GPS latitude
- `longitude` (decimal) - GPS longitude
- `is_active` (boolean) - Hotel visibility (default: true)
- `sort_order` (integer) - Display order (default: 0)

## 🏗️ Frontend Component Implementation

### 1. Hotel Creation Form Component

```jsx
import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { hotelAPI } from '../services/api';

const HotelCreationForm = () => {
  const { user, token } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    subdomain: '',
    city: '',
    country: '',
    short_description: '',
    tagline: '',
    address_line_1: '',
    address_line_2: '',
    postal_code: '',
    phone: '',
    email: '',
    website_url: '',
    is_active: true,
    sort_order: 0
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  // Auto-generate slug from name
  const handleNameChange = (name) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
    
    setFormData(prev => ({
      ...prev,
      name,
      slug,
      subdomain: slug
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});

    try {
      const response = await hotelAPI.createHotel(formData, token);
      
      // Success - redirect to hotel setup
      window.location.href = `/admin/hotels/${response.slug}/setup`;
      
    } catch (error) {
      setErrors(error.response?.data || { general: 'Failed to create hotel' });
    } finally {
      setLoading(false);
    }
  };

  // Permission check
  if (!user?.is_superuser) {
    return <AccessDenied message="Hotel creation requires superuser privileges" />;
  }

  return (
    <div className="hotel-creation-form">
      <h1>Create New Hotel</h1>
      
      <form onSubmit={handleSubmit}>
        {/* Basic Information */}
        <section>
          <h2>Basic Information</h2>
          
          <div className="form-group">
            <label>Hotel Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleNameChange(e.target.value)}
              required
            />
            {errors.name && <span className="error">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label>URL Slug *</label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => setFormData(prev => ({...prev, slug: e.target.value}))}
              required
              pattern="^[a-z0-9-]+$"
              title="Only lowercase letters, numbers, and hyphens allowed"
            />
            <small>Used in URLs: /hotels/{formData.slug}</small>
            {errors.slug && <span className="error">{errors.slug}</span>}
          </div>

          <div className="form-group">
            <label>Subdomain *</label>
            <input
              type="text"
              value={formData.subdomain}
              onChange={(e) => setFormData(prev => ({...prev, subdomain: e.target.value}))}
              required
              pattern="^[a-z0-9-]+$"
            />
            <small>Subdomain: {formData.subdomain}.hotelmate.com</small>
            {errors.subdomain && <span className="error">{errors.subdomain}</span>}
          </div>
        </section>

        {/* Location */}
        <section>
          <h2>Location</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label>City</label>
              <input
                type="text"
                value={formData.city}
                onChange={(e) => setFormData(prev => ({...prev, city: e.target.value}))}
              />
            </div>
            
            <div className="form-group">
              <label>Country</label>
              <input
                type="text"
                value={formData.country}
                onChange={(e) => setFormData(prev => ({...prev, country: e.target.value}))}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Address Line 1</label>
            <input
              type="text"
              value={formData.address_line_1}
              onChange={(e) => setFormData(prev => ({...prev, address_line_1: e.target.value}))}
            />
          </div>

          <div className="form-group">
            <label>Address Line 2</label>
            <input
              type="text"
              value={formData.address_line_2}
              onChange={(e) => setFormData(prev => ({...prev, address_line_2: e.target.value}))}
            />
          </div>

          <div className="form-group">
            <label>Postal Code</label>
            <input
              type="text"
              value={formData.postal_code}
              onChange={(e) => setFormData(prev => ({...prev, postal_code: e.target.value}))}
            />
          </div>
        </section>

        {/* Contact Information */}
        <section>
          <h2>Contact Information</h2>
          
          <div className="form-group">
            <label>Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData(prev => ({...prev, phone: e.target.value}))}
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({...prev, email: e.target.value}))}
            />
          </div>

          <div className="form-group">
            <label>Website</label>
            <input
              type="url"
              value={formData.website_url}
              onChange={(e) => setFormData(prev => ({...prev, website_url: e.target.value}))}
              placeholder="https://example.com"
            />
          </div>
        </section>

        {/* Marketing */}
        <section>
          <h2>Marketing</h2>
          
          <div className="form-group">
            <label>Tagline</label>
            <input
              type="text"
              value={formData.tagline}
              onChange={(e) => setFormData(prev => ({...prev, tagline: e.target.value}))}
              maxLength="200"
              placeholder="e.g., Experience Dublin's finest hospitality"
            />
          </div>

          <div className="form-group">
            <label>Short Description</label>
            <textarea
              value={formData.short_description}
              onChange={(e) => setFormData(prev => ({...prev, short_description: e.target.value}))}
              rows="3"
              placeholder="Brief marketing description for the hotel"
            />
          </div>
        </section>

        {/* Settings */}
        <section>
          <h2>Settings</h2>
          
          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({...prev, is_active: e.target.checked}))}
              />
              Active (visible to public)
            </label>
          </div>

          <div className="form-group">
            <label>Sort Order</label>
            <input
              type="number"
              value={formData.sort_order}
              onChange={(e) => setFormData(prev => ({...prev, sort_order: parseInt(e.target.value) || 0}))}
              min="0"
            />
            <small>Lower numbers appear first in listings</small>
          </div>
        </section>

        {errors.general && (
          <div className="error-banner">
            {errors.general}
          </div>
        )}

        <div className="form-actions">
          <button 
            type="submit" 
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Creating Hotel...' : 'Create Hotel'}
          </button>
          
          <button 
            type="button" 
            onClick={() => window.history.back()}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default HotelCreationForm;
```

### 2. API Service

```javascript
// services/hotelAPI.js
const BASE_URL = '/api/hotel';

export const hotelAPI = {
  // Create new hotel
  createHotel: async (hotelData, token) => {
    const response = await fetch(`${BASE_URL}/hotels/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(hotelData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create hotel');
    }

    return response.json();
  },

  // Get hotel by slug
  getHotel: async (slug, token) => {
    const response = await fetch(`${BASE_URL}/hotels/${slug}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch hotel');
    }

    return response.json();
  },

  // List all hotels (superuser only)
  listHotels: async (token) => {
    const response = await fetch(`${BASE_URL}/hotels/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch hotels');
    }

    return response.json();
  },
};
```

## 🔄 Post-Creation Setup Flow

After successful hotel creation, the following setup steps should be automated or prompted:

### 1. Bootstrap Hotel Public Page
```javascript
// Automatically create default public page sections
const bootstrapHotelPage = async (hotelSlug, token) => {
  try {
    const response = await fetch(`/api/staff/hotel/${hotelSlug}/public-page-bootstrap/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn('Failed to bootstrap public page');
    }
  } catch (error) {
    console.error('Bootstrap error:', error);
  }
};
```

### 2. Create Default Room Types
```javascript
const createDefaultRoomTypes = async (hotelSlug, token) => {
  const defaultRoomTypes = [
    {
      name: 'Standard Single',
      code: 'STD_SGL',
      capacity: 1,
      base_price: '75.00',
    },
    {
      name: 'Standard Double',
      code: 'STD_DBL',
      capacity: 2,
      base_price: '120.00',
    },
    {
      name: 'Superior Room',
      code: 'SUP_ROOM',
      capacity: 2,
      base_price: '160.00',
    },
  ];

  for (const roomType of defaultRoomTypes) {
    try {
      await fetch(`/api/staff/hotel/${hotelSlug}/room-types/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(roomType),
      });
    } catch (error) {
      console.error('Failed to create room type:', roomType.name);
    }
  }
};
```

### 3. Setup Navigation
```javascript
// Navigation items are automatically created via Django signals
// See: hotel/models.py @receiver(post_save, sender=Hotel)
```

## ✅ Validation Rules

### Frontend Validation
```javascript
const validateHotelData = (data) => {
  const errors = {};

  // Required fields
  if (!data.name?.trim()) {
    errors.name = 'Hotel name is required';
  }

  if (!data.slug?.trim()) {
    errors.slug = 'URL slug is required';
  } else if (!/^[a-z0-9-]+$/.test(data.slug)) {
    errors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
  }

  if (!data.subdomain?.trim()) {
    errors.subdomain = 'Subdomain is required';
  } else if (!/^[a-z0-9-]+$/.test(data.subdomain)) {
    errors.subdomain = 'Subdomain can only contain lowercase letters, numbers, and hyphens';
  }

  // Optional field validation
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.email = 'Please enter a valid email address';
  }

  if (data.website_url && !/^https?:\/\/.+/.test(data.website_url)) {
    errors.website_url = 'Website must be a valid URL starting with http:// or https://';
  }

  if (data.phone && !/^[\+]?[0-9\s\-\(\)]+$/.test(data.phone)) {
    errors.phone = 'Please enter a valid phone number';
  }

  return errors;
};
```

## 🎨 Styling Guidelines

### CSS Classes
```css
.hotel-creation-form {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.hotel-creation-form h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.hotel-creation-form section {
  background: #f8f9fa;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border-radius: 8px;
}

.hotel-creation-form section h2 {
  color: #34495e;
  margin-bottom: 1rem;
  border-bottom: 2px solid #3498db;
  padding-bottom: 0.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-group small {
  color: #7f8c8d;
  font-size: 0.875rem;
}

.error {
  color: #e74c3c;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

.error-banner {
  background: #ffebee;
  color: #c62828;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid #e74c3c;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}
```

## 🔐 Security Considerations

1. **Authentication**: Always verify user has superuser or super_staff_admin privileges
2. **Input Validation**: Validate all inputs on both frontend and backend
3. **Unique Constraints**: Ensure slug and subdomain uniqueness
4. **Rate Limiting**: Consider implementing rate limiting for hotel creation
5. **Audit Logging**: Log all hotel creation attempts for security monitoring

## 🧪 Testing

### Unit Tests
```javascript
// tests/hotelCreation.test.js
import { validateHotelData } from '../utils/validation';

describe('Hotel Creation Validation', () => {
  test('should require hotel name', () => {
    const data = { slug: 'test-hotel', subdomain: 'test-hotel' };
    const errors = validateHotelData(data);
    expect(errors.name).toBe('Hotel name is required');
  });

  test('should validate email format', () => {
    const data = {
      name: 'Test Hotel',
      slug: 'test-hotel',
      subdomain: 'test-hotel',
      email: 'invalid-email'
    };
    const errors = validateHotelData(data);
    expect(errors.email).toBe('Please enter a valid email address');
  });

  test('should validate slug format', () => {
    const data = {
      name: 'Test Hotel',
      slug: 'Test Hotel!',
      subdomain: 'test-hotel'
    };
    const errors = validateHotelData(data);
    expect(errors.slug).toContain('lowercase letters, numbers, and hyphens');
  });
});
```

## 📱 Mobile Responsiveness

```css
@media (max-width: 768px) {
  .hotel-creation-form {
    padding: 1rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}
```

## 🚀 Deployment Notes

1. **Environment Variables**: Ensure API endpoints are properly configured
2. **Permissions**: Verify superuser permissions are correctly implemented
3. **Database**: Ensure unique constraints on slug and subdomain fields
4. **File Uploads**: Configure Cloudinary for logo and image uploads
5. **URL Routing**: Update frontend routes to include hotel creation page

## 📋 Checklist

- [ ] Implement hotel creation form component
- [ ] Add API service methods
- [ ] Implement validation (frontend and backend)
- [ ] Add permission checks
- [ ] Style the form (responsive design)
- [ ] Add post-creation setup flow
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Write unit tests
- [ ] Test permission requirements
- [ ] Verify unique constraint handling
- [ ] Test mobile responsiveness