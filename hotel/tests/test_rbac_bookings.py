"""
Phase 6A tests — RBAC for the `bookings` module.

Covers:
- capability catalog + module policy self-consistency
- tier-based visibility / read / operate / supervise / manage policy object
- enforcement on staff room-booking endpoints (read vs operate vs supervise
  vs manage)
- hotel-scoping (cross-hotel access still fails)
- bucket escalation non-implication (read !⇒ operate, operate !⇒ supervise,
  supervise !⇒ manage)
"""
from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from hotel.models import Hotel, RoomBooking
from rooms.models import RoomType
from staff.capability_catalog import (
    BOOKING_CONFIG_MANAGE,
    BOOKING_MODULE_VIEW,
    BOOKING_OVERRIDE_SUPERVISE,
    BOOKING_RECORD_CANCEL,
    BOOKING_RECORD_READ,
    BOOKING_RECORD_UPDATE,
    BOOKING_ROOM_ASSIGN,
    BOOKING_STAY_CHECKIN,
    BOOKING_STAY_CHECKOUT,
    resolve_capabilities,
    validate_preset_maps,
)
from staff.models import Department, Role, Staff
from staff.module_policy import (
    MODULE_POLICY,
    resolve_module_policy,
    validate_module_policy,
)


# ---------------------------------------------------------------------------
# Helpers
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
    """
    Build a realistic staff row bound to canonical role/department slugs.

    Canonical slugs are enforced by ``Role.clean``; passing a legacy slug
    raises. Department slugs are free-form (department_slug_not_empty is the
    only constraint).
    """
    user = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )

    dept = None
    if department_slug:
        dept, _ = Department.objects.get_or_create(
            hotel=hotel,
            slug=department_slug,
            defaults={'name': department_slug.replace('_', ' ').title()},
        )

    role = None
    if role_slug:
        role, _ = Role.objects.get_or_create(
            hotel=hotel,
            slug=role_slug,
            defaults={
                'name': role_slug.replace('_', ' ').title(),
                'department': dept,
            },
        )

    return Staff.objects.create(
        user=user,
        hotel=hotel,
        department=dept,
        role=role,
        access_level=access_level,
        email=f"{username}@example.com",
        is_active=True,
    )


def _authed_client(user: User) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# ---------------------------------------------------------------------------
# Catalog + module policy self-consistency
# ---------------------------------------------------------------------------

class BookingPolicyRegistryTest(TestCase):
    def test_preset_maps_self_consistent(self):
        self.assertEqual(validate_preset_maps(), [])

    def test_module_policy_self_consistent(self):
        self.assertEqual(validate_module_policy(), [])

    def test_bookings_module_is_registered(self):
        self.assertIn('bookings', MODULE_POLICY)
        policy = MODULE_POLICY['bookings']
        self.assertEqual(policy['view_capability'], BOOKING_MODULE_VIEW)
        self.assertEqual(policy['read_capability'], BOOKING_RECORD_READ)
        # Every listed action maps to a canonical slug (validated above).
        self.assertIn('checkin', policy['actions'])
        self.assertIn('checkout', policy['actions'])
        self.assertIn('assign_room', policy['actions'])
        self.assertIn('manage_rules', policy['actions'])


class BookingPolicyResolutionTest(TestCase):
    """Tier-driven resolution of the bookings policy object."""

    def test_super_staff_admin_gets_supervise_not_manage(self):
        """Phase 6A.2: tier grants supervise, not manage."""
        caps = resolve_capabilities('super_staff_admin', None, None)
        pol = resolve_module_policy(caps)['bookings']
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        # Supervise bucket — granted
        for action in (
            'checkin', 'checkout', 'override_conflicts',
            'resolve_overstay', 'modify_locked',
        ):
            self.assertTrue(pol['actions'][action], action)
        # Manage bucket — denied (role preset only)
        self.assertFalse(pol['actions']['manage_rules'])

    def test_staff_admin_has_no_booking_caps(self):
        """Phase 6A.2: staff_admin tier no longer carries booking operate.
        Operate must come from the front_office department preset."""
        caps = resolve_capabilities('staff_admin', None, None)
        pol = resolve_module_policy(caps)['bookings']
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['read'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_regular_staff_gets_no_booking_caps_by_default(self):
        caps = resolve_capabilities('regular_staff', None, None)
        pol = resolve_module_policy(caps)['bookings']
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['read'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_front_office_dept_preset_grants_operate(self):
        """Phase 6A.2: front_office department preset carries booking
        READ + OPERATE so a front-office regular_staff agent can operate
        bookings without relying on tier elevation.
        """
        caps = resolve_capabilities(
            'regular_staff', None, 'front_office',
        )
        pol = resolve_module_policy(caps)['bookings']
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        for action in (
            'update', 'cancel', 'assign_room',
            'checkin', 'checkout', 'communicate',
        ):
            self.assertTrue(pol['actions'][action], action)
        # Supervise / manage buckets — denied
        self.assertFalse(pol['actions']['extend'])
        self.assertFalse(pol['actions']['resolve_overstay'])
        self.assertFalse(pol['actions']['manage_rules'])

    def test_housekeeping_dept_preset_does_not_grant_bookings(self):
        caps = resolve_capabilities(
            'regular_staff', None, 'housekeeping',
        )
        pol = resolve_module_policy(caps)['bookings']
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['read'])

    def test_hotel_manager_role_carries_booking_manage(self):
        caps = resolve_capabilities(
            'regular_staff', 'hotel_manager', None,
        )
        pol = resolve_module_policy(caps)['bookings']
        self.assertTrue(pol['actions']['manage_rules'])

    def test_front_office_manager_role_carries_booking_manage(self):
        caps = resolve_capabilities(
            'regular_staff', 'front_office_manager', None,
        )
        pol = resolve_module_policy(caps)['bookings']
        self.assertTrue(pol['actions']['manage_rules'])

    def test_bucket_non_implication_via_capability_sets(self):
        """Read does not imply operate; operate does not imply supervise;
        supervise does not imply manage."""
        read_only = [BOOKING_MODULE_VIEW, BOOKING_RECORD_READ]
        operate_only = read_only + [
            BOOKING_RECORD_UPDATE,
            BOOKING_RECORD_CANCEL,
            BOOKING_ROOM_ASSIGN,
            BOOKING_STAY_CHECKIN,
            BOOKING_STAY_CHECKOUT,
        ]
        supervise_only = operate_only + [BOOKING_OVERRIDE_SUPERVISE]
        manage_only = supervise_only + [BOOKING_CONFIG_MANAGE]

        pol_read = resolve_module_policy(read_only)['bookings']
        self.assertTrue(pol_read['read'])
        self.assertFalse(pol_read['actions']['checkin'])

        pol_op = resolve_module_policy(operate_only)['bookings']
        self.assertTrue(pol_op['actions']['checkin'])
        self.assertFalse(pol_op['actions']['resolve_overstay'])

        pol_sup = resolve_module_policy(supervise_only)['bookings']
        self.assertTrue(pol_sup['actions']['resolve_overstay'])
        self.assertFalse(pol_sup['actions']['manage_rules'])

        pol_mgr = resolve_module_policy(manage_only)['bookings']
        self.assertTrue(pol_mgr['actions']['manage_rules'])


# ---------------------------------------------------------------------------
# Endpoint enforcement
# ---------------------------------------------------------------------------

class BookingEndpointEnforcementTest(TestCase):
    """
    Enforcement on the real room-booking endpoints. Each test asserts that
    a user with just-enough capabilities passes, and a user at the tier
    below (missing the bucket) is forbidden.
    """

    @classmethod
    def setUpTestData(cls):
        cls.hotel = _make_hotel("phase6a-hotel")
        cls.other_hotel = _make_hotel("phase6a-other")

        cls.room_type = RoomType.objects.create(
            hotel=cls.hotel, name="Standard", code="STD",
            starting_price_from=100,
        )

        # Bookings in cls.hotel
        today = date(2026, 4, 23)
        cls.booking = RoomBooking.objects.create(
            hotel=cls.hotel,
            room_type=cls.room_type,
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=3),
            primary_first_name="Phase",
            primary_last_name="SixA",
            primary_email="guest@example.com",
            status='CONFIRMED',
            total_amount=200,
        )

        # Staff fixtures
        cls.super_admin = _make_staff(
            cls.hotel,
            username="super_admin",
            access_level="super_staff_admin",
        )
        # Phase 6A.2: tier no longer carries booking caps. Front-desk
        # staff must belong to `front_office` department to read/operate.
        cls.staff_admin = _make_staff(
            cls.hotel,
            username="staff_admin",
            access_level="staff_admin",
            department_slug="front_office",
        )
        cls.housekeeping_admin = _make_staff(
            cls.hotel,
            username="hk_admin",
            access_level="staff_admin",
            department_slug="housekeeping",
        )
        cls.regular = _make_staff(
            cls.hotel,
            username="regular",
            access_level="regular_staff",
        )
        cls.front_desk_regular = _make_staff(
            cls.hotel,
            username="front_desk_regular",
            access_level="regular_staff",
            department_slug="front_office",
        )
        cls.hotel_manager = _make_staff(
            cls.hotel,
            username="hotel_mgr",
            access_level="regular_staff",
            role_slug="hotel_manager",
        )
        cls.other_admin = _make_staff(
            cls.other_hotel,
            username="other_admin",
            access_level="super_staff_admin",
        )

    # ----- list (read) -----

    def test_list_forbidden_for_regular_staff(self):
        c = _authed_client(self.regular.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/room-bookings/"
        resp = c.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_allowed_for_front_office_staff_admin(self):
        c = _authed_client(self.staff_admin.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/room-bookings/"
        resp = c.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_forbidden_for_housekeeping_staff_admin(self):
        """Phase 6A.2: staff_admin without front_office dept must not
        reach the bookings module."""
        c = _authed_client(self.housekeeping_admin.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/room-bookings/"
        resp = c.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_allowed_for_front_office_regular_staff(self):
        """Phase 6A.2: the critical fix — a genuine regular_staff front
        desk agent must be able to read bookings via department preset."""
        c = _authed_client(self.front_desk_regular.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/room-bookings/"
        resp = c.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_cross_hotel_forbidden(self):
        """A super admin of hotel A cannot list hotel B's bookings even
        though they carry the full capability set."""
        c = _authed_client(self.other_admin.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/room-bookings/"
        resp = c.get(url)
        self.assertIn(
            resp.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )

    # ----- overstay acknowledge (supervise) -----

    def test_overstay_acknowledge_forbidden_for_staff_admin(self):
        """Phase 6A.2: staff_admin at front_office dept has operate but
        not supervise."""
        c = _authed_client(self.staff_admin.user)
        url = (
            f"/api/staff/hotel/{self.hotel.slug}"
            f"/room-bookings/{self.booking.booking_id}"
            f"/overstay/acknowledge/"
        )
        resp = c.post(url, data={}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_overstay_acknowledge_allowed_for_super_staff_admin(self):
        c = _authed_client(self.super_admin.user)
        url = (
            f"/api/staff/hotel/{self.hotel.slug}"
            f"/room-bookings/{self.booking.booking_id}"
            f"/overstay/acknowledge/"
        )
        resp = c.post(url, data={}, format='json')
        # Not 403 — capability check passes. Business logic may still
        # return 400/409 because the booking is not overstaying, but that
        # is past the RBAC layer and not what this test asserts.
        self.assertNotEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_overstay_extend_forbidden_for_front_office_staff_admin(self):
        """Phase 6A.2 remap: overstay extend is now supervise-only.
        A front-office staff_admin with operate but not supervise must
        be forbidden."""
        c = _authed_client(self.staff_admin.user)
        url = (
            f"/api/staff/hotel/{self.hotel.slug}"
            f"/room-bookings/{self.booking.booking_id}"
            f"/overstay/extend/"
        )
        resp = c.post(url, data={}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_overstay_extend_allowed_for_super_staff_admin(self):
        c = _authed_client(self.super_admin.user)
        url = (
            f"/api/staff/hotel/{self.hotel.slug}"
            f"/room-bookings/{self.booking.booking_id}"
            f"/overstay/extend/"
        )
        resp = c.post(url, data={}, format='json')
        self.assertNotEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ----- rate plans (manage config) -----

    def test_rate_plans_post_forbidden_for_super_staff_admin(self):
        """Phase 6A.2: manage_rules is no longer granted by tier.
        super_staff_admin alone must not be able to write rate plans."""
        c = _authed_client(self.super_admin.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/rate-plans/"
        resp = c.post(url, data={'name': 'Nope'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_rate_plans_post_allowed_for_hotel_manager(self):
        c = _authed_client(self.hotel_manager.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/rate-plans/"
        resp = c.post(url, data={'name': 'Mgr'}, format='json')
        # Past RBAC (400 from serializer is fine, 403 is not).
        self.assertNotEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_rate_plans_post_forbidden_for_staff_admin(self):
        """manage_rules is gated by BOOKING_CONFIG_MANAGE which
        staff_admin does not carry."""
        c = _authed_client(self.staff_admin.user)
        url = f"/api/staff/hotel/{self.hotel.slug}/rate-plans/"
        resp = c.post(url, data={'name': 'Nope'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ----- regular_staff cannot sneak past any booking endpoint -----

    def test_regular_staff_cannot_checkin(self):
        c = _authed_client(self.regular.user)
        url = (
            f"/api/staff/hotel/{self.hotel.slug}"
            f"/room-bookings/{self.booking.booking_id}/check-in/"
        )
        resp = c.post(url, data={}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_staff_cannot_cancel(self):
        c = _authed_client(self.regular.user)
        url = (
            f"/api/staff/hotel/{self.hotel.slug}"
            f"/room-bookings/{self.booking.booking_id}/cancel/"
        )
        resp = c.post(url, data={}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Authenticated payload — rbac.bookings must be present and tier-accurate
# ---------------------------------------------------------------------------

class BookingPayloadEmissionTest(TestCase):
    """The /me endpoint must include an ``rbac.bookings`` object computed
    from the resolved capability set."""

    @classmethod
    def setUpTestData(cls):
        cls.hotel = _make_hotel("phase6a-payload")
        cls.super_admin = _make_staff(
            cls.hotel,
            username="payload_super",
            access_level="super_staff_admin",
        )
        cls.staff_admin = _make_staff(
            cls.hotel,
            username="payload_admin",
            access_level="staff_admin",
        )
        cls.regular = _make_staff(
            cls.hotel,
            username="payload_regular",
            access_level="regular_staff",
        )

    def _fetch_rbac(self, user: User) -> dict:
        c = _authed_client(user)
        resp = c.get(f"/api/staff/hotel/{self.hotel.slug}/me/")
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, resp.content,
        )
        self.assertIn('rbac', resp.data)
        self.assertIn('bookings', resp.data['rbac'])
        return resp.data['rbac']['bookings']

    def test_super_staff_admin_payload(self):
        pol = self._fetch_rbac(self.super_admin.user)
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        self.assertTrue(pol['actions']['checkin'])
        self.assertTrue(pol['actions']['resolve_overstay'])
        # Phase 6A.2: manage_rules not granted by tier.
        self.assertFalse(pol['actions']['manage_rules'])

    def test_staff_admin_payload(self):
        pol = self._fetch_rbac(self.staff_admin.user)
        # Phase 6A.2: staff_admin tier no longer carries booking caps.
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['actions']['checkin'])
        self.assertFalse(pol['actions']['resolve_overstay'])
        self.assertFalse(pol['actions']['manage_rules'])

    def test_regular_staff_payload(self):
        pol = self._fetch_rbac(self.regular.user)
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['read'])
        self.assertFalse(pol['actions']['checkin'])
