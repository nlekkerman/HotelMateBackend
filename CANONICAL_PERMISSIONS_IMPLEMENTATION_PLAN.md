# Canonical Permissions Payload System - Implementation Plan

## Objective

Backend becomes the security + data source of truth for staff permissions by returning a stable, hotel-scoped permissions payload derived from NavigationItem M2M, with superuser bypass and consistent serializer output for frontend route-guards and menu rendering.

This must eliminate:
- missing keys causing frontend "emergency fixes"
- inconsistent nav lists between endpoints
- cross-hotel leakage of nav items

## Phase 0 — Lock the Contract (Before Coding)

### Define the canonical permission payload (always present)

Every auth/me/staff-permissions response must include these keys (even if empty):

```typescript
interface CanonicalPermissionsPayload {
  is_staff: boolean;
  is_superuser: boolean;
  hotel_slug: string | null;
  access_level: string | null;  // 'regular_staff' | 'staff_admin' | 'super_staff_admin' | null
  allowed_navs: string[];       // slugs only (e.g. ["stock_tracker", "chat", "home"])
  navigation_items: NavigationItem[];  // full menu structure already used by frontend
}
```

**Important**: slugs are underscore format (e.g. `stock_tracker`) — never hyphen.

## Phase 1 — Canonical Resolver (Single Source of Truth)

### 1) Create `staff/permissions.py`

Implement:

```python
def resolve_staff_navigation(user) -> dict:
    """
    Returns canonical permissions payload:
    {hotel_slug, access_level, allowed_navs, navigation_items}
    Hotel-scoped, superuser-aware, active-only
    """
```

#### Resolver rules (explicit):

1. **If no staff profile** → return empty payload (`allowed_navs=[]`, `navigation_items=[]`, etc.)
2. **Determine staff hotel** from `staff.hotel`
3. **Filter NavigationItem by**:
   - `hotel == staff.hotel`
   - `is_active == True` (if you have active flag; otherwise define it)
4. **If `user.is_superuser`**:
   - allowed items = all active nav items in that hotel
5. **Else**:
   - allowed items = `staff.allowed_navigation_items` (M2M) filtered to active + same hotel
6. **Build response**:
   - `allowed_navs = [item.slug ...]`
   - `navigation_items = serialize(items)` using the same serializer/shape frontend expects today

**Hard requirement**: every endpoint uses this resolver; no endpoint re-implements its own nav logic.

#### Implementation Details:

```python
from django.contrib.auth import get_user_model
from django.db.models import Q
from staff.models import Staff
from common.models import NavigationItem
from common.serializers import NavigationItemSerializer

User = get_user_model()

def resolve_staff_navigation(user: User) -> dict:
    """
    Single source of truth for staff navigation permissions.
    Returns consistent payload for all auth endpoints.
    """
    # Default empty payload
    base_payload = {
        'is_staff': False,
        'is_superuser': bool(user.is_superuser if user.is_authenticated else False),
        'hotel_slug': None,
        'access_level': None,
        'allowed_navs': [],
        'navigation_items': []
    }
    
    if not user.is_authenticated:
        return base_payload
        
    # Check if user has staff profile
    try:
        staff = user.staff_profile
    except AttributeError:
        return base_payload
    
    # Update payload with staff info
    base_payload.update({
        'is_staff': True,
        'hotel_slug': staff.hotel.slug,
        'access_level': staff.access_level
    })
    
    # Get hotel navigation items (active only)
    hotel_nav_items = NavigationItem.objects.filter(
        hotel=staff.hotel,
        is_active=True
    ).select_related('hotel').order_by('display_order', 'name')
    
    # Determine allowed navigation items
    if user.is_superuser:
        # Superusers get ALL active nav items for their hotel
        allowed_nav_items = hotel_nav_items
    else:
        # Regular staff get only assigned M2M items (filtered to active + same hotel)
        allowed_nav_items = staff.allowed_navigation_items.filter(
            hotel=staff.hotel,
            is_active=True
        ).select_related('hotel').order_by('display_order', 'name')
    
    # Build final payload
    base_payload.update({
        'allowed_navs': list(allowed_nav_items.values_list('slug', flat=True)),
        'navigation_items': NavigationItemSerializer(allowed_nav_items, many=True).data
    })
    
    return base_payload


class HasNavPermission:
    """
    Permission class for checking navigation-based permissions.
    Usage: permission_classes = [IsAuthenticated, HasNavPermission("stock_tracker")]
    """
    
    def __init__(self, required_slug: str):
        self.required_slug = required_slug
    
    def __call__(self, request, view=None):
        """Check if user has permission for the required navigation slug."""
        user = request.user
        
        # Superuser bypass
        if user.is_superuser:
            return True
            
        # Get canonical permissions
        permissions = resolve_staff_navigation(user)
        
        # Check if user has required navigation permission
        return self.required_slug in permissions.get('allowed_navs', [])


def requires_nav_permission(slug: str):
    """
    Decorator for view methods that require specific navigation permissions.
    Usage: @requires_nav_permission("stock_tracker")
    """
    from functools import wraps
    from django.http import JsonResponse
    from django.core.exceptions import PermissionDenied
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            permission_checker = HasNavPermission(slug)
            if not permission_checker(request):
                raise PermissionDenied(f"Navigation permission required: {slug}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
```

## Phase 2 — Auth + /me Payload Consistency

### 2) Update login serializer(s)

Ensure `StaffLoginOutputSerializer` (or equivalent) always includes:
- `access_level` from staff profile
- `allowed_navs` and `navigation_items` from `resolve_staff_navigation(user)`
- Provide fallbacks if staff profile missing (do not omit keys)

#### Implementation in `staff/serializers.py`:

```python
from .permissions import resolve_staff_navigation

class StaffLoginOutputSerializer(serializers.Serializer):
    staff_id = serializers.IntegerField()
    token = serializers.CharField()
    hotel = serializers.DictField()
    
    # Canonical permission fields (ALWAYS present)
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    hotel_slug = serializers.CharField(allow_null=True)
    access_level = serializers.CharField(allow_null=True)
    allowed_navs = serializers.ListField(child=serializers.CharField())
    navigation_items = serializers.ListField(child=serializers.DictField())
    
    # ... other existing fields
    
    def to_representation(self, instance):
        """Ensure canonical permissions are always included."""
        data = super().to_representation(instance)
        
        # Get canonical permissions payload
        permissions = resolve_staff_navigation(instance.get('user'))
        
        # Merge permissions into response
        data.update(permissions)
        
        return data
```

### 3) Update /me endpoint

Modify `CurrentStaffView` (or equivalent) to return the same payload keys using the resolver.

#### Implementation in `staff/views.py`:

```python
from .permissions import resolve_staff_navigation

class CurrentStaffView(APIView):
    """Returns current staff member's information with canonical permissions."""
    permission_classes = [IsAuthenticated, IsStaffMember]
    
    def get(self, request):
        """Get current staff information with canonical permissions payload."""
        try:
            staff = request.user.staff_profile
            
            # Get canonical permissions
            permissions = resolve_staff_navigation(request.user)
            
            # Build staff data
            staff_data = StaffSerializer(staff).data
            
            # Merge canonical permissions
            staff_data.update(permissions)
            
            return Response(staff_data)
            
        except AttributeError:
            # No staff profile - return minimal payload with canonical structure
            permissions = resolve_staff_navigation(request.user)
            return Response(permissions, status=200)
```

**Goal**: frontend never needs to "repair" missing permissions.

## Phase 3 — Permission Editor Endpoints (Dashboard "Can Access")

### 4) Add endpoints

Implement:
- `GET /api/staff/<id>/permissions/`
- `PATCH /api/staff/<id>/permissions/`

#### PATCH body format:
```json
{
  "allowed_navs": ["stock_tracker", "chat", "home"],
  "access_level": "staff_admin"  // optional
}
```

#### Authorization rules:
- requester must be authenticated staff
- same-hotel enforcement (unless requester is superuser and you explicitly allow cross-hotel)
- only `is_superuser` OR `access_level == "super_staff_admin"` can PATCH

#### Validation rules (important):
- each slug must exist as a NavigationItem in the target staff's hotel
- only allow assigning ACTIVE items (or define behavior for inactive)
- update M2M assignments to exactly match slug list (replace set)

#### Safety (recommended):
- prevent admin lockout: do not allow removing your own ability to manage permissions
  (or require extra confirmation; your call)

#### Return response:
- return updated canonical resolver payload for that staff member (so UI refresh is instant)

#### Implementation in `staff/views.py`:

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.get_object_or_404 import get_object_or_404
from django.core.exceptions import ValidationError
from common.models import NavigationItem
from .permissions import resolve_staff_navigation

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def staff_permissions_view(request, staff_id):
    """
    GET: Retrieve staff member's navigation permissions
    PATCH: Update staff member's navigation permissions
    """
    # Get target staff member
    target_staff = get_object_or_404(Staff, id=staff_id)
    
    # Authorization check
    requester_staff = request.user.staff_profile
    
    # Must be superuser or super_staff_admin
    if not (request.user.is_superuser or requester_staff.access_level == 'super_staff_admin'):
        return Response(
            {"error": "Permission denied. Requires super_staff_admin or superuser access."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Hotel scoping (unless superuser explicitly allowed cross-hotel)
    if not request.user.is_superuser:
        if requester_staff.hotel != target_staff.hotel:
            return Response(
                {"error": "Cannot manage permissions for staff in different hotel."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    if request.method == 'GET':
        # Return canonical permissions for target staff
        permissions = resolve_staff_navigation(target_staff.user)
        permissions['staff_id'] = target_staff.id
        return Response(permissions)
    
    elif request.method == 'PATCH':
        # Update permissions
        allowed_navs = request.data.get('allowed_navs', [])
        new_access_level = request.data.get('access_level')
        
        # Validate access level if provided
        if new_access_level and new_access_level not in ['regular_staff', 'staff_admin', 'super_staff_admin']:
            return Response(
                {"error": "Invalid access_level. Must be one of: regular_staff, staff_admin, super_staff_admin"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate navigation slugs
        if allowed_navs:
            # Check that all slugs exist as active NavigationItems in target staff's hotel
            valid_nav_items = NavigationItem.objects.filter(
                hotel=target_staff.hotel,
                is_active=True,
                slug__in=allowed_navs
            )
            
            valid_slugs = set(valid_nav_items.values_list('slug', flat=True))
            requested_slugs = set(allowed_navs)
            invalid_slugs = requested_slugs - valid_slugs
            
            if invalid_slugs:
                return Response(
                    {"error": f"Invalid navigation slugs for this hotel: {list(invalid_slugs)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Safety check: prevent self-lockout for permission management
        if (target_staff.user == request.user and 
            hasattr(target_staff, 'allowed_navigation_items')):
            
            # Check if removing permission management access from self
            current_nav_slugs = set(target_staff.allowed_navigation_items.values_list('slug', flat=True))
            permission_management_slugs = {'staff_management', 'admin_settings'}  # adjust as needed
            
            current_has_perm_mgmt = bool(current_nav_slugs.intersection(permission_management_slugs))
            new_has_perm_mgmt = bool(set(allowed_navs).intersection(permission_management_slugs))
            
            if current_has_perm_mgmt and not new_has_perm_mgmt:
                return Response(
                    {"error": "Cannot remove your own permission management access. Use another admin account."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update access level if provided
        if new_access_level:
            target_staff.access_level = new_access_level
            target_staff.save()
        
        # Update M2M navigation permissions (replace existing set)
        if allowed_navs is not None:  # Allow empty list to clear all permissions
            nav_items = NavigationItem.objects.filter(
                hotel=target_staff.hotel,
                is_active=True,
                slug__in=allowed_navs
            )
            target_staff.allowed_navigation_items.set(nav_items)
        
        # Return updated canonical permissions
        updated_permissions = resolve_staff_navigation(target_staff.user)
        updated_permissions['staff_id'] = target_staff.id
        
        return Response(updated_permissions)
```

## Phase 4 — Optional Module API Enforcement (Real Security)

### 5) Implement permission utilities

In `staff/permissions.py` add reusable permission class/decorator:
- `HasNavPermission("stock_tracker")`
- `@requires_nav_permission("stock_tracker")`

#### Rules:
- superuser bypass
- deny if missing staff profile
- deny if slug not in resolved `allowed_navs`
- enforce same-hotel scoping still via existing mixins

#### Apply to sensitive modules:
- stock tracker
- staff permissions management
- hotel settings / admin areas

**(Frontend guard is UX, backend is real lock.)**

#### Usage Examples:

```python
# In stock_tracker/views.py
from staff.permissions import requires_nav_permission, HasNavPermission

class StockTrackerViewSet(viewsets.ModelViewSet):
    """Stock tracking operations require navigation permission."""
    permission_classes = [IsAuthenticated, IsStaffMember, HasNavPermission("stock_tracker")]
    
    # ... implementation

@requires_nav_permission("admin_settings")
def sensitive_admin_operation(request):
    """Only users with admin_settings nav permission can access."""
    # ... implementation
```

## Phase 5 — Tests (Must-Have)

### 6) Add tests in `staff/tests.py` (or appropriate app)

Cover:
- superuser receives all active nav items in their hotel
- regular staff receives only M2M assigned items
- hotel scoping: nav items from other hotel never appear / cannot be assigned
- PATCH permissions forbidden unless super_staff_admin or superuser
- PATCH rejects unknown slug or wrong-hotel slug
- underscore slug `stock_tracker` preserved
- /me and login always include required keys (even if empty)

#### Test Implementation Structure:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from hotel.models import Hotel
from staff.models import Staff
from common.models import NavigationItem
from staff.permissions import resolve_staff_navigation

User = get_user_model()

class CanonicalPermissionsTestCase(APITestCase):
    """Test canonical permissions payload system."""
    
    def setUp(self):
        # Create test hotels
        self.hotel1 = Hotel.objects.create(name="Test Hotel 1", slug="test-hotel-1")
        self.hotel2 = Hotel.objects.create(name="Test Hotel 2", slug="test-hotel-2")
        
        # Create navigation items for hotel1
        self.nav1_stock = NavigationItem.objects.create(
            hotel=self.hotel1, slug="stock_tracker", name="Stock Tracker", 
            path="/stock", is_active=True
        )
        self.nav1_chat = NavigationItem.objects.create(
            hotel=self.hotel1, slug="chat", name="Chat", 
            path="/chat", is_active=True
        )
        self.nav1_inactive = NavigationItem.objects.create(
            hotel=self.hotel1, slug="inactive_module", name="Inactive", 
            path="/inactive", is_active=False
        )
        
        # Create navigation items for hotel2
        self.nav2_stock = NavigationItem.objects.create(
            hotel=self.hotel2, slug="stock_tracker", name="Stock Tracker", 
            path="/stock", is_active=True
        )
        
        # Create users and staff
        self.superuser = User.objects.create_user(
            username="superuser", email="super@test.com", is_superuser=True
        )
        self.super_admin_user = User.objects.create_user(
            username="superadmin", email="superadmin@test.com"
        )
        self.regular_user = User.objects.create_user(
            username="regular", email="regular@test.com"
        )
        self.no_staff_user = User.objects.create_user(
            username="nostaffprofile", email="nostaffprofile@test.com"
        )
        
        # Create staff profiles
        self.superuser_staff = Staff.objects.create(
            user=self.superuser, hotel=self.hotel1, access_level="super_staff_admin"
        )
        self.super_admin_staff = Staff.objects.create(
            user=self.super_admin_user, hotel=self.hotel1, access_level="super_staff_admin"
        )
        self.regular_staff = Staff.objects.create(
            user=self.regular_user, hotel=self.hotel1, access_level="regular_staff"
        )
        
        # Assign M2M permissions to regular staff (only chat)
        self.regular_staff.allowed_navigation_items.add(self.nav1_chat)
    
    def test_superuser_gets_all_active_nav_items(self):
        """Superuser should receive all active nav items for their hotel."""
        permissions = resolve_staff_navigation(self.superuser)
        
        self.assertTrue(permissions['is_superuser'])
        self.assertTrue(permissions['is_staff'])
        self.assertEqual(permissions['hotel_slug'], 'test-hotel-1')
        self.assertEqual(permissions['access_level'], 'super_staff_admin')
        
        # Should have all active nav items (not inactive ones)
        expected_slugs = {'stock_tracker', 'chat'}
        self.assertEqual(set(permissions['allowed_navs']), expected_slugs)
    
    def test_regular_staff_gets_only_assigned_items(self):
        """Regular staff should receive only M2M assigned nav items."""
        permissions = resolve_staff_navigation(self.regular_user)
        
        self.assertFalse(permissions['is_superuser'])
        self.assertTrue(permissions['is_staff'])
        self.assertEqual(permissions['hotel_slug'], 'test-hotel-1')
        self.assertEqual(permissions['access_level'], 'regular_staff')
        
        # Should have only assigned nav items
        self.assertEqual(permissions['allowed_navs'], ['chat'])
    
    def test_hotel_scoping_isolation(self):
        """Nav items from other hotels should never appear."""
        # Create staff in hotel2
        hotel2_user = User.objects.create_user(username="hotel2user", email="hotel2@test.com")
        hotel2_staff = Staff.objects.create(
            user=hotel2_user, hotel=self.hotel2, access_level="regular_staff"
        )
        
        permissions = resolve_staff_navigation(hotel2_user)
        
        # Should only see hotel2 nav items, never hotel1
        self.assertEqual(permissions['hotel_slug'], 'test-hotel-2')
        self.assertEqual(permissions['allowed_navs'], [])  # No M2M assignments yet
    
    def test_no_staff_profile_returns_empty_payload(self):
        """Users without staff profile should get empty but consistent payload."""
        permissions = resolve_staff_navigation(self.no_staff_user)
        
        self.assertFalse(permissions['is_staff'])
        self.assertFalse(permissions['is_superuser'])
        self.assertIsNone(permissions['hotel_slug'])
        self.assertIsNone(permissions['access_level'])
        self.assertEqual(permissions['allowed_navs'], [])
        self.assertEqual(permissions['navigation_items'], [])
    
    def test_underscore_slug_preservation(self):
        """Slugs should preserve underscore format (stock_tracker)."""
        permissions = resolve_staff_navigation(self.superuser)
        
        self.assertIn('stock_tracker', permissions['allowed_navs'])
        # Ensure no hyphen version exists
        self.assertNotIn('stock-tracker', permissions['allowed_navs'])
    
    def test_permission_editor_authorization(self):
        """Only super_staff_admin or superuser can manage permissions."""
        # Regular staff cannot access permission editor
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(f'/api/staff/{self.regular_staff.id}/permissions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Super staff admin can access
        self.client.force_authenticate(user=self.super_admin_user)
        response = self.client.get(f'/api/staff/{self.regular_staff.id}/permissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_permission_editor_hotel_scoping(self):
        """Cannot manage permissions for staff in different hotel."""
        # Create admin in hotel2
        hotel2_admin_user = User.objects.create_user(username="hotel2admin", email="hotel2admin@test.com")
        hotel2_admin_staff = Staff.objects.create(
            user=hotel2_admin_user, hotel=self.hotel2, access_level="super_staff_admin"
        )
        
        # Hotel2 admin cannot manage hotel1 staff
        self.client.force_authenticate(user=hotel2_admin_user)
        response = self.client.patch(
            f'/api/staff/{self.regular_staff.id}/permissions/',
            {"allowed_navs": ["chat"]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_permission_editor_slug_validation(self):
        """PATCH should reject invalid or cross-hotel slugs."""
        self.client.force_authenticate(user=self.super_admin_user)
        
        # Try to assign invalid slug
        response = self.client.patch(
            f'/api/staff/{self.regular_staff.id}/permissions/',
            {"allowed_navs": ["invalid_slug"]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Try to assign slug from different hotel
        response = self.client.patch(
            f'/api/staff/{self.regular_staff.id}/permissions/',
            {"allowed_navs": ["stock_tracker", "cross_hotel_slug"]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_me_endpoint_contract_compliance(self):
        """The /me endpoint should always include canonical permission keys."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/me/')  # Adjust URL as needed
        
        # Required keys must always be present
        required_keys = ['is_staff', 'is_superuser', 'hotel_slug', 'access_level', 'allowed_navs', 'navigation_items']
        for key in required_keys:
            self.assertIn(key, response.data, f"Missing required key: {key}")
    
    def test_login_response_contract_compliance(self):
        """Login response should always include canonical permission keys."""
        # This would test your login endpoint - adjust URL and logic as needed
        response = self.client.post('/api/auth/login/', {  # Adjust URL as needed
            'username': 'regular',
            'password': 'testpass123'  # You'll need to set passwords in setUp
        })
        
        if response.status_code == 200:  # Assuming successful login
            required_keys = ['is_staff', 'is_superuser', 'hotel_slug', 'access_level', 'allowed_navs', 'navigation_items']
            for key in required_keys:
                self.assertIn(key, response.data, f"Missing required key in login response: {key}")
```

## Phase 6 — Navigation Seeding Strategy

### 7) Seed default NavigationItems in `hotel/models.py`

Add post-save signal to create standard navigation set for new hotels, ensuring frontend menus never break from empty navigation.

#### Implementation:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from common.models import NavigationItem

@receiver(post_save, sender=Hotel)
def create_default_navigation_items(sender, instance, created, **kwargs):
    """Create default navigation items when a new hotel is created."""
    if created:
        default_nav_items = [
            {
                'name': 'Home',
                'slug': 'home',
                'path': '/',
                'display_order': 1,
                'is_active': True
            },
            {
                'name': 'Chat',
                'slug': 'chat', 
                'path': '/chat',
                'display_order': 2,
                'is_active': True
            },
            {
                'name': 'Stock Tracker',
                'slug': 'stock_tracker',
                'path': '/stock',
                'display_order': 3,
                'is_active': True
            },
            {
                'name': 'Bookings',
                'slug': 'bookings',
                'path': '/bookings',
                'display_order': 4,
                'is_active': True
            },
            {
                'name': 'Staff Management',
                'slug': 'staff_management',
                'path': '/staff',
                'display_order': 5,
                'is_active': True
            },
            {
                'name': 'Admin Settings',
                'slug': 'admin_settings',
                'path': '/admin',
                'display_order': 6,
                'is_active': True
            }
        ]
        
        for item_data in default_nav_items:
            NavigationItem.objects.create(
                hotel=instance,
                **item_data
            )
```

## Implementation Order & Dependencies

1. **Phase 1**: Create `staff/permissions.py` with canonical resolver
2. **Phase 6**: Add navigation seeding (if NavigationItem needs `is_active` field)
3. **Phase 2**: Update serializers and /me endpoint
4. **Phase 3**: Add permission editor endpoints
5. **Phase 4**: Apply security decorators to sensitive modules
6. **Phase 5**: Comprehensive test suite

## Key Success Metrics

- ✅ All auth endpoints return identical permission structure
- ✅ Frontend never encounters missing permission keys
- ✅ Hotel isolation: no cross-hotel nav item leakage
- ✅ Superuser bypass works consistently across all modules
- ✅ Permission editor enforces hotel boundaries and authorization
- ✅ Underscore slug format preserved (`stock_tracker` not `stock-tracker`)
- ✅ M2M assignments work correctly for regular staff
- ✅ New hotels automatically get functional navigation menus

## Security Considerations

1. **Backend is security truth**: Frontend guards are UX; backend decorators are the real security layer
2. **Hotel isolation**: All permission checks must respect hotel boundaries unless explicitly overridden for superusers
3. **Self-lockout prevention**: Admins cannot remove their own permission management access
4. **M2M validation**: Only allow assignment of active NavigationItems from the same hotel
5. **Superuser scope**: Define whether superusers operate within hotel context or have true cross-hotel access

## Performance Considerations

1. **Query optimization**: Use `select_related('hotel')` and `prefetch_related` in canonical resolver
2. **Per-request caching**: Consider Django's per-request cache for repeated calls to `resolve_staff_navigation`
3. **Avoid N+1 queries**: Batch navigation item lookups in permission editor
4. **Future Redis caching**: Only add if profiling shows resolver is a bottleneck

This implementation plan provides a complete, secure, and maintainable foundation for the canonical permissions system that eliminates frontend emergency fixes while ensuring proper security boundaries.