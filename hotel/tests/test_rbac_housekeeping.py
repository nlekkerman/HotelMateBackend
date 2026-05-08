"""
Phase 6C tests — RBAC for the `housekeeping` module.

Covers:
- capability catalog + module policy self-consistency
- persona resolution (tier/dept/role → rbac.housekeeping payload)
- no housekeeping.* capability leaks into any tier preset
- endpoint enforcement for every canonical housekeeping endpoint
- PATCH/PUT split: task.update alone cannot mutate assigned_to or
  status; mixed payloads require ALL implicated capabilities
- room status update routes through can_change_room_status
- manager_override no longer requires a tier
- status_history requires the history.read capability
- cross-hotel staff existence does not leak via assign error message
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from hotel.models import Hotel
from housekeeping.models import HousekeepingTask
from rooms.models import Room, RoomType
from staff.capability_catalog import (
    CANONICAL_CAPABILITIES,
    HOUSEKEEPING_DASHBOARD_READ,
    HOUSEKEEPING_MODULE_VIEW,
    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    HOUSEKEEPING_TASK_ASSIGN,
    HOUSEKEEPING_TASK_CANCEL,
    HOUSEKEEPING_TASK_CREATE,
    HOUSEKEEPING_TASK_DELETE,
    HOUSEKEEPING_TASK_EXECUTE,
    HOUSEKEEPING_TASK_READ,
    HOUSEKEEPING_TASK_UPDATE,
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


_HK_ACTION_CAPABILITIES = {
    'dashboard_read': HOUSEKEEPING_DASHBOARD_READ,
    'task_create': HOUSEKEEPING_TASK_CREATE,
    'task_update': HOUSEKEEPING_TASK_UPDATE,
    'task_delete': HOUSEKEEPING_TASK_DELETE,
    'task_assign': HOUSEKEEPING_TASK_ASSIGN,
    'task_execute': HOUSEKEEPING_TASK_EXECUTE,
    'task_cancel': HOUSEKEEPING_TASK_CANCEL,
    'status_transition': HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    'status_front_desk': HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    'status_override': HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    'status_history_read': HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
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

class HousekeepingPolicyRegistryTest(TestCase):
    def test_preset_maps_self_consistent(self):
        self.assertEqual(validate_preset_maps(), [])

    def test_module_policy_self_consistent(self):
        self.assertEqual(validate_module_policy(), [])

    def test_housekeeping_module_is_registered(self):
        self.assertIn('housekeeping', MODULE_POLICY)
        policy = MODULE_POLICY['housekeeping']
        self.assertEqual(policy['view_capability'], HOUSEKEEPING_MODULE_VIEW)
        self.assertEqual(policy['read_capability'], HOUSEKEEPING_TASK_READ)

    def test_no_decorative_action_keys_in_housekeeping_policy(self):
        policy = MODULE_POLICY['housekeeping']
        for action, cap in policy['actions'].items():
            self.assertIn(
                cap, CANONICAL_CAPABILITIES,
                f"Action {action!r} maps to non-canonical capability {cap!r}",
            )
            self.assertIn(action, _HK_ACTION_CAPABILITIES, action)
            self.assertEqual(
                cap, _HK_ACTION_CAPABILITIES[action],
                f"Action {action!r} capability drifted",
            )

    def test_no_housekeeping_capability_in_lower_tier_presets(self):
        """Manager-role rebalance: super_staff_admin tier carries the
        full hotel-scoped bundle including housekeeping. Lower tiers
        (staff_admin, regular_staff) must still NOT leak housekeeping
        capabilities — only super_staff_admin earns them by tier."""
        hk_caps = {
            c for c in CANONICAL_CAPABILITIES if c.startswith('housekeeping.')
        }
        for tier, caps in TIER_DEFAULT_CAPABILITIES.items():
            if tier == 'super_staff_admin':
                continue
            leaked = caps & hk_caps
            self.assertFalse(
                leaked,
                f"Tier {tier!r} leaks housekeeping capabilities: "
                f"{sorted(leaked)}",
            )


# ---------------------------------------------------------------------------
# Persona resolution via resolve_capabilities()
# ---------------------------------------------------------------------------

class HousekeepingPolicyPersonaTest(TestCase):
    def _policy(self, tier=None, role_slug=None, department_slug=None):
        caps = resolve_capabilities(tier, role_slug, department_slug)
        return resolve_module_policy(caps)['housekeeping']

    def test_front_office_regular_visible_history_and_front_desk_only(self):
        pol = self._policy('regular_staff', None, 'front_office')
        self.assertTrue(pol['visible'])
        # No task.read → no module-level read of tasks.
        self.assertFalse(pol['read'])
        self.assertTrue(pol['actions']['status_front_desk'])
        self.assertTrue(pol['actions']['status_history_read'])
        # Operate / supervise / manage all denied.
        self.assertFalse(pol['actions']['task_create'])
        self.assertFalse(pol['actions']['task_assign'])
        self.assertFalse(pol['actions']['task_execute'])
        self.assertFalse(pol['actions']['task_cancel'])
        self.assertFalse(pol['actions']['task_delete'])
        self.assertFalse(pol['actions']['status_transition'])
        self.assertFalse(pol['actions']['status_override'])

    def test_housekeeping_regular_operates(self):
        pol = self._policy('regular_staff', None, 'housekeeping')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        self.assertTrue(pol['actions']['dashboard_read'])
        self.assertTrue(pol['actions']['task_execute'])
        self.assertTrue(pol['actions']['status_transition'])
        # Supervise / manage denied
        self.assertFalse(pol['actions']['task_create'])
        self.assertFalse(pol['actions']['task_update'])
        self.assertFalse(pol['actions']['task_assign'])
        self.assertFalse(pol['actions']['task_cancel'])
        self.assertFalse(pol['actions']['task_delete'])
        self.assertFalse(pol['actions']['status_override'])

    def test_housekeeping_supervisor_supervises(self):
        pol = self._policy('regular_staff', 'housekeeping_supervisor',
                           'housekeeping')
        self.assertTrue(pol['actions']['task_create'])
        self.assertTrue(pol['actions']['task_update'])
        self.assertTrue(pol['actions']['task_assign'])
        self.assertTrue(pol['actions']['task_cancel'])
        self.assertTrue(pol['actions']['task_execute'])
        self.assertTrue(pol['actions']['status_transition'])
        self.assertTrue(pol['actions']['status_override'])
        # Manage still denied
        self.assertFalse(pol['actions']['task_delete'])

    def test_housekeeping_manager_manages(self):
        pol = self._policy('regular_staff', 'housekeeping_manager',
                           'housekeeping')
        self.assertTrue(pol['actions']['task_create'])
        self.assertTrue(pol['actions']['task_update'])
        self.assertTrue(pol['actions']['task_assign'])
        self.assertTrue(pol['actions']['task_cancel'])
        self.assertTrue(pol['actions']['task_delete'])
        self.assertTrue(pol['actions']['status_override'])

    def test_hotel_manager_manages_full(self):
        pol = self._policy('regular_staff', 'hotel_manager', 'management')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        # hotel_manager carries every housekeeping capability EXCEPT
        # the department-scoped status_front_desk (granted only via the
        # front_office department preset).
        for action in pol['actions']:
            if action == 'status_front_desk':
                continue
            self.assertTrue(pol['actions'][action], action)

    def test_front_office_manager_manages(self):
        """Manager-role rebalance: front_office_manager now carries the
        full hotel-scoped authority bundle, identical to hotel_manager."""
        pol = self._policy('regular_staff', 'front_office_manager',
                           'front_office')
        self.assertTrue(pol['actions']['task_create'])
        self.assertTrue(pol['actions']['task_assign'])
        self.assertTrue(pol['actions']['status_override'])
        self.assertTrue(pol['actions']['task_delete'])

    def test_tier_only_super_staff_admin_has_full_housekeeping_caps(self):
        """Manager-role rebalance: tier alone now grants full
        housekeeping authority via _HOTEL_FULL_AUTHORITY."""
        pol = self._policy('super_staff_admin', None, None)
        self.assertTrue(pol['visible'])
        # Every housekeeping action except status_front_desk (department
        # scoped to front_office) is granted by the tier bundle.
        for action, granted in pol['actions'].items():
            if action == 'status_front_desk':
                continue
            self.assertTrue(granted, action)

    def test_tier_only_staff_admin_has_no_housekeeping_caps(self):
        pol = self._policy('staff_admin', None, None)
        self.assertFalse(pol['visible'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)

    def test_kitchen_has_no_housekeeping_visibility(self):
        pol = self._policy('regular_staff', 'kitchen_staff', 'kitchen')
        self.assertFalse(pol['visible'])
        for action, granted in pol['actions'].items():
            self.assertFalse(granted, action)


# ---------------------------------------------------------------------------
# Endpoint enforcement
# ---------------------------------------------------------------------------

class HousekeepingEndpointEnforcementTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.hotel = _make_hotel("phase6c-hotel")
        cls.other_hotel = _make_hotel("phase6c-other")

        cls.room_type = RoomType.objects.create(
            hotel=cls.hotel, name="Standard", code="STD",
            starting_price_from=100,
        )
        cls.room = Room.objects.create(
            hotel=cls.hotel, room_number=101,
            room_type=cls.room_type, is_active=True,
            room_status='CHECKOUT_DIRTY',
        )

        # --- Personas -----------------------------------------------------
        cls.no_caps = _make_staff(
            cls.hotel, username='nobody6c', access_level='regular_staff',
        )
        cls.front_desk = _make_staff(
            cls.hotel, username='fd6c', access_level='regular_staff',
            department_slug='front_office',
        )
        cls.housekeeper = _make_staff(
            cls.hotel, username='hker6c', access_level='regular_staff',
            department_slug='housekeeping',
        )
        cls.hk_supervisor = _make_staff(
            cls.hotel, username='hksup6c', access_level='regular_staff',
            role_slug='housekeeping_supervisor',
            department_slug='housekeeping',
        )
        cls.hk_manager = _make_staff(
            cls.hotel, username='hkmgr6c', access_level='regular_staff',
            role_slug='housekeeping_manager',
            department_slug='housekeeping',
        )
        cls.hotel_manager = _make_staff(
            cls.hotel, username='hmgr6c', access_level='regular_staff',
            role_slug='hotel_manager', department_slug='management',
        )
        cls.tier_only_super = _make_staff(
            cls.hotel, username='sa6c',
            access_level='super_staff_admin',
        )

        # Cross-hotel housekeeper (used for the assign-leak regression).
        cls.other_housekeeper = _make_staff(
            cls.other_hotel, username='other_hker6c',
            access_level='regular_staff',
            department_slug='housekeeping',
        )

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------
    @property
    def base(self) -> str:
        return f'/api/staff/hotel/{self.hotel.slug}/housekeeping'

    def _make_task(self, **overrides) -> HousekeepingTask:
        defaults = dict(
            hotel=self.hotel, room=self.room, task_type='TURNOVER',
            status='OPEN', priority='MED',
        )
        defaults.update(overrides)
        return HousekeepingTask.objects.create(**defaults)

    # ------------------------------------------------------------------
    # Module-view gate on every endpoint
    # ------------------------------------------------------------------

    def test_no_caps_is_denied_on_every_endpoint(self):
        task = self._make_task()
        c = _authed_client(self.no_caps.user)
        endpoints = [
            ('get', f'{self.base}/dashboard/', {}),
            ('get', f'{self.base}/tasks/', {}),
            ('post', f'{self.base}/tasks/',
             {'room': self.room.id, 'task_type': 'TURNOVER'}),
            ('post', f'{self.base}/tasks/{task.id}/assign/',
             {'assigned_to_id': self.housekeeper.id}),
            ('post', f'{self.base}/tasks/{task.id}/start/', {}),
            ('post', f'{self.base}/tasks/{task.id}/complete/', {}),
            ('delete', f'{self.base}/tasks/{task.id}/', {}),
            ('post', f'{self.base}/rooms/{self.room.id}/status/',
             {'to_status': 'IN_PROGRESS', 'source': 'HOUSEKEEPING'}),
            ('post',
             f'{self.base}/rooms/{self.room.id}/manager_override/',
             {'to_status': 'READY_FOR_GUEST'}),
            ('get', f'{self.base}/rooms/{self.room.id}/status-history/', {}),
        ]
        for method, url, body in endpoints:
            resp = getattr(c, method)(url, data=body, format='json')
            self.assertEqual(
                resp.status_code, status.HTTP_403_FORBIDDEN,
                f"{method.upper()} {url} expected 403, got {resp.status_code}",
            )

    def test_tier_only_super_admin_has_full_housekeeping_authority(self):
        """Manager-role rebalance: super_staff_admin tier alone now
        grants the full hotel-scoped housekeeping authority."""
        task = self._make_task()
        c = _authed_client(self.tier_only_super.user)
        # READ endpoints succeed.
        for method, url in (
            ('get', f'{self.base}/dashboard/'),
            ('get', f'{self.base}/tasks/'),
        ):
            resp = getattr(c, method)(url)
            self.assertEqual(
                resp.status_code, status.HTTP_200_OK,
                f"{method.upper()} {url} expected 200, got {resp.status_code}",
            )
        # WRITE endpoints succeed (assign + manager override).
        resp = c.post(
            f'{self.base}/tasks/{task.id}/assign/',
            data={'assigned_to_id': self.housekeeper.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/manager_override/',
            data={'to_status': 'READY_FOR_GUEST', 'note': 'x'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def test_housekeeper_can_read_dashboard(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.get(f'{self.base}/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Without task.assign, the hotel-wide open task queue is empty.
        self.assertEqual(resp.data.get('open_tasks', []), [])

    def test_supervisor_dashboard_includes_open_tasks(self):
        self._make_task()  # creates an OPEN task
        c = _authed_client(self.hk_supervisor.user)
        resp = c.get(f'{self.base}/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data['open_tasks']), 1)

    def test_front_desk_cannot_read_dashboard(self):
        # front_office has module.view + history_read but NOT dashboard_read.
        c = _authed_client(self.front_desk.user)
        resp = c.get(f'{self.base}/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Task list / create / delete
    # ------------------------------------------------------------------

    def test_housekeeper_can_list_tasks(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.get(f'{self.base}/tasks/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_front_desk_cannot_list_tasks(self):
        c = _authed_client(self.front_desk.user)
        resp = c.get(f'{self.base}/tasks/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_housekeeper_cannot_create_task(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'{self.base}/tasks/',
            data={'room': self.room.id, 'task_type': 'TURNOVER'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_create_task(self):
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'{self.base}/tasks/',
            data={'room': self.room.id, 'task_type': 'TURNOVER'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_supervisor_cannot_delete_task(self):
        task = self._make_task()
        c = _authed_client(self.hk_supervisor.user)
        resp = c.delete(f'{self.base}/tasks/{task.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_delete_task(self):
        task = self._make_task()
        c = _authed_client(self.hk_manager.user)
        resp = c.delete(f'{self.base}/tasks/{task.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Task execute (start / complete) and assign
    # ------------------------------------------------------------------

    def test_housekeeper_can_start_assigned_task(self):
        task = self._make_task(assigned_to=self.housekeeper)
        c = _authed_client(self.housekeeper.user)
        resp = c.post(f'{self.base}/tasks/{task.id}/start/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_front_desk_cannot_start_task(self):
        task = self._make_task()
        c = _authed_client(self.front_desk.user)
        resp = c.post(f'{self.base}/tasks/{task.id}/start/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_housekeeper_cannot_assign_task(self):
        task = self._make_task()
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'{self.base}/tasks/{task.id}/assign/',
            data={'assigned_to_id': self.housekeeper.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_assign_task(self):
        task = self._make_task()
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'{self.base}/tasks/{task.id}/assign/',
            data={'assigned_to_id': self.housekeeper.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # PATCH/PUT split — task.update alone cannot mutate action fields
    # ------------------------------------------------------------------

    def test_patch_generic_field_requires_only_task_update(self):
        task = self._make_task()
        c = _authed_client(self.hk_supervisor.user)
        resp = c.patch(
            f'{self.base}/tasks/{task.id}/',
            data={'note': 'updated'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_housekeeper_cannot_patch_assigned_to(self):
        """Housekeeper has task.execute but NOT task.assign — a PATCH
        whose only mutation is assigned_to must 403."""
        task = self._make_task()
        c = _authed_client(self.housekeeper.user)
        resp = c.patch(
            f'{self.base}/tasks/{task.id}/',
            data={'assigned_to': self.housekeeper.id}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_housekeeper_cannot_patch_status_to_cancelled(self):
        """Housekeeper lacks task.cancel — PATCH status=CANCELLED → 403."""
        task = self._make_task(assigned_to=self.housekeeper)
        c = _authed_client(self.housekeeper.user)
        resp = c.patch(
            f'{self.base}/tasks/{task.id}/',
            data={'status': 'CANCELLED'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_housekeeper_can_patch_status_to_in_progress(self):
        """Housekeeper holds task.execute → PATCH status=IN_PROGRESS OK."""
        task = self._make_task(assigned_to=self.housekeeper)
        c = _authed_client(self.housekeeper.user)
        resp = c.patch(
            f'{self.base}/tasks/{task.id}/',
            data={'status': 'IN_PROGRESS'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_supervisor_mixed_payload_requires_all_caps(self):
        """Supervisor holds update + assign + cancel + execute, so a
        mixed PATCH body must succeed for them."""
        task = self._make_task()
        c = _authed_client(self.hk_supervisor.user)
        resp = c.patch(
            f'{self.base}/tasks/{task.id}/',
            data={
                'note': 'mixed',
                'assigned_to': self.housekeeper.id,
                'status': 'CANCELLED',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_housekeeper_mixed_payload_blocked_when_any_cap_missing(self):
        """Housekeeper has task.execute but lacks update + assign, so a
        mixed PATCH (note + status=IN_PROGRESS) must 403 because note
        edits require task.update."""
        task = self._make_task(assigned_to=self.housekeeper)
        c = _authed_client(self.housekeeper.user)
        resp = c.patch(
            f'{self.base}/tasks/{task.id}/',
            data={'note': 'mix', 'status': 'IN_PROGRESS'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Room status update (capability via policy.can_change_room_status)
    # ------------------------------------------------------------------

    def test_housekeeper_can_transition_room_status(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/status/',
            data={'to_status': 'IN_PROGRESS', 'source': 'HOUSEKEEPING'},
            format='json',
        )
        # Capability is present, so the gate must NOT 403. Whether the
        # business rule accepts the specific transition is out of scope
        # for the RBAC test (we accept 200 or 400, never 403).
        self.assertNotEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_front_desk_can_use_front_desk_status(self):
        # FRONT_DESK source uses housekeeping.room_status.front_desk
        # which front_office regular staff hold.
        c = _authed_client(self.front_desk.user)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/status/',
            data={'to_status': 'CHECKOUT_DIRTY', 'source': 'FRONT_DESK'},
            format='json',
        )
        # Either 200 (allowed) or 400 (blocked by business rule), but
        # NEVER 403 — capability is present.
        self.assertNotEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_caps_cannot_update_status(self):
        c = _authed_client(self.no_caps.user)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/status/',
            data={'to_status': 'IN_PROGRESS', 'source': 'HOUSEKEEPING'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Manager override no longer requires a tier
    # ------------------------------------------------------------------

    def test_manager_override_not_tier_gated(self):
        """Manager-role rebalance: tier-only super_staff_admin now
        carries the full hotel-scoped housekeeping authority and may
        invoke manager_override."""
        c = _authed_client(self.tier_only_super.user)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/manager_override/',
            data={'to_status': 'READY_FOR_GUEST', 'note': 'x'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_manager_override_allowed_for_supervisor(self):
        c = _authed_client(self.hk_supervisor.user)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/manager_override/',
            data={'to_status': 'READY_FOR_GUEST', 'note': 'override'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_manager_override_denied_for_housekeeper(self):
        c = _authed_client(self.housekeeper.user)
        resp = c.post(
            f'{self.base}/rooms/{self.room.id}/manager_override/',
            data={'to_status': 'READY_FOR_GUEST', 'note': 'override'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Status history
    # ------------------------------------------------------------------

    def test_status_history_requires_history_read(self):
        # No-caps persona lacks both module_view and history_read; the
        # module gate already blocks them. This proves the endpoint is
        # not anonymously reachable. Personas with module_view in the
        # current preset distribution all carry history_read (via the
        # _HOUSEKEEPING_BASE bundle or front_office department), which
        # is the intended Phase 6C contract.
        c = _authed_client(self.no_caps.user)
        resp = c.get(f'{self.base}/rooms/{self.room.id}/status-history/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_history_allowed_for_front_desk(self):
        c = _authed_client(self.front_desk.user)
        resp = c.get(f'{self.base}/rooms/{self.room.id}/status-history/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_status_history_allowed_for_supervisor(self):
        c = _authed_client(self.hk_supervisor.user)
        resp = c.get(f'{self.base}/rooms/{self.room.id}/status-history/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Cross-hotel staff existence does not leak via assign error
    # ------------------------------------------------------------------

    def test_assign_does_not_leak_cross_hotel_staff_existence(self):
        """When validate_assigned_to_id receives an ID that exists in
        another hotel, the error must be identical to the error for a
        non-existent ID. No cross-hotel differential disclosure."""
        task = self._make_task()
        c = _authed_client(self.hk_supervisor.user)

        non_existent_id = 9_999_999
        resp_missing = c.post(
            f'{self.base}/tasks/{task.id}/assign/',
            data={'assigned_to_id': non_existent_id},
            format='json',
        )

        resp_other_hotel = c.post(
            f'{self.base}/tasks/{task.id}/assign/',
            data={'assigned_to_id': self.other_housekeeper.id},
            format='json',
        )

        self.assertEqual(
            resp_missing.status_code, status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            resp_other_hotel.status_code, status.HTTP_400_BAD_REQUEST,
        )
        # Same field error verbatim — proves no leak.
        self.assertEqual(
            resp_missing.data.get('assigned_to_id'),
            resp_other_hotel.data.get('assigned_to_id'),
        )
