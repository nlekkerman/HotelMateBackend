# Staff Authentication & Permissions System

This document explains how staff authentication, authorization, and permissions work in the HotelMate backend.

---

## Overview

The system uses Django's built-in User model extended with a Staff profile that connects users to hotels and provides role-based access control.

---

## Core Models

### 1. User (Django Built-in)
- Standard Django authentication user
- Linked to Staff via OneToOne relationship

### 2. Staff Model
Located in: `staff/models.py`

```python
class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_profile',  # IMPORTANT: Access via user.staff_profile
        null=True,
        blank=True
    )
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, ...)
    role = models.ForeignKey(Role, ...)
    
    ACCESS_LEVEL_CHOICES = [
        ('staff_admin', 'Staff Admin'),
        ('super_staff_admin', 'Super Staff Admin'),
        ('regular_staff', 'Regular Staff'),
    ]
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='regular_staff'
    )
```

**Key Points:**
- Each Staff member belongs to ONE hotel
- Related name is `staff_profile` - access via `request.user.staff_profile`
- Has access levels for hierarchical permissions
- Has department and role for granular access control

### 3. Role & Department
- Roles define job functions (e.g., "Manager", "Receptionist")
- Departments group related roles (e.g., "Front Desk", "Housekeeping")
- Used for filtering and organizing staff

### 4. NavigationItem
- Defines what menu items/pages a staff member can access
- Hotel-specific navigation items
- Assigned to staff members by Super Staff Admin

---

## Authentication Pattern

### Checking if User is Staff

```python
# Pattern used throughout the codebase:
if not hasattr(request.user, 'staff_profile'):
    return Response({"error": "User is not staff"}, status=403)

staff = request.user.staff_profile
```

### Getting Staff Hotel

```python
staff = request.user.staff_profile
hotel = staff.hotel
hotel_slug = staff.hotel.slug
```

---

## Custom Permission Classes

Located in: `staff_chat/permissions.py` (can be reused across apps)

### 1. IsStaffMember
**Purpose:** Verify user has a staff profile

```python
class IsStaffMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'staff_profile')
        )
```

**Usage:**
```python
permission_classes = [IsAuthenticated, IsStaffMember]
```

### 2. IsSameHotel
**Purpose:** Verify staff belongs to the hotel in the URL

```python
class IsSameHotel(permissions.BasePermission):
    def has_permission(self, request, view):
        hotel_slug = view.kwargs.get('hotel_slug')
        try:
            staff = request.user.staff_profile
            return staff.hotel.slug == hotel_slug
        except AttributeError:
            return False
```

**Usage:**
```python
# For URLs like: /api/staff/hotels/<hotel_slug>/...
permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
```

### 3. CanManageConversation
**Purpose:** Check if staff can manage a specific conversation

```python
class CanManageConversation(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        staff = request.user.staff_profile
        
        # Creator can always manage
        if obj.created_by and obj.created_by.id == staff.id:
            return True
        
        # Managers and admins can manage any conversation
        if staff.role and staff.role.slug in ['manager', 'admin']:
            return True
        
        return False
```

---

## Common Permission Patterns

### Pattern 1: Staff-Only Endpoint (Any Hotel)
```python
from rest_framework.permissions import IsAuthenticated

class SomeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Check if user is staff
        if not hasattr(request.user, 'staff_profile'):
            return Response({"error": "Staff access required"}, 
                          status=403)
        
        staff = request.user.staff_profile
        # ... rest of logic
```

### Pattern 2: Staff-Only Endpoint (Specific Hotel)
```python
from rest_framework.permissions import IsAuthenticated

class HotelSpecificView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, hotel_slug):
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({"error": "Staff access required"}, 
                          status=403)
        
        # Verify staff belongs to this hotel
        if staff.hotel.slug != hotel_slug:
            return Response(
                {"error": "You don't have access to this hotel"}, 
                status=403
            )
        
        # ... rest of logic
```

### Pattern 3: Using Custom Permission Classes
```python
from rest_framework.permissions import IsAuthenticated
from staff_chat.permissions import IsStaffMember, IsSameHotel

class StaffHotelView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get(self, request, hotel_slug):
        # Permissions already checked!
        staff = request.user.staff_profile
        # ... rest of logic
```

### Pattern 4: Role-Based Access
```python
def get(self, request, hotel_slug):
    staff = request.user.staff_profile
    
    # Check if staff has manager or admin role
    if not staff.role or staff.role.slug not in ['manager', 'admin']:
        return Response(
            {"error": "Manager or Admin access required"}, 
            status=403
        )
    
    # ... rest of logic
```

### Pattern 5: Access Level Check
```python
def post(self, request, hotel_slug):
    staff = request.user.staff_profile
    
    # Check access level
    if staff.access_level not in ['super_staff_admin', 'staff_admin']:
        return Response(
            {"error": "Admin access required"}, 
            status=403
        )
    
    # ... rest of logic
```

---

## URL Routing Patterns

### Pattern 1: Staff-Specific Routes
```python
# URL includes hotel slug
path('staff/<slug:hotel_slug>/settings/', StaffSettingsView.as_view())

# View validates hotel ownership
class StaffSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
```

### Pattern 2: Public Routes with Optional Staff Access
```python
# Public endpoint but different behavior for staff
path('public/hotels/<slug:hotel_slug>/info/', PublicHotelView.as_view())

class PublicHotelView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug):
        # Check if requester is staff
        is_staff = (
            request.user.is_authenticated and 
            hasattr(request.user, 'staff_profile')
        )
        
        if is_staff:
            # Return extra data for staff
            pass
        else:
            # Return public data only
            pass
```

---

## Best Practices

### ✅ DO:

1. **Always check staff_profile exists:**
   ```python
   if not hasattr(request.user, 'staff_profile'):
       return Response({"error": "Staff required"}, status=403)
   ```

2. **Verify hotel ownership for hotel-specific endpoints:**
   ```python
   if staff.hotel.slug != hotel_slug:
       return Response({"error": "Access denied"}, status=403)
   ```

3. **Use custom permission classes for common checks:**
   ```python
   permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
   ```

4. **Handle AttributeError when accessing staff_profile:**
   ```python
   try:
       staff = request.user.staff_profile
   except AttributeError:
       return Response({"error": "Not a staff member"}, status=403)
   ```

### ❌ DON'T:

1. **Don't assume user has staff_profile:**
   ```python
   # BAD:
   staff = request.user.staff_profile  # Can raise AttributeError!
   
   # GOOD:
   try:
       staff = request.user.staff_profile
   except AttributeError:
       return Response({"error": "Staff required"}, status=403)
   ```

2. **Don't skip hotel verification:**
   ```python
   # BAD: Any staff can access any hotel
   staff = request.user.staff_profile
   hotel = Hotel.objects.get(slug=hotel_slug)
   
   # GOOD: Verify ownership
   staff = request.user.staff_profile
   if staff.hotel.slug != hotel_slug:
       return Response({"error": "Access denied"}, status=403)
   ```

3. **Don't use generic IsAuthenticated for staff endpoints:**
   ```python
   # BAD: Guests can access
   permission_classes = [IsAuthenticated]
   
   # GOOD: Explicitly require staff
   permission_classes = [IsAuthenticated, IsStaffMember]
   ```

---

## Example: Complete Staff Endpoint

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from staff_chat.permissions import IsStaffMember, IsSameHotel
from hotel.models import Hotel

class StaffHotelSettingsView(APIView):
    """
    Staff endpoint to manage hotel settings.
    URL: /api/staff/hotels/<hotel_slug>/settings/
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get(self, request, hotel_slug):
        """Get hotel settings"""
        # Permission classes already verified:
        # - User is authenticated
        # - User has staff_profile
        # - Staff belongs to this hotel
        
        staff = request.user.staff_profile
        hotel = staff.hotel
        
        # Your logic here...
        return Response({
            "hotel": hotel.name,
            "staff": f"{staff.first_name} {staff.last_name}"
        })
    
    def put(self, request, hotel_slug):
        """Update hotel settings (admin only)"""
        staff = request.user.staff_profile
        
        # Additional permission: only admins can update
        if staff.access_level not in ['super_staff_admin', 'staff_admin']:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Your update logic here...
        return Response({"message": "Settings updated"})
```

---

## TODO: Future Improvements

1. **Create centralized permission classes module:**
   - Move permissions from `staff_chat/permissions.py` to `common/permissions.py`
   - Make them reusable across all apps

2. **Add more granular permissions:**
   - Permission-based access (like Django's built-in permissions)
   - Custom permission model for feature-level access

3. **Add permission decorators:**
   ```python
   @require_staff_member
   @require_hotel_access
   def my_view(request, hotel_slug):
       pass
   ```

4. **Add audit logging:**
   - Track when staff access resources
   - Log permission denials

---

## Related Files

- `staff/models.py` - Staff, Role, Department, NavigationItem models
- `staff_chat/permissions.py` - Custom permission classes
- `staff/views.py` - Staff CRUD operations and authentication
- `hotel/models.py` - Hotel model

---

## Questions?

When implementing new staff endpoints, ask:
1. Does this endpoint require authentication? → `IsAuthenticated`
2. Does this endpoint require staff access? → `IsStaffMember`
3. Is this endpoint hotel-specific? → `IsSameHotel`
4. Does this require specific roles? → Add role check in view
5. Does this require specific access level? → Add access_level check in view
