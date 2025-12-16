"""
Comprehensive Test Suite for Canonical Permissions System

Tests all scenarios for the hotel-scoped navigation permissions system:
- Superuser bypass logic
- Hotel isolation enforcement  
- M2M assignment validation
- Permission editor security
- Contract compliance across endpoints
- Navigation seeding for new hotels
- Underscore slug preservation
"""

import os
import sys
import django
from django.test.utils import get_runner
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

# Import after Django setup
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from hotel.models import Hotel
from staff.models import Staff, NavigationItem, Department, Role
from staff.permissions import resolve_staff_navigation

User = get_user_model()


class CanonicalPermissionsTestSuite(TestCase):
    """Comprehensive test suite for canonical permissions system."""
    
    def setUp(self):
        """Set up test data for all scenarios."""
        print("\n🔧 Setting up test data...")
        
        # Create test hotels
        self.hotel1 = Hotel.objects.create(
            name="Test Hotel Alpha", 
            slug="test-hotel-alpha"
        )
        self.hotel2 = Hotel.objects.create(
            name="Test Hotel Beta", 
            slug="test-hotel-beta"
        )
        print(f"✅ Created hotels: {self.hotel1.slug}, {self.hotel2.slug}")
        
        # Create departments and roles (or get existing)
        self.department, _ = Department.objects.get_or_create(
            slug="management",
            defaults={'name': "Management"}
        )
        self.role, _ = Role.objects.get_or_create(
            slug="manager",
            defaults={
                'department': self.department,
                'name': "Manager"
            }
        )
        
        # Navigation items should be created by signal for new hotels
        # But let's verify and create manually if needed
        self.setup_navigation_items()
        
        # Create test users
        self.setup_test_users()
        
    def setup_navigation_items(self):
        """Ensure navigation items exist for testing."""
        # Check if navigation seeding worked
        hotel1_nav_count = NavigationItem.objects.filter(hotel=self.hotel1).count()
        hotel2_nav_count = NavigationItem.objects.filter(hotel=self.hotel2).count()
        
        print(f"📊 Navigation items - Hotel1: {hotel1_nav_count}, Hotel2: {hotel2_nav_count}")
        
        if hotel1_nav_count == 0:
            print("⚠️ Navigation seeding didn't work, creating manually...")
            # Create navigation items for hotel1
            nav_items_hotel1 = [
                {'slug': 'home', 'name': 'Home', 'path': '/', 'is_active': True, 'display_order': 1},
                {'slug': 'chat', 'name': 'Chat', 'path': '/chat', 'is_active': True, 'display_order': 2},
                {'slug': 'stock_tracker', 'name': 'Stock Tracker', 'path': '/stock', 'is_active': True, 'display_order': 3},
                {'slug': 'staff_management', 'name': 'Staff Management', 'path': '/staff', 'is_active': True, 'display_order': 4},
                {'slug': 'admin_settings', 'name': 'Admin Settings', 'path': '/admin', 'is_active': True, 'display_order': 5},
                {'slug': 'inactive_module', 'name': 'Inactive Module', 'path': '/inactive', 'is_active': False, 'display_order': 6}
            ]
            
            for item in nav_items_hotel1:
                NavigationItem.objects.create(hotel=self.hotel1, **item)
        
        if hotel2_nav_count == 0:
            # Create fewer items for hotel2 to test isolation
            nav_items_hotel2 = [
                {'slug': 'home', 'name': 'Home', 'path': '/', 'is_active': True, 'display_order': 1},
                {'slug': 'stock_tracker', 'name': 'Stock Tracker', 'path': '/stock', 'is_active': True, 'display_order': 2}
            ]
            
            for item in nav_items_hotel2:
                NavigationItem.objects.create(hotel=self.hotel2, **item)
        
        # Store references to navigation items
        self.nav1_home = NavigationItem.objects.get(hotel=self.hotel1, slug='home')
        self.nav1_chat = NavigationItem.objects.get(hotel=self.hotel1, slug='chat')
        self.nav1_stock = NavigationItem.objects.get(hotel=self.hotel1, slug='stock_tracker')
        self.nav1_staff_mgmt = NavigationItem.objects.get(hotel=self.hotel1, slug='staff_management')
        self.nav1_admin = NavigationItem.objects.get(hotel=self.hotel1, slug='admin_settings')
        
        self.nav2_home = NavigationItem.objects.get(hotel=self.hotel2, slug='home')
        self.nav2_stock = NavigationItem.objects.get(hotel=self.hotel2, slug='stock_tracker')
        
        print("✅ Navigation items configured")
        
    def setup_test_users(self):
        """Create test users and staff profiles."""
        # Superuser in hotel1
        self.superuser = User.objects.create_user(
            username="superuser", 
            email="super@test.com", 
            is_superuser=True
        )
        self.superuser_staff = Staff.objects.create(
            user=self.superuser, 
            hotel=self.hotel1, 
            access_level="super_staff_admin",
            first_name="Super",
            last_name="User",
            department=self.department,
            role=self.role
        )
        
        # Super staff admin in hotel1
        self.super_admin_user = User.objects.create_user(
            username="superadmin", 
            email="superadmin@test.com"
        )
        self.super_admin_staff = Staff.objects.create(
            user=self.super_admin_user, 
            hotel=self.hotel1, 
            access_level="super_staff_admin",
            first_name="Super",
            last_name="Admin",
            department=self.department,
            role=self.role
        )
        
        # Regular staff in hotel1
        self.regular_user = User.objects.create_user(
            username="regular", 
            email="regular@test.com"
        )
        self.regular_staff = Staff.objects.create(
            user=self.regular_user, 
            hotel=self.hotel1, 
            access_level="regular_staff",
            first_name="Regular",
            last_name="Staff",
            department=self.department,
            role=self.role
        )
        
        # Staff in hotel2 for isolation testing
        self.hotel2_admin_user = User.objects.create_user(
            username="hotel2admin", 
            email="hotel2admin@test.com"
        )
        self.hotel2_admin_staff = Staff.objects.create(
            user=self.hotel2_admin_user, 
            hotel=self.hotel2, 
            access_level="super_staff_admin",
            first_name="Hotel2",
            last_name="Admin",
            department=self.department,
            role=self.role
        )
        
        # User without staff profile
        self.no_staff_user = User.objects.create_user(
            username="nostaffprofile", 
            email="nostaffprofile@test.com"
        )
        
        # Assign some M2M permissions to regular staff (only chat and home)
        self.regular_staff.allowed_navigation_items.set([self.nav1_home, self.nav1_chat])
        
        print("✅ Created test users and staff profiles")
    
    def test_1_canonical_resolver_superuser_bypass(self):
        """Test: Superuser receives all active nav items for their hotel."""
        print("\n🧪 TEST 1: Superuser bypass logic")
        
        permissions = resolve_staff_navigation(self.superuser)
        
        # Assertions
        self.assertTrue(permissions['is_superuser'], "Should be marked as superuser")
        self.assertTrue(permissions['is_staff'], "Should be marked as staff")
        self.assertEqual(permissions['hotel_slug'], 'test-hotel-alpha')
        self.assertEqual(permissions['access_level'], 'super_staff_admin')
        
        # Should have all active nav items (not inactive ones)
        expected_slugs = {'home', 'chat', 'stock_tracker', 'staff_management', 'admin_settings'}
        actual_slugs = set(permissions['allowed_navs'])
        
        self.assertEqual(actual_slugs, expected_slugs, 
                        f"Superuser should get all active nav items. Expected: {expected_slugs}, Got: {actual_slugs}")
        
        # Should not have inactive items
        self.assertNotIn('inactive_module', permissions['allowed_navs'])
        
        print("✅ Superuser bypass working correctly")
        
    def test_2_regular_staff_m2m_restrictions(self):
        """Test: Regular staff receives only M2M assigned nav items."""
        print("\n🧪 TEST 2: Regular staff M2M restrictions")
        
        permissions = resolve_staff_navigation(self.regular_user)
        
        # Assertions
        self.assertFalse(permissions['is_superuser'], "Should not be superuser")
        self.assertTrue(permissions['is_staff'], "Should be staff")
        self.assertEqual(permissions['hotel_slug'], 'test-hotel-alpha')
        self.assertEqual(permissions['access_level'], 'regular_staff')
        
        # Should only have assigned nav items (home, chat)
        expected_slugs = {'home', 'chat'}
        actual_slugs = set(permissions['allowed_navs'])
        
        self.assertEqual(actual_slugs, expected_slugs,
                        f"Regular staff should only get M2M assigned items. Expected: {expected_slugs}, Got: {actual_slugs}")
        
        print("✅ Regular staff M2M restrictions working correctly")
        
    def test_3_hotel_isolation_enforcement(self):
        """Test: Nav items from other hotels never appear."""
        print("\n🧪 TEST 3: Hotel isolation enforcement")
        
        # Hotel2 admin should only see hotel2 nav items
        permissions = resolve_staff_navigation(self.hotel2_admin_user)
        
        self.assertEqual(permissions['hotel_slug'], 'test-hotel-beta')
        
        # Hotel2 only has 'home' and 'stock_tracker' 
        expected_slugs = {'home', 'stock_tracker'}
        actual_slugs = set(permissions['allowed_navs'])
        
        self.assertEqual(actual_slugs, expected_slugs,
                        f"Hotel2 admin should only see hotel2 items. Expected: {expected_slugs}, Got: {actual_slugs}")
        
        # Should never see hotel1-specific items like 'chat'
        self.assertNotIn('chat', permissions['allowed_navs'])
        
        print("✅ Hotel isolation working correctly")
        
    def test_4_no_staff_profile_empty_payload(self):
        """Test: Users without staff profile get empty but consistent payload."""
        print("\n🧪 TEST 4: No staff profile handling")
        
        permissions = resolve_staff_navigation(self.no_staff_user)
        
        # Contract compliance - all keys must be present
        required_keys = ['is_staff', 'is_superuser', 'hotel_slug', 'access_level', 'allowed_navs', 'navigation_items']
        for key in required_keys:
            self.assertIn(key, permissions, f"Missing required key: {key}")
        
        # Values should be empty/null but consistent
        self.assertFalse(permissions['is_staff'])
        self.assertFalse(permissions['is_superuser'])
        self.assertIsNone(permissions['hotel_slug'])
        self.assertIsNone(permissions['access_level'])
        self.assertEqual(permissions['allowed_navs'], [])
        self.assertEqual(permissions['navigation_items'], [])
        
        print("✅ No staff profile handling working correctly")
        
    def test_5_underscore_slug_preservation(self):
        """Test: Slugs preserve underscore format (stock_tracker)."""
        print("\n🧪 TEST 5: Underscore slug preservation")
        
        permissions = resolve_staff_navigation(self.superuser)
        
        # Check for underscore format
        self.assertIn('stock_tracker', permissions['allowed_navs'])
        self.assertIn('staff_management', permissions['allowed_navs'])
        self.assertIn('admin_settings', permissions['allowed_navs'])
        
        # Ensure no hyphen versions exist
        hyphen_variants = ['stock-tracker', 'staff-management', 'admin-settings']
        for variant in hyphen_variants:
            self.assertNotIn(variant, permissions['allowed_navs'], 
                           f"Found hyphen variant: {variant}")
        
        print("✅ Underscore slug preservation working correctly")
        
    def test_6_permission_editor_view_logic(self):
        """Test: Permission editor view logic and authorization."""
        print("\n🧪 TEST 6: Permission editor view logic")
        
        # Import the view class
        from staff.views import StaffNavigationPermissionsView
        
        view = StaffNavigationPermissionsView()
        
        # Test authorization method
        can_manage = view._check_authorization(self.super_admin_user, self.regular_staff)
        self.assertTrue(can_manage, "Super admin should be able to manage permissions")
        
        cannot_manage = view._check_authorization(self.regular_user, self.regular_staff)
        self.assertFalse(cannot_manage, "Regular staff should not be able to manage permissions")
        
        # Test cross-hotel restriction
        cross_hotel = view._check_authorization(self.hotel2_admin_user, self.regular_staff)
        self.assertFalse(cross_hotel, "Cross-hotel management should be forbidden")
        
        # Test superuser bypass
        superuser_can = view._check_authorization(self.superuser, self.regular_staff)
        self.assertTrue(superuser_can, "Superuser should bypass hotel restrictions")
        
        print("✅ Permission editor view logic working correctly")
        
    def test_7_m2m_assignment_updates(self):
        """Test: M2M assignment updates work correctly."""
        print("\n🧪 TEST 7: M2M assignment updates")
        
        # Initially regular staff has home and chat
        initial_permissions = resolve_staff_navigation(self.regular_user)
        initial_slugs = set(initial_permissions['allowed_navs'])
        expected_initial = {'home', 'chat'}
        self.assertEqual(initial_slugs, expected_initial, "Initial M2M assignment incorrect")
        
        # Update M2M assignment to include stock_tracker
        new_nav_items = [self.nav1_home, self.nav1_stock, self.nav1_staff_mgmt]
        self.regular_staff.allowed_navigation_items.set(new_nav_items)
        
        # Verify update
        updated_permissions = resolve_staff_navigation(self.regular_user)
        updated_slugs = set(updated_permissions['allowed_navs'])
        expected_updated = {'home', 'stock_tracker', 'staff_management'}
        
        self.assertEqual(updated_slugs, expected_updated,
                        f"M2M update failed. Expected: {expected_updated}, Got: {updated_slugs}")
        
        print("✅ M2M assignment updates working correctly")
        
    def test_8_slug_validation_logic(self):
        """Test: Slug validation for hotel scoping."""
        print("\n🧪 TEST 8: Slug validation logic")
        
        # Test valid slugs from same hotel
        hotel1_slugs = ['home', 'chat', 'stock_tracker']
        valid_items = NavigationItem.objects.filter(
            hotel=self.hotel1,
            is_active=True,
            slug__in=hotel1_slugs
        )
        
        self.assertEqual(len(valid_items), len(hotel1_slugs),
                        "All hotel1 slugs should be valid")
        
        # Test invalid slug
        invalid_items = NavigationItem.objects.filter(
            hotel=self.hotel1,
            is_active=True,
            slug__in=['nonexistent_slug']
        )
        
        self.assertEqual(len(invalid_items), 0,
                        "Invalid slugs should not match any items")
        
        # Test cross-hotel slug leakage prevention
        hotel1_only_items = NavigationItem.objects.filter(
            hotel=self.hotel1,
            is_active=True,
            slug='chat'  # Chat only exists in hotel1
        )
        
        hotel2_chat_items = NavigationItem.objects.filter(
            hotel=self.hotel2,
            is_active=True,
            slug='chat'  # Should not exist in hotel2
        )
        
        self.assertEqual(len(hotel1_only_items), 1, "Chat should exist in hotel1")
        self.assertEqual(len(hotel2_chat_items), 0, "Chat should not exist in hotel2")
        
        print("✅ Slug validation logic working correctly")
        
    def test_9_serializer_contract_compliance(self):
        """Test: Serializers include all canonical permission keys."""
        print("\n🧪 TEST 9: Serializer contract compliance")
        
        # Test login output serializer
        from staff.serializers import StaffLoginOutputSerializer
        
        # Create test data
        test_data = {
            'staff_id': self.regular_staff.id,
            'username': self.regular_user.username,
            'token': 'test_token',
            'hotel_id': self.hotel1.id,
            'hotel_name': self.hotel1.name,
            'hotel': {
                'id': self.hotel1.id,
                'name': self.hotel1.name,
                'slug': self.hotel1.slug,
            },
            'profile_image_url': None,
            'role': 'Manager',
            'department': 'Management',
            'user': self.regular_user  # For to_representation method
        }
        
        serializer = StaffLoginOutputSerializer(test_data)
        serialized_data = serializer.data
        
        # Check all required canonical keys
        required_keys = ['is_staff', 'is_superuser', 'hotel_slug', 'access_level', 'allowed_navs', 'navigation_items']
        for key in required_keys:
            self.assertIn(key, serialized_data, f"Serializer output missing required key: {key}")
        
        # Verify data correctness
        self.assertTrue(serialized_data['is_staff'])
        self.assertFalse(serialized_data['is_superuser'])
        self.assertEqual(serialized_data['hotel_slug'], 'test-hotel-alpha')
        self.assertEqual(serialized_data['access_level'], 'regular_staff')
        
        print("✅ Serializer contract compliance working correctly")
        
    def test_10_canonical_resolver_consistency(self):
        """Test: Canonical resolver returns consistent data structure."""
        print("\n🧪 TEST 10: Canonical resolver consistency")
        
        # Test multiple calls return same structure
        permissions1 = resolve_staff_navigation(self.regular_user)
        permissions2 = resolve_staff_navigation(self.regular_user)
        
        # Should have identical structure and content
        self.assertEqual(permissions1, permissions2, "Resolver should be consistent")
        
        # Test with different users but same structure
        super_permissions = resolve_staff_navigation(self.superuser)
        regular_permissions = resolve_staff_navigation(self.regular_user)
        
        # Should have same keys but different values
        self.assertEqual(set(super_permissions.keys()), set(regular_permissions.keys()),
                        "All users should get same key structure")
        
        # But different permission values
        self.assertNotEqual(super_permissions['allowed_navs'], regular_permissions['allowed_navs'],
                           "Different users should have different permissions")
        
        print("✅ Canonical resolver consistency working correctly")
        
    def test_11_navigation_seeding_verification(self):
        """Test: New hotels automatically get default navigation items."""
        print("\n🧪 TEST 11: Navigation seeding verification")
        
        # Create a new hotel and check if navigation items were created
        new_hotel = Hotel.objects.create(
            name="Test Hotel Gamma", 
            slug="test-hotel-gamma"
        )
        
        # Check if navigation items were created by signal
        nav_items = NavigationItem.objects.filter(hotel=new_hotel)
        nav_count = nav_items.count()
        
        # Should have at least the default navigation items
        self.assertGreater(nav_count, 0, "New hotel should have navigation items created by signal")
        
        # Check for expected default slugs
        nav_slugs = set(nav_items.values_list('slug', flat=True))
        expected_defaults = {'home', 'stock_tracker', 'staff_management'}
        
        # At least some defaults should exist
        intersection = nav_slugs.intersection(expected_defaults)
        self.assertGreater(len(intersection), 0, 
                          f"New hotel should have some default nav items. Found: {nav_slugs}")
        
        print(f"✅ Navigation seeding working - new hotel has {nav_count} items: {list(nav_slugs)}")
        
    def test_12_superuser_cross_hotel_access(self):
        """Test: Superuser navigation scope within hotel context."""
        print("\n🧪 TEST 12: Superuser cross-hotel access patterns")
        
        # Superuser in hotel1 should only see hotel1 nav items
        permissions = resolve_staff_navigation(self.superuser)
        
        # Should see all hotel1 items but not hotel2-specific items
        hotel1_nav_slugs = set(NavigationItem.objects.filter(
            hotel=self.hotel1, is_active=True
        ).values_list('slug', flat=True))
        
        actual_slugs = set(permissions['allowed_navs'])
        self.assertEqual(actual_slugs, hotel1_nav_slugs,
                        "Superuser should see all nav items from their own hotel only")
        
        print("✅ Superuser cross-hotel access working correctly")
        
    def run_all_tests(self):
        """Run all test methods in sequence."""
        test_methods = [method for method in dir(self) if method.startswith('test_')]
        test_methods.sort()  # Run tests in order
        
        print(f"\n🚀 Running {len(test_methods)} comprehensive tests...")
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                method = getattr(self, test_method)
                method()
                passed += 1
            except Exception as e:
                print(f"❌ {test_method} FAILED: {e}")
                failed += 1
                
        print(f"\n📊 TEST SUMMARY:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        return passed, failed


def run_comprehensive_test_suite():
    """Main test runner function."""
    print("🔬 CANONICAL PERMISSIONS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    try:
        # Create test instance
        test_suite = CanonicalPermissionsTestSuite()
        
        # Setup test environment
        test_suite.setUp()
        
        # Run all tests
        passed, failed = test_suite.run_all_tests()
        
        if failed == 0:
            print(f"\n🎉 ALL TESTS PASSED! The canonical permissions system is working correctly.")
            return True
        else:
            print(f"\n⚠️ Some tests failed. Please review the implementation.")
            return False
            
    except Exception as e:
        print(f"❌ Test suite setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_comprehensive_test_suite()
    sys.exit(0 if success else 1)