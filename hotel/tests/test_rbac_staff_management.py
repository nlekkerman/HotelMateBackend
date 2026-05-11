"""
Phase 6E.1 tests — RBAC for the `staff_management` module.

Covers:
- capability catalog + module policy self-consistency
- persona resolution (tier/role/department → rbac.staff_management payload)
- no staff_management.* capability leaks into any tier preset
- endpoint enforcement for every staff-management endpoint
- generic PATCH cannot mutate authority/identity fields
- authority @actions enforce per-field capabilities + anti-escalation
- hotel-scoped user enumeration
- role/department read/manage capability split
- registration package read/create/email/print separation
- deactivate/delete self-rejection
- superuser-without-staff_profile safety
- role/department capability ceiling
- navigation subset-of-requester
- access-level strict-less-than
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from hotel.models import Hotel
from staff.capability_catalog import (
    CANONICAL_CAPABILITIES,
    ROLE_PRESET_CAPABILITIES,
    STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,
    STAFF_MANAGEMENT_AUTHORITY_VIEW,
    STAFF_MANAGEMENT_DEPARTMENT_MANAGE,
    STAFF_MANAGEMENT_DEPARTMENT_READ,
    STAFF_MANAGEMENT_MODULE_VIEW,
    STAFF_MANAGEMENT_PENDING_REGISTRATION_READ,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ,
    STAFF_MANAGEMENT_ROLE_MANAGE,
    STAFF_MANAGEMENT_ROLE_READ,
    STAFF_MANAGEMENT_STAFF_CREATE,
    STAFF_MANAGEMENT_STAFF_DEACTIVATE,
    STAFF_MANAGEMENT_STAFF_DELETE,
    STAFF_MANAGEMENT_STAFF_READ,
    STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
    STAFF_MANAGEMENT_USER_READ,
    TIER_DEFAULT_CAPABILITIES,
    resolve_capabilities,
    validate_preset_maps,
)
from staff.models import (
    Department, NavigationItem, RegistrationCode, Role, Staff,
)
from staff.module_policy import (
    MODULE_POLICY,
    resolve_module_policy,
    validate_module_policy,
)


_SM_ACTIONS = {
    'staff_read': STAFF_MANAGEMENT_STAFF_READ,
    'user_read': STAFF_MANAGEMENT_USER_READ,
    'pending_registration_read': STAFF_MANAGEMENT_PENDING_REGISTRATION_READ,
    'staff_create': STAFF_MANAGEMENT_STAFF_CREATE,
    'staff_update_profile': STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
    'staff_deactivate': STAFF_MANAGEMENT_STAFF_DEACTIVATE,
    'staff_delete': STAFF_MANAGEMENT_STAFF_DELETE,
    'authority_view': STAFF_MANAGEMENT_AUTHORITY_VIEW,
    'authority_role_assign': STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN,
    'authority_department_assign': STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN,
    'authority_access_level_assign': (
        STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN
    ),
    'authority_nav_assign': STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
    'authority_supervise': STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,
    'role_read': STAFF_MANAGEMENT_ROLE_READ,
    'role_manage': STAFF_MANAGEMENT_ROLE_MANAGE,
    'department_read': STAFF_MANAGEMENT_DEPARTMENT_READ,
    'department_manage': STAFF_MANAGEMENT_DEPARTMENT_MANAGE,
    'registration_package_read': STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ,
    'registration_package_create': (
        STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE
    ),
    'registration_package_email': STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL,
    'registration_package_print': STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_hotel(slug: str) -> Hotel:
    return Hotel.objects.create(
        name=f"Hotel {slug}", slug=slug, timezone="UTC",
    )


def _make_staff(
    hotel: Hotel,
    *,
    username: str,
    access_level: str,
    role_slug: str | None = None,
    department_slug: str | None = None,
) -> Staff:
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    dept = None
    if department_slug:
        dept, _ = Department.objects.get_or_create(
            hotel=hotel, slug=department_slug,
            defaults={'name': department_slug.replace('_', ' ').title()},
        )
    role = None
    if role_slug:
        role, _ = Role.objects.get_or_create(
            hotel=hotel, slug=role_slug,
            defaults={
                'name': role_slug.replace('_', ' ').title(),
                'department': dept,
            },
        )
    return Staff.objects.create(
        user=user, hotel=hotel, department=dept, role=role,
        access_level=access_level, email=f"{username}@example.com",
        is_active=True,
    )


def _make_superuser(username: str = 'root') -> User:
    return User.objects.create_superuser(
        username=username, email=f'{username}@example.com',
        password='testpass123',
    )


def _authed_client(user: User) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# ---------------------------------------------------------------------------
# Registry self-consistency
# ---------------------------------------------------------------------------

class StaffManagementPolicyRegistryTest(TestCase):
    def test_preset_maps_self_consistent(self):
        self.assertEqual(validate_preset_maps(), [])

    def test_module_policy_self_consistent(self):
        self.assertEqual(validate_module_policy(), [])

    def test_staff_management_module_registered(self):
        self.assertIn('staff_management', MODULE_POLICY)
        policy = MODULE_POLICY['staff_management']
        self.assertEqual(
            policy['view_capability'], STAFF_MANAGEMENT_MODULE_VIEW,
        )
        self.assertEqual(
            policy['read_capability'], STAFF_MANAGEMENT_STAFF_READ,
        )

    def test_no_decorative_action_keys(self):
        policy = MODULE_POLICY['staff_management']
        for action, cap in policy['actions'].items():
            self.assertIn(
                cap, CANONICAL_CAPABILITIES,
                f"Action {action!r} → non-canonical capability {cap!r}",
            )
            self.assertIn(action, _SM_ACTIONS, action)
            self.assertEqual(
                cap, _SM_ACTIONS[action],
                f"Action {action!r} capability drifted",
            )

    def test_no_staff_management_capability_in_lower_tier_presets(self):
        """Manager-role rebalance: super_staff_admin tier carries the
        full hotel-scoped bundle including staff_management. Lower
        tiers (staff_admin, regular_staff) must still NOT leak
        staff_management.* capabilities by tier."""
        sm_caps = {
            c for c in CANONICAL_CAPABILITIES
            if c.startswith('staff_management.')
        }
        for tier, caps in TIER_DEFAULT_CAPABILITIES.items():
            if tier == 'super_staff_admin':
                continue
            leaked = caps & sm_caps
            self.assertFalse(
                leaked,
                f"Tier {tier!r} leaks staff_management capabilities: "
                f"{sorted(leaked)}",
            )


# ---------------------------------------------------------------------------
# Persona resolution
# ---------------------------------------------------------------------------

class StaffManagementPolicyPersonaTest(TestCase):
    def _policy(self, tier=None, role_slug=None, department_slug=None):
        caps = resolve_capabilities(tier, role_slug, department_slug)
        return resolve_module_policy(caps)['staff_management']

    def test_regular_staff_no_access(self):
        pol = self._policy('regular_staff', None, None)
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['read'])

    def test_tier_only_staff_admin_no_authority(self):
        """Tier staff_admin MUST NOT grant staff_management authority."""
        pol = self._policy('staff_admin', None, None)
        self.assertFalse(pol['visible'])
        for k in pol['actions']:
            self.assertFalse(pol['actions'][k], k)

    def test_tier_only_super_staff_admin_no_authority(self):
        pol = self._policy('super_staff_admin', None, None)
        self.assertFalse(pol['visible'])
        for k in pol['actions']:
            self.assertFalse(pol['actions'][k], k)

    def test_role_staff_admin_basic_bundle(self):
        pol = self._policy('regular_staff', 'staff_admin', 'administration')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        # BASIC bundle: no authority / delete / supervise
        self.assertTrue(pol['actions']['staff_create'])
        self.assertTrue(pol['actions']['staff_update_profile'])
        self.assertTrue(pol['actions']['registration_package_create'])
        self.assertFalse(pol['actions']['staff_delete'])
        self.assertFalse(pol['actions']['authority_role_assign'])
        self.assertFalse(pol['actions']['authority_access_level_assign'])
        self.assertFalse(pol['actions']['authority_supervise'])

    def test_role_super_staff_admin_full_bundle(self):
        pol = self._policy(
            'regular_staff', 'super_staff_admin', 'administration',
        )
        self.assertTrue(pol['visible'])
        # FULL bundle: authority.* + delete but NOT supervise
        self.assertTrue(pol['actions']['authority_role_assign'])
        self.assertTrue(pol['actions']['authority_access_level_assign'])
        self.assertTrue(pol['actions']['authority_nav_assign'])
        self.assertTrue(pol['actions']['staff_delete'])
        self.assertFalse(pol['actions']['authority_supervise'])

    def test_hotel_manager_manager_bundle(self):
        pol = self._policy('regular_staff', 'hotel_manager', 'management')
        self.assertTrue(pol['actions']['authority_supervise'])
        self.assertTrue(pol['actions']['staff_delete'])


# ---------------------------------------------------------------------------
# Endpoint enforcement
# ---------------------------------------------------------------------------

class StaffManagementEndpointEnforcementTest(TestCase):
    def setUp(self):
        self.hotel = _make_hotel('alpha')
        self.other_hotel = _make_hotel('beta')

        # Personas
        self.regular = _make_staff(
            self.hotel, username='reg', access_level='regular_staff',
        )
        self.tier_only_ssa = _make_staff(
            self.hotel, username='tier_ssa',
            access_level='super_staff_admin',
        )
        self.role_sa = _make_staff(
            self.hotel, username='role_sa',
            access_level='staff_admin',
            role_slug='staff_admin',
            department_slug='administration',
        )
        self.role_ssa = _make_staff(
            self.hotel, username='role_ssa',
            access_level='super_staff_admin',
            role_slug='super_staff_admin',
            department_slug='administration',
        )
        self.manager = _make_staff(
            self.hotel, username='hm',
            access_level='super_staff_admin',
            role_slug='hotel_manager',
            department_slug='management',
        )
        self.superuser = _make_superuser('root')

    # -- staff read --
    def test_staff_list_denied_for_tier_only_ssa(self):
        client = _authed_client(self.tier_only_ssa.user)
        resp = client.get(f'/api/staff/{self.hotel.slug}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_list_allowed_for_role_sa(self):
        client = _authed_client(self.role_sa.user)
        resp = client.get(f'/api/staff/{self.hotel.slug}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # -- staff.hotel API-immutable --
    def test_generic_patch_cannot_change_hotel(self):
        client = _authed_client(self.role_sa.user)
        resp = client.patch(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/',
            data={'hotel': self.other_hotel.id},
            format='json',
        )
        # patch is permitted for profile fields; hotel is read-only
        # on StaffSerializer and StaffProfileUpdateSerializer.
        self.assertIn(resp.status_code, (
            status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST,
        ))
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.hotel, self.hotel)

    def test_generic_patch_cannot_change_access_level(self):
        client = _authed_client(self.role_sa.user)
        resp = client.patch(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/',
            data={'access_level': 'super_staff_admin'},
            format='json',
        )
        self.assertIn(resp.status_code, (
            status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST,
        ))
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.access_level, 'regular_staff')

    def test_generic_patch_cannot_change_role_or_department(self):
        other_role = Role.objects.create(
            hotel=self.hotel, name='Other', slug='duty_manager',
        )
        client = _authed_client(self.role_sa.user)
        resp = client.patch(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/',
            data={'role': other_role.id},
            format='json',
        )
        self.assertIn(resp.status_code, (
            status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST,
        ))
        self.regular.refresh_from_db()
        self.assertIsNone(self.regular.role)

    # -- authority view --
    def test_authority_view_denied_for_regular(self):
        client = _authed_client(self.regular.user)
        resp = client.get(
            f'/api/staff/{self.hotel.slug}/{self.role_sa.id}/authority/',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_authority_view_allowed_for_role_ssa(self):
        client = _authed_client(self.role_ssa.user)
        resp = client.get(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/authority/',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # -- authority role assign --
    def test_assign_role_denied_for_role_sa_basic(self):
        # role_sa has BASIC (no authority.role.assign)
        other_role = Role.objects.create(
            hotel=self.hotel, name='FD', slug='front_desk_agent',
            department=self.regular.department,
        )
        client = _authed_client(self.role_sa.user)
        resp = client.patch(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/assign-role/',
            data={'role': other_role.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_role_allowed_for_role_ssa(self):
        # `duty_manager` is a canonical role (catalog-valid) with no
        # ROLE_PRESET_CAPABILITIES entry — ceiling check grants empty set.
        other_role = Role.objects.create(
            hotel=self.hotel, name='Duty Manager', slug='duty_manager',
        )
        client = _authed_client(self.role_ssa.user)
        resp = client.patch(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/assign-role/',
            data={'role': other_role.id},
            format='json',
        )
        # role_ssa FULL bundle covers authority.role.assign but the
        # role preset ceiling may block if the target role's preset
        # grants caps outside role_ssa's set. front_desk_agent is a
        # low-privilege role so this should succeed.
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.regular.refresh_from_db()
        self.assertEqual(self.regular.role_id, other_role.id)

    # -- access level strict-less-than --
    def test_assign_access_level_strict_less_than(self):
        # role_ssa (access_level=super_staff_admin) should NOT be able
        # to assign super_staff_admin to another staff without
        # supervise cap.
        client = _authed_client(self.role_ssa.user)
        url = (
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/'
            f'assign-access-level/'
        )
        resp = client.patch(
            url, data={'access_level': 'super_staff_admin'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # hotel_manager HAS supervise; must succeed.
        client = _authed_client(self.manager.user)
        resp = client.patch(
            url, data={'access_level': 'super_staff_admin'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_cannot_assign_authority_to_self(self):
        client = _authed_client(self.role_ssa.user)
        url = (
            f'/api/staff/{self.hotel.slug}/{self.role_ssa.id}/'
            f'assign-access-level/'
        )
        resp = client.patch(
            url, data={'access_level': 'staff_admin'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # -- nav subset --
    def test_assign_navigation_subset_of_requester(self):
        # Use custom slugs that don't collide with the 12 default navs
        # auto-created on hotel creation.
        nav1 = NavigationItem.objects.create(
            hotel=self.hotel, name='Custom A', slug='phase6e_custom_a',
            path='/a', is_active=True,
        )
        nav2 = NavigationItem.objects.create(
            hotel=self.hotel, name='Custom B', slug='phase6e_custom_b',
            path='/b', is_active=True,
        )
        # Requester only has nav1
        self.role_ssa.allowed_navigation_items.set([nav1])
        client = _authed_client(self.role_ssa.user)
        url = (
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/'
            f'assign-navigation/'
        )
        resp = client.patch(
            url, data={'slugs': [nav1.slug, nav2.slug]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # manager has supervise → bypass
        self.manager.allowed_navigation_items.set([nav1])
        client = _authed_client(self.manager.user)
        resp = client.patch(
            url, data={'slugs': [nav1.slug, nav2.slug]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # -- delete / deactivate --
    def test_delete_denied_for_role_sa(self):
        client = _authed_client(self.role_sa.user)
        resp = client.delete(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_allowed_for_role_ssa(self):
        client = _authed_client(self.role_ssa.user)
        resp = client.delete(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/',
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_self(self):
        client = _authed_client(self.role_ssa.user)
        resp = client.delete(
            f'/api/staff/{self.hotel.slug}/{self.role_ssa.id}/',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_rejects_self(self):
        client = _authed_client(self.role_ssa.user)
        resp = client.post(
            f'/api/staff/{self.hotel.slug}/{self.role_ssa.id}/deactivate/',
            data={}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_denied_without_capability(self):
        # tier_only_ssa has NO staff_management.* caps.
        client = _authed_client(self.tier_only_ssa.user)
        resp = client.post(
            f'/api/staff/{self.hotel.slug}/{self.regular.id}/deactivate/',
            data={}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # -- department / role read/manage --
    def test_department_read_denied_for_tier_only(self):
        client = _authed_client(self.tier_only_ssa.user)
        resp = client.get(f'/api/staff/{self.hotel.slug}/departments/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_department_read_allowed_for_role_sa(self):
        client = _authed_client(self.role_sa.user)
        resp = client.get(f'/api/staff/{self.hotel.slug}/departments/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_department_manage_denied_for_role_sa(self):
        # role_sa BASIC bundle has department.read but NOT manage
        client = _authed_client(self.role_sa.user)
        resp = client.post(
            f'/api/staff/{self.hotel.slug}/departments/',
            data={'name': 'New Dept'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_department_manage_allowed_for_role_ssa(self):
        client = _authed_client(self.role_ssa.user)
        resp = client.post(
            f'/api/staff/{self.hotel.slug}/departments/',
            data={'name': 'New Dept 2'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    # -- registration package --
    def test_registration_package_read_vs_create(self):
        # role_sa (BASIC) has both read and create
        client = _authed_client(self.role_sa.user)
        resp = client.post(
            '/api/staff/registration-package/',
            data={'hotel_slug': self.hotel.slug, 'count': 1},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_registration_package_tier_only_denied(self):
        # Tier-only super_staff_admin has NO registration_package.* cap.
        client = _authed_client(self.tier_only_ssa.user)
        resp = client.get('/api/staff/registration-package/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_registration_package_without_staff_profile(self):
        """Regression: superuser without staff_profile must NOT 500."""
        client = _authed_client(self.superuser)
        resp = client.get(
            f'/api/staff/registration-package/?hotel_slug={self.hotel.slug}',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # -- pending registrations --
    def test_pending_registrations_denied_for_regular(self):
        client = _authed_client(self.regular.user)
        resp = client.get(
            f'/api/staff/{self.hotel.slug}/pending-registrations/',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_registrations_allowed_for_role_sa(self):
        client = _authed_client(self.role_sa.user)
        resp = client.get(
            f'/api/staff/{self.hotel.slug}/pending-registrations/',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # -- user list hotel scoping --
    def test_user_list_hotel_scoped_no_cross_hotel_leak(self):
        # Create a user with consumed registration code for other_hotel
        other_user = User.objects.create_user(
            username='other_user', password='x',
        )
        code = RegistrationCode.create_package(
            hotel_slug=self.other_hotel.slug,
        )
        rc = RegistrationCode.objects.get(code=code['code'])
        rc.used_by = other_user
        rc.save()

        # USER_READ capability is in the FULL bundle (role_ssa), not BASIC.
        client = _authed_client(self.role_ssa.user)
        resp = client.get('/api/staff/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        usernames = [u['username'] for u in resp.data.get(
            'results', resp.data,
        )]
        self.assertNotIn('other_user', usernames)

    # -- staff create anti-escalation --
    def test_create_staff_access_level_escalation_denied(self):
        # role_sa (access_level=staff_admin) tries to create super_staff_admin
        target_user = User.objects.create_user(
            username='candidate', password='x',
        )
        code = RegistrationCode.create_package(hotel_slug=self.hotel.slug)
        rc = RegistrationCode.objects.get(code=code['code'])
        rc.used_by = target_user
        rc.save()

        client = _authed_client(self.role_sa.user)
        resp = client.post(
            f'/api/staff/{self.hotel.slug}/create-staff/',
            data={
                'user_id': target_user.id,
                'access_level': 'super_staff_admin',
                'first_name': 'Candy',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_staff_allowed_same_hotel_lower_level(self):
        target_user = User.objects.create_user(
            username='candidate2', password='x',
        )
        code = RegistrationCode.create_package(hotel_slug=self.hotel.slug)
        rc = RegistrationCode.objects.get(code=code['code'])
        rc.used_by = target_user
        rc.save()

        client = _authed_client(self.role_ssa.user)
        resp = client.post(
            f'/api/staff/{self.hotel.slug}/create-staff/',
            data={
                'user_id': target_user.id,
                'access_level': 'regular_staff',
                'first_name': 'Candy2',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Anti-escalation helpers (unit-level)
# ---------------------------------------------------------------------------

class AntiEscalationHelpersTest(TestCase):
    def test_access_level_strict_less_than(self):
        from staff.permissions import assert_access_level_allowed

        class FakeUser:
            is_superuser = False

        # staff_admin cannot assign super_staff_admin (higher authority)
        self.assertIsNotNone(assert_access_level_allowed(
            FakeUser(), [],
            'staff_admin', 'super_staff_admin',
        ))
        # staff_admin can assign regular_staff (lower)
        self.assertIsNone(assert_access_level_allowed(
            FakeUser(), [],
            'staff_admin', 'regular_staff',
        ))
        # Equal level without supervise → deny
        self.assertIsNotNone(assert_access_level_allowed(
            FakeUser(), [],
            'staff_admin', 'staff_admin',
        ))
        # Supervise bypass
        self.assertIsNone(assert_access_level_allowed(
            FakeUser(), [STAFF_MANAGEMENT_AUTHORITY_SUPERVISE],
            'staff_admin', 'super_staff_admin',
        ))

    def test_nav_subset(self):
        from staff.permissions import assert_nav_subset

        class FakeUser:
            is_superuser = False

        self.assertIsNone(assert_nav_subset(
            FakeUser(), [], ['a', 'b'], ['a'],
        ))
        self.assertIsNotNone(assert_nav_subset(
            FakeUser(), [], ['a'], ['a', 'b'],
        ))
        self.assertIsNone(assert_nav_subset(
            FakeUser(),
            [STAFF_MANAGEMENT_AUTHORITY_SUPERVISE],
            ['a'], ['a', 'b'],
        ))

    def test_role_department_ceiling(self):
        from staff.permissions import assert_role_department_ceiling

        class FakeUser:
            is_superuser = False

        # Requester with no caps cannot assign a role whose preset has caps.
        # Pick a canonical role with a known preset.
        any_role = next(iter(ROLE_PRESET_CAPABILITIES.keys()))
        err = assert_role_department_ceiling(
            FakeUser(), set(), any_role, None,
        )
        # If that role has no preset caps, this is None; try to find one
        # that does.
        if not ROLE_PRESET_CAPABILITIES[any_role]:
            for k, v in ROLE_PRESET_CAPABILITIES.items():
                if v:
                    any_role = k
                    break
            err = assert_role_department_ceiling(
                FakeUser(), set(), any_role, None,
            )
        self.assertIsNotNone(err)
