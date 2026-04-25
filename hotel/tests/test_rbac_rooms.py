"""
Phase 6B.1 tests — RBAC for the `rooms` module.

Covers:
- capability catalog + module policy self-consistency
- persona resolution (tier/dept/role → rbac.rooms payload)
- no room.* capability leaks into any tier preset
- endpoint enforcement for every canonical rooms endpoint
- hotel-scoping (cross-hotel access still fails)
- legacy-gate removal (is_superuser, CanManageRooms)
- PATCH is_out_of_order requires the out-of-order capability
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from hotel.models import Hotel
from rooms.models import Room, RoomType
from staff.capability_catalog import (
    CANONICAL_CAPABILITIES,
    DEPARTMENT_PRESET_CAPABILITIES,
    ROLE_PRESET_CAPABILITIES,
    ROOM_CHECKOUT_BULK,
    ROOM_CHECKOUT_DESTRUCTIVE,
    ROOM_INSPECTION_PERFORM,
    ROOM_INVENTORY_CREATE,
    ROOM_INVENTORY_DELETE,
    ROOM_INVENTORY_READ,
    ROOM_INVENTORY_UPDATE,
    ROOM_MAINTENANCE_CLEAR,
    ROOM_MAINTENANCE_FLAG,
    ROOM_MEDIA_MANAGE,
    ROOM_MEDIA_READ,
    ROOM_MODULE_VIEW,
    ROOM_OUT_OF_ORDER_SET,
    ROOM_STATUS_READ,
    ROOM_STATUS_TRANSITION,
    ROOM_TYPE_MANAGE,
    ROOM_TYPE_READ,
    TIER_DEFAULT_CAPABILITIES,
    resolve_capabilities,
    validate_preset_maps,
)
from staff.models import Department, Role, Staff
from staff.module_policy import (
    MODULE_POLICY,
    resolve_module_policy,
    validate_module_policy,
)


# Canonical slugs for every action listed by MODULE_POLICY['rooms']. Used to
# prove each advertised key maps to a canonical capability (no decorative
# action keys) and to drive per-action persona assertions.
_ROOM_ACTION_CAPABILITIES = {
    'inventory_create': ROOM_INVENTORY_CREATE,
    'inventory_update': ROOM_INVENTORY_UPDATE,
    'inventory_delete': ROOM_INVENTORY_DELETE,
    'type_manage': ROOM_TYPE_MANAGE,
    'media_manage': ROOM_MEDIA_MANAGE,
    'out_of_order_set': ROOM_OUT_OF_ORDER_SET,
    'checkout_destructive': ROOM_CHECKOUT_DESTRUCTIVE,
    'status_transition': ROOM_STATUS_TRANSITION,
    'maintenance_flag': ROOM_MAINTENANCE_FLAG,
    'inspect': ROOM_INSPECTION_PERFORM,
    'maintenance_clear': ROOM_MAINTENANCE_CLEAR,
    'checkout_bulk': ROOM_CHECKOUT_BULK,
}


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def _make_hotel(slug: str) -> Hotel:
    return Hotel.objects.create(name=f"Hotel {slug}", slug=slug, timezone="UTC")


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


def _authed_client(user: User) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# ---------------------------------------------------------------------------
# Registry self-consistency
# ---------------------------------------------------------------------------

class RoomPolicyRegistryTest(TestCase):
    def test_preset_maps_self_consistent(self):
        self.assertEqual(validate_preset_maps(), [])

    def test_module_policy_self_consistent(self):
        self.assertEqual(validate_module_policy(), [])

    def test_rooms_module_is_registered(self):
        self.assertIn('rooms', MODULE_POLICY)
        policy = MODULE_POLICY['rooms']
        self.assertEqual(policy['view_capability'], ROOM_MODULE_VIEW)
        self.assertEqual(policy['read_capability'], ROOM_INVENTORY_READ)

    def test_no_decorative_action_keys_in_rooms_policy(self):
        """Every rooms action key must map to a canonical capability."""
        policy = MODULE_POLICY['rooms']
        for action, cap in policy['actions'].items():
            self.assertIn(
                cap, CANONICAL_CAPABILITIES,
                f"Action {action!r} maps to non-canonical capability {cap!r}",
            )
            # And must match the expected mapping declared at the top.
            self.assertIn(action, _ROOM_ACTION_CAPABILITIES, action)
            self.assertEqual(
                cap, _ROOM_ACTION_CAPABILITIES[action],
                f"Action {action!r} capability drifted",
            )

    def test_no_room_capability_in_any_tier_preset(self):
        """Tier must never carry a room.* capability (contract rule)."""
        room_caps = {c for c in CANONICAL_CAPABILITIES if c.startswith('room.')}
        for tier, caps in TIER_DEFAULT_CAPABILITIES.items():
            leaked = caps & room_caps
            self.assertFalse(
                leaked,
                f"Tier {tier!r} leaks room capabilities: {sorted(leaked)}",
            )


# ---------------------------------------------------------------------------
# Persona resolution via resolve_capabilities()
# ---------------------------------------------------------------------------

class RoomPolicyPersonaTest(TestCase):
    """Tier/dept/role → rbac.rooms resolution, with no endpoint calls."""

    def _policy(self, tier=None, role_slug=None, department_slug=None):
        caps = resolve_capabilities(tier, role_slug, department_slug)
        return resolve_module_policy(caps)['rooms']

    def test_front_office_regular_staff_reads_only(self):
        pol = self._policy('regular_staff', None, 'front_office')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        # No operate, no supervise, no manage
        self.assertFalse(pol['actions']['status_transition'])
        self.assertFalse(pol['actions']['inspect'])
        self.assertFalse(pol['actions']['maintenance_flag'])
        self.assertFalse(pol['actions']['inventory_create'])
        self.assertFalse(pol['actions']['out_of_order_set'])

    def test_housekeeping_regular_staff_operates(self):
        pol = self._policy('regular_staff', None, 'housekeeping')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        self.assertTrue(pol['actions']['status_transition'])
        self.assertTrue(pol['actions']['maintenance_flag'])
        # Supervise / manage — denied
        self.assertFalse(pol['actions']['inspect'])
        self.assertFalse(pol['actions']['maintenance_clear'])
        self.assertFalse(pol['actions']['checkout_bulk'])
        self.assertFalse(pol['actions']['inventory_create'])

    def test_housekeeping_supervisor_supervises(self):
        pol = self._policy('regular_staff', 'housekeeping_supervisor',
                           'housekeeping')
        self.assertTrue(pol['actions']['status_transition'])
        self.assertTrue(pol['actions']['inspect'])
        self.assertTrue(pol['actions']['maintenance_clear'])
        self.assertTrue(pol['actions']['checkout_bulk'])
        # Manage still denied
        self.assertFalse(pol['actions']['inventory_create'])
        self.assertFalse(pol['actions']['type_manage'])
        self.assertFalse(pol['actions']['out_of_order_set'])
        self.assertFalse(pol['actions']['checkout_destructive'])

    def test_housekeeping_manager_supervises(self):
        pol = self._policy('regular_staff', 'housekeeping_manager',
                           'housekeeping')
        self.assertTrue(pol['actions']['inspect'])
        self.assertTrue(pol['actions']['maintenance_clear'])
        self.assertTrue(pol['actions']['checkout_bulk'])
        self.assertFalse(pol['actions']['inventory_create'])

    def test_maintenance_regular_staff_can_flag_not_clear(self):
        pol = self._policy('regular_staff', None, 'maintenance')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['actions']['maintenance_flag'])
        self.assertFalse(pol['actions']['maintenance_clear'])
        self.assertFalse(pol['actions']['out_of_order_set'])
        self.assertFalse(pol['actions']['status_transition'])

    def test_maintenance_supervisor_clears(self):
        pol = self._policy('regular_staff', 'maintenance_supervisor',
                           'maintenance')
        self.assertTrue(pol['actions']['maintenance_flag'])
        self.assertTrue(pol['actions']['maintenance_clear'])
        self.assertFalse(pol['actions']['out_of_order_set'])

    def test_maintenance_manager_clears_and_out_of_order(self):
        pol = self._policy('regular_staff', 'maintenance_manager',
                           'maintenance')
        self.assertTrue(pol['actions']['maintenance_clear'])
        self.assertTrue(pol['actions']['out_of_order_set'])
        # Still not manage bucket
        self.assertFalse(pol['actions']['inventory_create'])
        self.assertFalse(pol['actions']['checkout_destructive'])

    def test_food_beverage_has_no_room_visibility(self):
        pol = self._policy('regular_staff', 'waiter', 'food_beverage')
        self.assertFalse(pol['visible'])
        self.assertFalse(pol['read'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_kitchen_has_no_room_visibility(self):
        pol = self._policy('regular_staff', 'kitchen_staff', 'kitchen')
        self.assertFalse(pol['visible'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_staff_admin_tier_alone_has_no_room_caps(self):
        pol = self._policy('staff_admin', None, None)
        self.assertFalse(pol['visible'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_super_staff_admin_tier_alone_has_no_room_caps(self):
        pol = self._policy('super_staff_admin', None, None)
        self.assertFalse(pol['visible'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_hotel_manager_role_gets_full_manage(self):
        pol = self._policy('regular_staff', 'hotel_manager', 'management')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        for action in pol['actions']:
            self.assertTrue(pol['actions'][action], action)

    def test_front_office_manager_role_supervises(self):
        pol = self._policy('regular_staff', 'front_office_manager',
                           'front_office')
        self.assertTrue(pol['actions']['inspect'])
        self.assertTrue(pol['actions']['checkout_bulk'])
        self.assertFalse(pol['actions']['inventory_create'])


# ---------------------------------------------------------------------------
# Endpoint enforcement
# ---------------------------------------------------------------------------

class RoomEndpointEnforcementTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.hotel = _make_hotel("phase6b-hotel")
        cls.other_hotel = _make_hotel("phase6b-other")

        cls.room_type = RoomType.objects.create(
            hotel=cls.hotel, name="Standard", code="STD",
            starting_price_from=100,
        )
        cls.other_room_type = RoomType.objects.create(
            hotel=cls.other_hotel, name="Standard", code="STD",
            starting_price_from=100,
        )

        cls.room = Room.objects.create(
            hotel=cls.hotel, room_number=101,
            room_type=cls.room_type, is_active=True,
            room_status='CHECKOUT_DIRTY',
        )
        cls.other_room = Room.objects.create(
            hotel=cls.other_hotel, room_number=101,
            room_type=cls.other_room_type, is_active=True,
            room_status='CHECKOUT_DIRTY',
        )

        # Personas
        cls.no_caps = _make_staff(
            cls.hotel, username='nobody', access_level='regular_staff',
        )
        cls.front_desk = _make_staff(
            cls.hotel, username='frontdesk', access_level='regular_staff',
            department_slug='front_office',
        )
        cls.housekeeper = _make_staff(
            cls.hotel, username='hker', access_level='regular_staff',
            department_slug='housekeeping',
        )
        cls.hk_supervisor = _make_staff(
            cls.hotel, username='hk_sup', access_level='regular_staff',
            role_slug='housekeeping_supervisor',
            department_slug='housekeeping',
        )
        cls.maint_tech = _make_staff(
            cls.hotel, username='maint_t', access_level='regular_staff',
            department_slug='maintenance',
        )
        cls.maint_supervisor = _make_staff(
            cls.hotel, username='maint_s', access_level='regular_staff',
            role_slug='maintenance_supervisor',
            department_slug='maintenance',
        )
        cls.hotel_manager = _make_staff(
            cls.hotel, username='hmgr', access_level='regular_staff',
            role_slug='hotel_manager', department_slug='management',
        )
        cls.ooo_setter = _make_staff(
            cls.hotel, username='ooo_setter', access_level='regular_staff',
            role_slug='maintenance_manager',
            department_slug='maintenance',
        )
        cls.super_staff_admin = _make_staff(
            cls.hotel, username='sa',
            access_level='super_staff_admin',
        )
        cls.other_hotel_manager = _make_staff(
            cls.other_hotel, username='other_hmgr',
            access_level='regular_staff',
            role_slug='hotel_manager', department_slug='management',
        )

    # --- Module visibility gate on every endpoint ---------------------------

    def _all_endpoints(self):
        slug = self.hotel.slug
        rn = self.room.room_number
        return [
            ('get', f'/api/staff/hotel/{slug}/room-management/', {}),
            ('get', f'/api/staff/hotel/{slug}/room-management/{rn}/', {}),
            ('get', f'/api/staff/hotel/{slug}/room-types/', {}),
            ('get', f'/api/staff/hotel/{slug}/room-images/', {}),
            ('get', f'/api/staff/hotel/{slug}/turnover/rooms/', {}),
            ('get', f'/api/staff/hotel/{slug}/turnover/stats/', {}),
            ('post', f'/api/staff/hotel/{slug}/rooms/checkout/',
             {'room_ids': [self.room.id]}),
            ('post',
             f'/api/staff/hotel/{slug}/rooms/{rn}/start-cleaning/', {}),
            ('post',
             f'/api/staff/hotel/{slug}/rooms/{rn}/mark-cleaned/', {}),
            ('post',
             f'/api/staff/hotel/{slug}/rooms/{rn}/inspect/', {}),
            ('post',
             f'/api/staff/hotel/{slug}/rooms/{rn}/mark-maintenance/', {}),
            ('post',
             f'/api/staff/hotel/{slug}/rooms/{rn}/complete-maintenance/',
             {}),
            ('post',
             f'/api/staff/hotel/{slug}/room-types/'
             f'{self.room_type.id}/rooms/bulk-create/',
             {'room_numbers': [999]}),
        ]

    def test_every_endpoint_denies_user_without_module_view(self):
        c = _authed_client(self.no_caps.user)
        for method, url, body in self._all_endpoints():
            resp = getattr(c, method)(url, data=body, format='json')
            self.assertEqual(
                resp.status_code, status.HTTP_403_FORBIDDEN,
                f"{method.upper()} {url} expected 403, got {resp.status_code}",
            )

    # --- Inventory (room-management) ----------------------------------------

    def test_front_desk_can_read_inventory(self):
        c = _authed_client(self.front_desk.user)
        resp = c.get(f'/api/staff/hotel/{self.hotel.slug}/room-management/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_housekeeper_cannot_create_inventory(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-management/',
            data={'room_number': 555, 'room_type': self.room_type.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hotel_manager_can_create_inventory(self):
        c = _authed_client(self.hotel_manager.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-management/',
            data={'room_number': 777, 'room_type': self.room_type.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_hotel_manager_can_delete_inventory(self):
        extra = Room.objects.create(
            hotel=self.hotel, room_number=888, room_type=self.room_type,
            is_active=True, room_status='READY_FOR_GUEST',
        )
        c = _authed_client(self.hotel_manager.user)
        resp = c.delete(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{extra.room_number}/'
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_patch_normal_field_does_not_require_out_of_order_cap(self):
        # A persona that holds inventory.update (hotel_manager carries
        # _ROOM_MANAGE) must be able to patch unrelated writable fields
        # without also holding room.out_of_order.set.
        c = _authed_client(self.hotel_manager.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_active': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_patch_is_out_of_order_only_allowed_for_ooo_setter(self):
        """Phase 6B.2 drift fix: maintenance_manager holds
        room.out_of_order.set but not room.inventory.update. A PATCH
        whose body ONLY toggles is_out_of_order must succeed."""
        c = _authed_client(self.ooo_setter.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_out_of_order': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_out_of_order)

    def test_ooo_setter_cannot_patch_non_ooo_fields(self):
        """maintenance_manager lacks inventory.update; touching any
        other writable field must still 403."""
        c = _authed_client(self.ooo_setter.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_active': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_ooo_setter_mixed_payload_requires_inventory_update(self):
        """Mixed payload (is_out_of_order + other fields) must require
        BOTH capabilities — maintenance_manager lacks inventory.update
        → 403."""
        c = _authed_client(self.ooo_setter.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_out_of_order': True, 'is_active': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hk_supervisor_cannot_toggle_out_of_order(self):
        """Housekeeping supervisor carries neither inventory.update nor
        out_of_order.set → a PATCH toggling is_out_of_order must 403
        even when the body contains only that field."""
        c = _authed_client(self.hk_supervisor.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_out_of_order': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_is_out_of_order_allowed_for_hotel_manager(self):
        c = _authed_client(self.hotel_manager.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_out_of_order': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_hotel_manager_mixed_payload_allowed(self):
        """hotel_manager carries both inventory.update and
        out_of_order.set (via _ROOM_MANAGE) → mixed payload allowed."""
        c = _authed_client(self.hotel_manager.user)
        resp = c.patch(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/room-management/{self.room.room_number}/',
            data={'is_out_of_order': True, 'is_active': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # --- Room types ---------------------------------------------------------

    def test_front_desk_can_read_room_types(self):
        c = _authed_client(self.front_desk.user)
        resp = c.get(f'/api/staff/hotel/{self.hotel.slug}/room-types/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_supervisor_cannot_manage_room_types(self):
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-types/',
            data={'name': 'Suite', 'code': 'ST', 'starting_price_from': 200},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hotel_manager_can_manage_room_types(self):
        c = _authed_client(self.hotel_manager.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-types/',
            data={'name': 'Suite', 'code': 'ST', 'starting_price_from': 200},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    # --- Turnover transitions ----------------------------------------------

    def test_housekeeper_can_start_cleaning(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/start-cleaning/',
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_front_desk_cannot_start_cleaning(self):
        c = _authed_client(self.front_desk.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/start-cleaning/',
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_housekeeper_cannot_inspect(self):
        # Move the room to a cleanable state via the housekeeper first.
        self.room.room_status = 'CLEANED_UNINSPECTED'
        self.room.save(update_fields=['room_status'])
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/inspect/',
            data={'passed': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hk_supervisor_can_inspect(self):
        self.room.room_status = 'CLEANED_UNINSPECTED'
        self.room.save(update_fields=['room_status'])
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/inspect/',
            data={'passed': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # --- Maintenance --------------------------------------------------------

    def test_maintenance_tech_can_flag_maintenance(self):
        c = _authed_client(self.maint_tech.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/mark-maintenance/',
            data={'priority': 'LOW'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_maintenance_tech_cannot_clear_maintenance(self):
        self.room.room_status = 'MAINTENANCE_REQUIRED'
        self.room.maintenance_required = True
        self.room.save(update_fields=['room_status', 'maintenance_required'])
        c = _authed_client(self.maint_tech.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/complete-maintenance/',
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_maintenance_supervisor_can_clear_maintenance(self):
        self.room.room_status = 'MAINTENANCE_REQUIRED'
        self.room.maintenance_required = True
        self.room.save(update_fields=['room_status', 'maintenance_required'])
        c = _authed_client(self.maint_supervisor.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/complete-maintenance/',
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_mark_maintenance_no_longer_accepts_maintenance_nav_alone(self):
        """A staff member with only maintenance visibility and no room
        capability must be denied (legacy nav-only gate removed)."""
        # front_office carries ROOM_READ only (no maintenance_flag).
        c = _authed_client(self.front_desk.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/mark-maintenance/',
            data={'priority': 'LOW'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # --- Checkout -----------------------------------------------------------

    def test_front_desk_cannot_bulk_checkout(self):
        c = _authed_client(self.front_desk.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/',
            data={'room_ids': [self.room.id]}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hk_supervisor_can_bulk_checkout(self):
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/',
            data={'room_ids': [self.room.id]}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_hk_supervisor_cannot_destructive_checkout(self):
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/',
            data={'room_ids': [self.room.id], 'destructive': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_hotel_manager_can_destructive_checkout(self):
        c = _authed_client(self.hotel_manager.user)
        resp = c.post(
            f'/api/staff/hotel/{self.hotel.slug}/rooms/checkout/',
            data={'room_ids': [self.room.id], 'destructive': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # --- Cross-hotel --------------------------------------------------------

    def test_cross_hotel_denied_even_with_capability(self):
        """A hotel_manager of hotel B cannot touch hotel A's rooms even
        though they hold every room capability."""
        c = _authed_client(self.other_hotel_manager.user)
        url = (
            f'/api/staff/hotel/{self.hotel.slug}'
            f'/rooms/{self.room.room_number}/start-cleaning/'
        )
        resp = c.post(url, format='json')
        self.assertIn(
            resp.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )


# ---------------------------------------------------------------------------
# Legacy-gate removal (grep-style guards against regression)
# ---------------------------------------------------------------------------

class RoomLegacyGateRemovalTest(TestCase):
    ROOMS_VIEWS = Path(__file__).resolve().parent.parent.parent / 'rooms' / 'views.py'

    def _source(self) -> str:
        return self.ROOMS_VIEWS.read_text(encoding='utf-8')

    def test_no_CanManageRooms_callsites_remain(self):
        src = self._source()
        self.assertNotIn('CanManageRooms', src)

    def test_no_inline_rooms_nav_gate_in_rooms_views(self):
        src = self._source()
        self.assertNotIn("HasNavPermission('rooms')", src)
        self.assertNotIn('HasNavPermission("rooms")', src)

    def test_no_maintenance_nav_gate_in_rooms_views(self):
        src = self._source()
        self.assertNotIn("HasNavPermission('maintenance')", src)
        self.assertNotIn('HasNavPermission("maintenance")', src)

    def test_no_is_superuser_gate_in_checkout_rooms(self):
        src = self._source()
        # checkout_rooms function body must not test is_superuser.
        match = re.search(
            r'def checkout_rooms\(.*?\)(.*?)\n(?:def |@api_view)',
            src, flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "checkout_rooms body not found")
        self.assertNotIn('is_superuser', match.group(1))

    def test_CanManageRooms_class_removed_from_staff_permissions(self):
        from staff import permissions as sperms
        self.assertFalse(
            hasattr(sperms, 'CanManageRooms'),
            "CanManageRooms class should be removed from staff.permissions",
        )
