# Staff Feed API - Frontend Integration Guide

## Overview
The Staff Feed (Posts system) allows hotel staff to create posts, comment, reply, and like content within their hotel's social feed. All routes require authentication and hotel slug in the URL.

## Base URL Structure
All staff feed endpoints follow this pattern:
```
/api/staff/hotels/{hotel_slug}/home/posts/
```

**Example with hotel slug:**
```
/api/staff/hotels/hotel-killarney/home/posts/
```

---

## Frontend Route Structure

### Staff Feed Page
```
Frontend: http://localhost:5173/staff/{hotel_slug}/feed
Backend:  /api/staff/hotels/{hotel_slug}/home/posts/
```

**Important:** The frontend MUST include the hotel slug in the route and pass it to all API calls.

---

## API Endpoints

### 1. Posts Management

#### List All Posts
```http
GET /api/staff/hotels/{hotel_slug}/home/posts/
```

**Response:**
```json
[
  {
    "id": 1,
    "author": {
      "id": 1,
      "user": {
        "username": "john_doe",
        "first_name": "John",
        "last_name": "Doe"
      }
    },
    "hotel": {
      "id": 1,
      "name": "Hotel Killarney",
      "slug": "hotel-killarney"
    },
    "content": "Welcome to our new staff portal!",
    "image": "https://...",
    "created_at": "2025-11-23T10:00:00Z",
    "updated_at": "2025-11-23T10:00:00Z",
    "likes": [
      {"id": 1, "staff": 2}
    ],
    "like_count": 1,
    "comments": [...]
  }
]
```

#### Create New Post
```http
POST /api/staff/hotels/{hotel_slug}/home/posts/
Content-Type: multipart/form-data
```

**Request Body:**
```javascript
const formData = new FormData();
formData.append('content', 'Post content here');
formData.append('image', imageFile); // optional
```

**Response:**
```json
{
  "id": 2,
  "author": {...},
  "hotel": {...},
  "content": "Post content here",
  "image": "https://...",
  "created_at": "2025-11-23T11:00:00Z",
  "updated_at": "2025-11-23T11:00:00Z",
  "likes": [],
  "like_count": 0,
  "comments": []
}
```

#### Get Single Post
```http
GET /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/
```

#### Update Post
```http
PUT /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/
PATCH /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/
Content-Type: multipart/form-data
```

**Note:** Only the post author can update their own posts.

#### Delete Post
```http
DELETE /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/
```

**Note:** Only the post author can delete their own posts.

---

### 2. Like System

#### Toggle Like on Post
```http
POST /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/like/
```

**Response:**
```json
{
  "liked": true,
  "like_count": 5
}
```

**Note:** 
- First call creates a like
- Second call removes the like (toggle behavior)

---

### 3. Comments Management

#### List Comments on Post
```http
GET /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/
```

**Response:**
```json
[
  {
    "id": 1,
    "author": {
      "id": 1,
      "user": {
        "username": "john_doe",
        "first_name": "John",
        "last_name": "Doe"
      }
    },
    "post": 1,
    "content": "Great post!",
    "image": null,
    "created_at": "2025-11-23T10:30:00Z",
    "updated_at": "2025-11-23T10:30:00Z",
    "replies": [...]
  }
]
```

#### Create Comment
```http
POST /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/
Content-Type: multipart/form-data
```

**Request Body:**
```javascript
const formData = new FormData();
formData.append('content', 'Comment text here');
formData.append('image', imageFile); // optional
```

#### Get Single Comment
```http
GET /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/
```

#### Update Comment
```http
PUT /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/
PATCH /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/
Content-Type: multipart/form-data
```

#### Delete Comment
```http
DELETE /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/
```

---

### 4. Comment Replies Management

#### List Replies on Comment
```http
GET /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/replies/
```

**Response:**
```json
[
  {
    "id": 1,
    "author": {
      "id": 2,
      "user": {
        "username": "jane_smith",
        "first_name": "Jane",
        "last_name": "Smith"
      }
    },
    "comment": 1,
    "content": "Thanks for your comment!",
    "image": null,
    "created_at": "2025-11-23T11:00:00Z",
    "updated_at": "2025-11-23T11:00:00Z"
  }
]
```

#### Create Reply
```http
POST /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/replies/
Content-Type: multipart/form-data
```

**Request Body:**
```javascript
const formData = new FormData();
formData.append('content', 'Reply text here');
formData.append('image', imageFile); // optional
```

#### Get Single Reply
```http
GET /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/replies/{reply_id}/
```

#### Update Reply
```http
PUT /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/replies/{reply_id}/
PATCH /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/replies/{reply_id}/
Content-Type: multipart/form-data
```

#### Delete Reply
```http
DELETE /api/staff/hotels/{hotel_slug}/home/posts/{post_id}/comments/{comment_id}/replies/{reply_id}/
```

---

## Frontend Implementation Example

### React/Vue Component Setup

```javascript
// Get hotel slug from route params
const { hotelSlug } = useParams(); // or from route context

// Base API URL
const API_BASE = `/api/staff/hotels/${hotelSlug}/home/posts`;

// Fetch all posts
const fetchPosts = async () => {
  const response = await fetch(API_BASE, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
};

// Create new post
const createPost = async (content, image) => {
  const formData = new FormData();
  formData.append('content', content);
  if (image) {
    formData.append('image', image);
  }
  
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  return await response.json();
};

// Like a post
const likePost = async (postId) => {
  const response = await fetch(`${API_BASE}/${postId}/like/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
};

// Create comment
const createComment = async (postId, content, image) => {
  const formData = new FormData();
  formData.append('content', content);
  if (image) {
    formData.append('image', image);
  }
  
  const response = await fetch(`${API_BASE}/${postId}/comments/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  return await response.json();
};

// Create reply
const createReply = async (postId, commentId, content, image) => {
  const formData = new FormData();
  formData.append('content', content);
  if (image) {
    formData.append('image', image);
  }
  
  const response = await fetch(
    `${API_BASE}/${postId}/comments/${commentId}/replies/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  return await response.json();
};
```

---

## Authentication & Permissions

### Requirements
- User must be authenticated
- User must have a linked staff profile
- User can only edit/delete their own posts, comments, and replies
- All actions are scoped to the hotel specified in the URL

### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "detail": "You can only modify your own posts."
}
```

**400 Bad Request:**
```json
{
  "detail": "Your user account is not linked to a staff profile."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

---

## Frontend Routing Examples

### React Router Setup
```javascript
<Route path="/staff/:hotelSlug/feed" element={<StaffFeed />} />
```

### Vue Router Setup
```javascript
{
  path: '/staff/:hotelSlug/feed',
  component: StaffFeed,
  props: true
}
```

### Access the Route
```
http://localhost:5173/staff/hotel-killarney/feed
```

---

## Testing

### Test with cURL
```bash
# List posts
curl -X GET "http://localhost:8000/api/staff/hotels/hotel-killarney/home/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create post
curl -X POST "http://localhost:8000/api/staff/hotels/hotel-killarney/home/posts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "content=Hello World!"

# Like post
curl -X POST "http://localhost:8000/api/staff/hotels/hotel-killarney/home/posts/1/like/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Notes

- **All endpoints require hotel_slug** in the URL path
- **Images are optional** for posts, comments, and replies
- **Content is required** for all create operations
- **Like system is a toggle** - same endpoint to like/unlike
- **Nested structure**: Posts → Comments → Replies
- **Soft deletes may be implemented** - check with backend team

---

---

## Theme Preferences API

### Get/Update Hotel Theme
```http
GET    /api/staff/hotels/{hotel_slug}/common/theme/
POST   /api/staff/hotels/{hotel_slug}/common/theme/
PATCH  /api/staff/hotels/{hotel_slug}/common/theme/
PUT    /api/staff/hotels/{hotel_slug}/common/theme/
```

**Description:** Manage theme preferences for the hotel. Auto-creates theme if it doesn't exist on GET.

**Example URL:**
```
/api/staff/hotels/hotel-killarney/common/theme/
```

**GET Response:**
```json
{
  "id": 1,
  "hotel": {
    "id": 1,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "primary_color": "#1976d2",
  "secondary_color": "#dc004e",
  "background_color": "#ffffff",
  "text_color": "#000000",
  "font_family": "Roboto",
  "created_at": "2025-11-23T10:00:00Z",
  "updated_at": "2025-11-23T10:00:00Z"
}
```

**PATCH/PUT Request:**
```json
{
  "primary_color": "#ff5722",
  "secondary_color": "#ffc107",
  "font_family": "Arial"
}
```

**Frontend Implementation:**
```javascript
// Get hotel slug from route params
const { hotelSlug } = useParams();

// Fetch theme
const fetchTheme = async () => {
  const response = await fetch(
    `/api/staff/hotels/${hotelSlug}/common/theme/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
};

// Update theme
const updateTheme = async (themeData) => {
  const response = await fetch(
    `/api/staff/hotels/${hotelSlug}/common/theme/`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(themeData)
    }
  );
  return await response.json();
};
```

---

## Related Documentation
- [FRONTEND_API_INTEGRATION.md](./FRONTEND_API_INTEGRATION.md) - General API integration guide
- [PHASE1_IMPLEMENTATION.md](../PHASE1_IMPLEMENTATION.md) - Phase 1 routing structure
