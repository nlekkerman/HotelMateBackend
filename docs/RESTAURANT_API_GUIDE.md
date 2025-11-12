# Restaurant Management API Guide

Complete API documentation for restaurant creation and management in HotelMate.

---

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
  - [Create Restaurant](#create-restaurant)
  - [List Restaurants](#list-restaurants)
  - [Get Restaurant Details](#get-restaurant-details)
  - [Update Restaurant](#update-restaurant)
  - [Delete Restaurant](#delete-restaurant)
- [Data Models](#data-models)
- [Examples](#examples)
- [Error Handling](#error-handling)

---

## Overview

The Restaurant API allows you to create and manage restaurants for a specific hotel. Each restaurant is automatically associated with a hotel using the `hotel_slug` parameter in the URL.

**Key Features:**
- ✅ Automatic hotel assignment via URL parameter
- ✅ Auto-generated slug from restaurant name
- ✅ Soft delete (sets `is_active=False`)
- ✅ Optional opening/closing times
- ✅ Booking configuration (max group size, bookings per hour)
- ✅ Cloudinary image support

---

## Authentication

Most endpoints require authentication. Include the authorization token in the request header:

```http
Authorization: Bearer <your-token-here>
```

---

## Base URL

```
/api/bookings/
```

---

## Endpoints

### Create Restaurant

Create a new restaurant for a specific hotel.

**Endpoint:** `POST /api/bookings/{hotel_slug}/restaurants/`

**URL Parameters:**
- `hotel_slug` (string, required) - The hotel identifier (slug)

**Request Body:**

```json
{
  "name": "The Garden Restaurant",
  "capacity": 50,
  "description": "Fine dining experience with garden views",
  "opening_time": "18:00:00",
  "closing_time": "23:00:00",
  "max_bookings_per_hour": 10,
  "max_group_size": 15,
  "taking_bookings": true
}
```

**Required Fields:**
- `name` (string) - Restaurant name

**Optional Fields:**
- `capacity` (integer, default: 30) - Maximum number of guests
- `description` (string) - Restaurant description
- `opening_time` (time, format: "HH:MM:SS") - Opening time
- `closing_time` (time, format: "HH:MM:SS") - Closing time
- `max_bookings_per_hour` (integer, default: 8) - Max bookings per hour
- `max_group_size` (integer, default: 12) - Maximum group size
- `taking_bookings` (boolean, default: true) - Whether accepting bookings

**Response (201 Created):**

```json
{
  "id": 1,
  "name": "The Garden Restaurant",
  "slug": "the-garden-restaurant",
  "hotel": 5,
  "hotel_slug": "grand-hotel",
  "capacity": 50,
  "description": "Fine dining experience with garden views",
  "opening_time": "18:00:00",
  "closing_time": "23:00:00",
  "is_active": true,
  "max_bookings_per_hour": 10,
  "max_group_size": 15,
  "taking_bookings": true,
  "image": null
}
```

**Automatic Field Assignment:**
- `slug` - Auto-generated from restaurant name (e.g., "The Garden" → "the-garden")
- `hotel` - Auto-assigned from URL `hotel_slug` parameter
- `hotel_slug` - Read-only field showing the hotel's slug
- `is_active` - Defaults to `true`

---

### List Restaurants

Get all active restaurants for a specific hotel.

**Endpoint:** `GET /api/bookings/{hotel_slug}/restaurants/`

**URL Parameters:**
- `hotel_slug` (string, required) - The hotel identifier

**Query Parameters:**
- None

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "The Garden Restaurant",
    "slug": "the-garden-restaurant",
    "hotel": 5,
    "hotel_slug": "grand-hotel",
    "capacity": 50,
    "description": "Fine dining experience",
    "opening_time": "18:00:00",
    "closing_time": "23:00:00",
    "is_active": true,
    "max_bookings_per_hour": 10,
    "max_group_size": 15,
    "taking_bookings": true,
    "image": "https://res.cloudinary.com/..."
  },
  {
    "id": 2,
    "name": "Breakfast Terrace",
    "slug": "breakfast-terrace",
    "hotel": 5,
    "hotel_slug": "grand-hotel",
    "capacity": 30,
    "description": "Morning dining area",
    "opening_time": "07:00:00",
    "closing_time": "11:00:00",
    "is_active": true,
    "max_bookings_per_hour": 8,
    "max_group_size": 12,
    "taking_bookings": true,
    "image": null
  }
]
```

**Alternative Endpoint (Query Param):**

You can also filter restaurants using the default router endpoint:

```
GET /api/bookings/restaurants/?hotel_slug=grand-hotel
```

---

### Get Restaurant Details

Retrieve details of a specific restaurant.

**Endpoint:** `GET /api/bookings/restaurants/{restaurant_slug}/`

**URL Parameters:**
- `restaurant_slug` (string, required) - The restaurant identifier

**Response (200 OK):**

```json
{
  "id": 1,
  "name": "The Garden Restaurant",
  "slug": "the-garden-restaurant",
  "hotel": 5,
  "hotel_slug": "grand-hotel",
  "capacity": 50,
  "description": "Fine dining experience with garden views",
  "opening_time": "18:00:00",
  "closing_time": "23:00:00",
  "is_active": true,
  "max_bookings_per_hour": 10,
  "max_group_size": 15,
  "taking_bookings": true,
  "image": "https://res.cloudinary.com/..."
}
```

---

### Update Restaurant

Update an existing restaurant. Supports both full update (PUT) and partial update (PATCH).

**Endpoint:** `PATCH /api/bookings/restaurants/{restaurant_slug}/`

**URL Parameters:**
- `restaurant_slug` (string, required) - The restaurant identifier

**Request Body (Partial Update):**

```json
{
  "capacity": 60,
  "taking_bookings": false,
  "description": "Updated description"
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "name": "The Garden Restaurant",
  "slug": "the-garden-restaurant",
  "hotel": 5,
  "hotel_slug": "grand-hotel",
  "capacity": 60,
  "description": "Updated description",
  "opening_time": "18:00:00",
  "closing_time": "23:00:00",
  "is_active": true,
  "max_bookings_per_hour": 10,
  "max_group_size": 15,
  "taking_bookings": false,
  "image": null
}
```

**Note:** You cannot change the `hotel` field after creation - it's read-only.

---

### Delete Restaurant

Soft delete a restaurant (sets `is_active=False` instead of permanently deleting).

**Endpoint:** `DELETE /api/bookings/restaurants/{restaurant_slug}/`

**URL Parameters:**
- `restaurant_slug` (string, required) - The restaurant identifier

**Response (204 No Content):**

No response body. The restaurant's `is_active` field is set to `false`.

**Note:** The restaurant is not permanently deleted from the database. It's marked as inactive and won't appear in list queries.

---

## Data Models

### Restaurant Model

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | integer | Auto | - | Unique identifier |
| `name` | string | Yes | - | Restaurant name |
| `slug` | string | Auto | - | URL-safe identifier (auto-generated) |
| `hotel` | integer | Auto | - | Foreign key to Hotel (auto-assigned) |
| `hotel_slug` | string | Read-only | - | Hotel's slug for reference |
| `capacity` | integer | No | 30 | Maximum number of guests |
| `description` | string | No | null | Restaurant description |
| `opening_time` | time | No | null | Opening time (HH:MM:SS) |
| `closing_time` | time | No | null | Closing time (HH:MM:SS) |
| `is_active` | boolean | Auto | true | Active status |
| `max_bookings_per_hour` | integer | No | 8 | Max bookings per hour |
| `max_group_size` | integer | No | 12 | Maximum group size allowed |
| `taking_bookings` | boolean | No | true | Whether accepting bookings |
| `image` | string/url | No | null | Cloudinary image URL |

---

## Examples

### Frontend Implementation (React/JavaScript)

#### Create Restaurant

```javascript
const createRestaurant = async (hotelSlug, restaurantData) => {
  const response = await fetch(
    `/api/bookings/${hotelSlug}/restaurants/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(restaurantData)
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to create restaurant');
  }
  
  return await response.json();
};

// Usage
const newRestaurant = {
  name: "The Garden Restaurant",
  capacity: 50,
  description: "Fine dining experience",
  opening_time: "18:00:00",
  closing_time: "23:00:00",
  max_bookings_per_hour: 10,
  max_group_size: 15
};

try {
  const restaurant = await createRestaurant('grand-hotel', newRestaurant);
  console.log('Restaurant created:', restaurant);
} catch (error) {
  console.error('Error:', error.message);
}
```

#### List Restaurants

```javascript
const fetchRestaurants = async (hotelSlug) => {
  const response = await fetch(
    `/api/bookings/${hotelSlug}/restaurants/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch restaurants');
  }
  
  return await response.json();
};

// Usage
const restaurants = await fetchRestaurants('grand-hotel');
console.log('Restaurants:', restaurants);
```

#### Update Restaurant

```javascript
const updateRestaurant = async (restaurantSlug, updates) => {
  const response = await fetch(
    `/api/bookings/restaurants/${restaurantSlug}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(updates)
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to update restaurant');
  }
  
  return await response.json();
};

// Usage
const updates = {
  capacity: 60,
  taking_bookings: false
};

const updated = await updateRestaurant('the-garden-restaurant', updates);
console.log('Updated:', updated);
```

#### Delete Restaurant

```javascript
const deleteRestaurant = async (restaurantSlug) => {
  const response = await fetch(
    `/api/bookings/restaurants/${restaurantSlug}/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to delete restaurant');
  }
  
  return true; // 204 No Content
};

// Usage
await deleteRestaurant('the-garden-restaurant');
console.log('Restaurant deleted (soft delete)');
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request - Missing Hotel Slug

```json
{
  "hotel": ["Hotel identifier (hotel_slug) is required in URL"]
}
```

**Solution:** Ensure you're using the correct endpoint with `{hotel_slug}` in the URL.

#### 404 Not Found - Hotel Not Found

```json
{
  "detail": "Not found."
}
```

**Solution:** Verify the `hotel_slug` exists in the system.

#### 400 Bad Request - Validation Error

```json
{
  "name": ["This field is required."],
  "capacity": ["Ensure this value is greater than or equal to 1."]
}
```

**Solution:** Check that all required fields are provided and valid.

#### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Solution:** Include a valid authentication token in the Authorization header.

---

## Best Practices

### 1. Always Include Hotel Slug
Use the hotel-specific endpoint for creating restaurants:
```
✅ POST /api/bookings/{hotel_slug}/restaurants/
❌ POST /api/bookings/restaurants/ (missing hotel context)
```

### 2. Time Format
Always use 24-hour time format with seconds:
```json
{
  "opening_time": "18:00:00",  // ✅ Correct
  "closing_time": "11:00 PM"   // ❌ Invalid
}
```

### 3. Handle Read-Only Fields
Don't include read-only fields in your POST/PATCH requests:
```json
{
  "name": "New Restaurant",
  // ❌ Don't include these in requests:
  // "id": 1,
  // "slug": "new-restaurant",
  // "hotel": 5,
  // "hotel_slug": "grand-hotel"
}
```

### 4. Error Handling
Always handle errors gracefully:
```javascript
try {
  const restaurant = await createRestaurant(hotelSlug, data);
  // Success handling
} catch (error) {
  // Show user-friendly error message
  console.error('Failed to create restaurant:', error);
}
```

### 5. Validation Before Submit
Validate required fields on the frontend before making the API call:
```javascript
const validateRestaurant = (data) => {
  const errors = {};
  
  if (!data.name || data.name.trim() === '') {
    errors.name = 'Restaurant name is required';
  }
  
  if (data.capacity && data.capacity < 1) {
    errors.capacity = 'Capacity must be at least 1';
  }
  
  return errors;
};
```

---

## Notes

- **Slug Generation:** Restaurant slugs are automatically generated from the name. For example, "The Garden Restaurant" becomes "the-garden-restaurant".
- **Soft Delete:** Deleted restaurants are not removed from the database; they're marked as inactive (`is_active=False`).
- **Hotel Context:** The hotel is automatically assigned from the URL parameter - you don't need to include it in the request body.
- **Image Upload:** Currently, the `image` field is read-only. Image uploads may require a separate endpoint or admin panel access.

---

## Related Documentation

- [Booking API Guide](./BOOKING_API_GUIDE.md)
- [Restaurant Blueprint API](./RESTAURANT_BLUEPRINT_API.md)
- [Dining Table Management](./DINING_TABLE_API.md)

---

**Last Updated:** November 12, 2025  
**API Version:** v1  
**Maintained by:** HotelMate Backend Team
