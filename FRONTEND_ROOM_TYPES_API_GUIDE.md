# Frontend Guide: How to Get Room Types with Starting Prices for Public Hotel Page

## Overview
This guide explains how to fetch room type information with starting prices for display on public hotel pages in your React frontend.

## API Endpoint

### Get Hotel Page with Room Types
**Endpoint:** `GET /api/public/hotel/{hotel-slug}/page/`

**Example URL:**
```
GET http://127.0.0.1:8000/api/public/hotel/hotel-killarney/page/
```

**No Authentication Required** - This is a public endpoint

## API Response Structure

The response includes hotel information, sections, and importantly **room type data** within the rooms section:

```json
{
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "preset": 2,  // Style preset for consistent theming
    // ... other hotel data
  },
  "sections": [
    {
      "id": 61,
      "position": 2,
      "name": "Our Rooms & Suites",
      "element": {
        "element_type": "rooms_list",
        "title": "Our Rooms & Suites", 
        "subtitle": "Choose the perfect stay for your visit"
      },
      "rooms_data": {
        "style_variant": 1,
        "room_types": [
          {
            "id": 1,
            "code": "STD-ROOM",
            "name": "Standard Double Room",
            "short_description": "Comfortable room with modern amenities",
            "max_occupancy": 2,
            "bed_setup": "1 Double Bed",
            "photo": "https://res.cloudinary.com/.../room-image.jpg",
            "starting_price_from": "89.00",  // ← Starting price per night
            "currency": "EUR",               // ← Currency code
            "availability_message": "Popular choice",
            "booking_cta_url": "/public/booking/hotel-killarney?room_type_code=STD-ROOM"
          },
          {
            "id": 2,
            "code": "DLX-SUITE", 
            "name": "Deluxe Suite",
            "short_description": "Spacious suite with separate living area",
            "max_occupancy": 4,
            "bed_setup": "King Bed + Sofa Bed",
            "photo": "https://res.cloudinary.com/.../suite-image.jpg", 
            "starting_price_from": "159.00",  // ← Starting price per night
            "currency": "EUR",
            "availability_message": "High demand",
            "booking_cta_url": "/public/booking/hotel-killarney?room_type_code=DLX-SUITE"
          }
          // ... more room types
        ]
      }
    }
    // ... other sections
  ]
}
```

## Frontend Implementation Examples

### React Component - Fetch Room Types

```jsx
import React, { useState, useEffect } from 'react';

const HotelRoomsSection = ({ hotelSlug }) => {
  const [roomTypes, setRoomTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRoomTypes = async () => {
      try {
        const response = await fetch(
          `/api/public/hotel/${hotelSlug}/page/`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch hotel data');
        }
        
        const data = await response.json();
        
        // Find the rooms section
        const roomsSection = data.sections?.find(
          section => section.element?.element_type === 'rooms_list'
        );
        
        if (roomsSection?.rooms_data?.room_types) {
          setRoomTypes(roomsSection.rooms_data.room_types);
        }
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRoomTypes();
  }, [hotelSlug]);

  if (loading) return <div>Loading rooms...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="rooms-section">
      <h2>Our Rooms & Suites</h2>
      <div className="room-grid">
        {roomTypes.map(room => (
          <RoomCard key={room.id} room={room} />
        ))}
      </div>
    </div>
  );
};

const RoomCard = ({ room }) => {
  return (
    <div className="room-card">
      {room.photo && (
        <img src={room.photo} alt={room.name} className="room-image" />
      )}
      
      <div className="room-content">
        <h3>{room.name}</h3>
        <p className="description">{room.short_description}</p>
        
        <div className="room-details">
          <span className="occupancy">
            👥 Up to {room.max_occupancy} guests
          </span>
          <span className="bed-setup">
            🛏️ {room.bed_setup}
          </span>
        </div>
        
        <div className="pricing">
          <span className="price">
            From {room.currency} {room.starting_price_from}
          </span>
          <span className="per-night">/night</span>
        </div>
        
        {room.availability_message && (
          <span className="availability-badge">
            {room.availability_message}
          </span>
        )}
        
        <a 
          href={room.booking_cta_url} 
          className="book-button"
        >
          Book Now
        </a>
      </div>
    </div>
  );
};

export default HotelRoomsSection;
```

### JavaScript Fetch Example

```javascript
// Simple function to get room types with prices
async function fetchHotelRoomTypes(hotelSlug) {
  try {
    const response = await fetch(`/api/public/hotel/${hotelSlug}/page/`);
    const data = await response.json();
    
    // Extract room types from the rooms section
    const roomsSection = data.sections?.find(
      section => section.element?.element_type === 'rooms_list'
    );
    
    return roomsSection?.rooms_data?.room_types || [];
  } catch (error) {
    console.error('Error fetching room types:', error);
    return [];
  }
}

// Usage example
fetchHotelRoomTypes('hotel-killarney').then(roomTypes => {
  console.log('Room types:', roomTypes);
  
  roomTypes.forEach(room => {
    console.log(`${room.name}: ${room.currency} ${room.starting_price_from}/night`);
  });
});
```

## Room Type Data Fields

Each room type object contains:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | number | Unique room type ID | `1` |
| `code` | string | Room type code | `"DLX-SUITE"` |
| `name` | string | Display name | `"Deluxe Suite"` |
| `short_description` | string | Brief description | `"Spacious suite with..."` |
| `max_occupancy` | number | Maximum guests | `4` |
| `bed_setup` | string | Bed configuration | `"King Bed + Sofa Bed"` |
| `photo` | string | Image URL | `"https://res.cloudinary.com/..."` |
| `starting_price_from` | string | Starting price per night | `"159.00"` |
| `currency` | string | Currency code | `"EUR"` |
| `availability_message` | string | Status message | `"High demand"` |
| `booking_cta_url` | string | Booking link | `"/public/booking/..."` |

## Price Display Best Practices

### 1. Format Currency Properly
```jsx
const formatPrice = (price, currency) => {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: currency,
  }).format(parseFloat(price));
};

// Usage
<span className="price">
  From {formatPrice(room.starting_price_from, room.currency)}
</span>
```

### 2. Show "Starting From" Language
```jsx
<div className="pricing">
  <span className="from-label">Starting from</span>
  <span className="price">
    {room.currency} {room.starting_price_from}
  </span>
  <span className="per-night">per night</span>
</div>
```

### 3. Handle Missing Data
```jsx
const RoomPrice = ({ room }) => {
  if (!room.starting_price_from) {
    return <span className="price-tbd">Price on request</span>;
  }
  
  return (
    <span className="price">
      From {room.currency} {room.starting_price_from}/night
    </span>
  );
};
```

## Error Handling

```javascript
const fetchRoomTypesWithErrorHandling = async (hotelSlug) => {
  try {
    const response = await fetch(`/api/public/hotel/${hotelSlug}/page/`);
    
    if (response.status === 404) {
      throw new Error('Hotel not found');
    }
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Check if hotel has room types
    const roomsSection = data.sections?.find(
      section => section.element?.element_type === 'rooms_list'
    );
    
    if (!roomsSection) {
      console.warn('Hotel has no rooms section configured');
      return [];
    }
    
    return roomsSection.rooms_data?.room_types || [];
    
  } catch (error) {
    console.error('Failed to fetch room types:', error);
    throw error; // Re-throw to let component handle it
  }
};
```

## Available Hotels

To get a list of available hotel slugs:

```
GET /api/public/hotels/
```

This returns a list of all active hotels with their slugs for testing.

## Summary

- **Single Endpoint**: `/api/public/hotel/{hotel-slug}/page/` provides all room types with pricing
- **Starting Prices**: Each room type includes `starting_price_from` field
- **Complete Data**: Includes photos, descriptions, occupancy, bed setup, and booking URLs
- **No Auth Required**: Public endpoint accessible from frontend
- **Consistent Theming**: Hotel `preset` field available for styling consistency

This approach provides all the room type information your frontend needs to display attractive room listings with starting prices on public hotel pages.