# Staff Chat - Frontend Integration Guide

## Overview
This guide covers how to display a list of staff members and initiate chat conversations between staff members.

---

## 1. Display Staff List

### Endpoint
```
GET /api/staff_chat/<hotel_slug>/staff-list/
```

### Headers
```javascript
{
  'Authorization': 'Token <your-auth-token>',
  'Content-Type': 'application/json'
}
```

### Example Request
```javascript
const fetchStaffList = async (hotelSlug) => {
  const response = await fetch(
    `https://your-api.com/api/staff_chat/${hotelSlug}/staff-list/`,
    {
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const staffList = await response.json();
  return staffList;
};
```

### Response Format
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "email": "john@hotel.com",
    "phone_number": "+1234567890",
    "department": {
      "id": 1,
      "name": "Reception",
      "slug": "reception"
    },
    "role": {
      "id": 1,
      "name": "Receptionist",
      "slug": "receptionist"
    },
    "is_active": true,
    "is_on_duty": true,
    "hotel_name": "Grand Hotel",
    "profile_image_url": "https://cloudinary.com/image.jpg"
  }
]
```

### Features Available
- **Search**: `?search=john` - Search by first name, last name, email, department, or role
- **Ordering**: `?ordering=first_name` or `?ordering=-last_name`

### Example with Search
```javascript
const searchStaff = async (hotelSlug, searchTerm) => {
  const response = await fetch(
    `https://your-api.com/api/staff_chat/${hotelSlug}/staff-list/?search=${searchTerm}`,
    {
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  return await response.json();
};
```

---

## 2. Select Staff & Start Chat

### Endpoint
```
POST /api/staff_chat/<hotel_slug>/conversations/
```

### Headers
```javascript
{
  'Authorization': 'Token <your-auth-token>',
  'Content-Type': 'application/json'
}
```

### Request Body
```json
{
  "participant_ids": [2],
  "title": "Optional Title (for group chats)"
}
```

**Notes:**
- `participant_ids`: Array of staff IDs to chat with
- For 1-on-1 chat: Include only one staff ID
- For group chat: Include multiple staff IDs and optionally a title
- The API automatically includes the current user as a participant

### Example: Start 1-on-1 Chat
```javascript
const startChatWithStaff = async (hotelSlug, staffId) => {
  const response = await fetch(
    `https://your-api.com/api/staff_chat/${hotelSlug}/conversations/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        participant_ids: [staffId]
      })
    }
  );
  
  const conversation = await response.json();
  return conversation;
};
```

### Example: Start Group Chat
```javascript
const startGroupChat = async (hotelSlug, staffIds, groupTitle) => {
  const response = await fetch(
    `https://your-api.com/api/staff_chat/${hotelSlug}/conversations/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Token ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        participant_ids: staffIds,
        title: groupTitle
      })
    }
  );
  
  const conversation = await response.json();
  return conversation;
};
```

### Response Format
```json
{
  "id": 5,
  "hotel": 1,
  "hotel_name": "Grand Hotel",
  "participants": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "department_name": "Reception",
      "role_name": "Receptionist",
      "is_on_duty": true,
      "profile_image_url": "https://cloudinary.com/image.jpg"
    },
    {
      "id": 2,
      "first_name": "Jane",
      "last_name": "Smith",
      "full_name": "Jane Smith",
      "department_name": "Housekeeping",
      "role_name": "Supervisor",
      "is_on_duty": false,
      "profile_image_url": null
    }
  ],
  "title": null,
  "is_group": false,
  "created_at": "2025-11-05T10:30:00Z",
  "updated_at": "2025-11-05T10:30:00Z",
  "last_message": null,
  "unread_count": 0
}
```

**Important:**
- If a 1-on-1 conversation already exists with the selected staff, the API returns the existing conversation (status 200)
- If it's a new conversation, the API creates it and returns status 201
- Navigate to the conversation view using the `id` from the response

---

## 3. Complete React Example

### Staff List Component
```javascript
import React, { useState, useEffect } from 'react';

const StaffChatList = ({ hotelSlug, authToken, onSelectStaff }) => {
  const [staffList, setStaffList] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStaff();
  }, [hotelSlug, searchTerm]);

  const fetchStaff = async () => {
    setLoading(true);
    try {
      const url = searchTerm
        ? `/api/staff_chat/${hotelSlug}/staff-list/?search=${searchTerm}`
        : `/api/staff_chat/${hotelSlug}/staff-list/`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      setStaffList(data);
    } catch (error) {
      console.error('Error fetching staff:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = async (staffId) => {
    try {
      const response = await fetch(
        `/api/staff_chat/${hotelSlug}/conversations/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Token ${authToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            participant_ids: [staffId]
          })
        }
      );
      
      const conversation = await response.json();
      onSelectStaff(conversation);
    } catch (error) {
      console.error('Error starting chat:', error);
    }
  };

  return (
    <div className="staff-chat-list">
      <input
        type="text"
        placeholder="Search staff..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="search-input"
      />
      
      {loading ? (
        <div>Loading...</div>
      ) : (
        <ul className="staff-list">
          {staffList.map((staff) => (
            <li key={staff.id} className="staff-item">
              <div className="staff-info">
                {staff.profile_image_url && (
                  <img 
                    src={staff.profile_image_url} 
                    alt={staff.full_name}
                    className="staff-avatar"
                  />
                )}
                <div>
                  <h4>{staff.full_name}</h4>
                  {staff.role && <p>{staff.role.name}</p>}
                  {staff.department && (
                    <p className="department">{staff.department.name}</p>
                  )}
                  {staff.is_on_duty && (
                    <span className="on-duty-badge">On Duty</span>
                  )}
                </div>
              </div>
              <button 
                onClick={() => handleStartChat(staff.id)}
                className="chat-button"
              >
                Chat
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default StaffChatList;
```

---

## 4. Error Handling

### Common Error Responses

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```
→ Check that the auth token is valid and included in headers

**403 Forbidden**
```json
{
  "error": "You can only create conversations in your hotel"
}
```
→ The staff member doesn't belong to the specified hotel

**400 Bad Request**
```json
{
  "error": "At least one participant is required"
}
```
→ No participant_ids provided or empty array

**400 Bad Request**
```json
{
  "error": "Some participants are invalid or inactive"
}
```
→ One or more staff IDs don't exist or are inactive

---

## 5. UI/UX Recommendations

### Staff List Display
- Show profile image (or default avatar if none)
- Display full name prominently
- Show role and department
- Add "On Duty" indicator badge
- Include search/filter functionality
- Sort by: name, department, or on-duty status

### Starting a Chat
- Single click/tap to start 1-on-1 chat
- For group chats: multi-select mode with "Create Group" button
- Show loading state while creating conversation
- Navigate to chat view after conversation is created/retrieved

### Visual Indicators
- Green dot for "on duty"
- Gray/offline indicator for off-duty
- Last seen/active status (future enhancement)

---

## Quick Start Checklist

- [ ] Get auth token from staff login
- [ ] Get hotel_slug from logged-in staff profile
- [ ] Fetch staff list: `GET /api/staff_chat/{hotel_slug}/staff-list/`
- [ ] Display staff with profile images, names, roles
- [ ] Add search input for filtering staff
- [ ] Implement "Chat" button for each staff member
- [ ] On click: `POST /api/staff_chat/{hotel_slug}/conversations/` with `participant_ids`
- [ ] Navigate to chat view with returned conversation ID

---

## Next Steps

After implementing the staff list and chat selection:
1. **Display Messages**: See `STAFF_CHAT_MESSAGES.md` (upcoming)
2. **Send Messages**: See `STAFF_CHAT_SEND_MESSAGE.md` (upcoming)
3. **Real-time Updates**: WebSocket integration (upcoming)

---

## Need Help?

- Check that your auth token is valid
- Verify hotel_slug matches the logged-in staff's hotel
- Use browser DevTools Network tab to inspect requests/responses
- Check backend logs for detailed error messages
