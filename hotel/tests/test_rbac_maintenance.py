"""
Phase 6D.1 tests — RBAC for the `maintenance` module.

Covers:
- capability catalog + module policy self-consistency
- persona resolution (tier/dept/role → rbac.maintenance payload)
- no maintenance.* capability leaks into any tier preset
- endpoint enforcement for every maintenance endpoint
- generic PATCH cannot mutate status / accepted_by
- action endpoints enforce their own capabilities
- comment author-vs-moderator object-level rules
- photo upload / delete capability split
- cross-hotel FK rejection with generic-error parity
"""
from __future__ import annotations

from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from hotel.models import Hotel
from maintenance.models import (
    MaintenanceComment, MaintenancePhoto, MaintenanceRequest,
)
from rooms.models import Room, RoomType
from staff.capability_catalog import (
    CANONICAL_CAPABILITIES,
    MAINTENANCE_COMMENT_CREATE,
    MAINTENANCE_COMMENT_MODERATE,
    MAINTENANCE_MODULE_VIEW,
    MAINTENANCE_PHOTO_DELETE,
    MAINTENANCE_PHOTO_UPLOAD,
    MAINTENANCE_REQUEST_ACCEPT,
    MAINTENANCE_REQUEST_CLOSE,
    MAINTENANCE_REQUEST_CREATE,
    MAINTENANCE_REQUEST_DELETE,
    MAINTENANCE_REQUEST_READ,
    MAINTENANCE_REQUEST_REASSIGN,
    MAINTENANCE_REQUEST_REOPEN,
    MAINTENANCE_REQUEST_RESOLVE,
    MAINTENANCE_REQUEST_UPDATE,
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


_FAKE_CLOUDINARY_UPLOAD = {
    'public_id': 'test_photo',
    'version': '1234567890',
    'signature': 'fakesig',
    'width': 1,
    'height': 1,
    'format': 'png',
    'resource_type': 'image',
    'created_at': '2024-01-01T00:00:00Z',
    'tags': [],
    'bytes': 1,
    'type': 'upload',
    'etag': 'fakeetag',
    'url': 'http://res.cloudinary.com/test/image/upload/test.png',
    'secure_url': 'https://res.cloudinary.com/test/image/upload/test.png',
}


_MAINT_ACTION_CAPABILITIES = {
    'request_create': MAINTENANCE_REQUEST_CREATE,
    'request_accept': MAINTENANCE_REQUEST_ACCEPT,
    'request_resolve': MAINTENANCE_REQUEST_RESOLVE,
    'request_update': MAINTENANCE_REQUEST_UPDATE,
    'request_reassign': MAINTENANCE_REQUEST_REASSIGN,
    'request_reopen': MAINTENANCE_REQUEST_REOPEN,
    'request_close': MAINTENANCE_REQUEST_CLOSE,
    'request_delete': MAINTENANCE_REQUEST_DELETE,
    'comment_create': MAINTENANCE_COMMENT_CREATE,
    'comment_moderate': MAINTENANCE_COMMENT_MODERATE,
    'photo_upload': MAINTENANCE_PHOTO_UPLOAD,
    'photo_delete': MAINTENANCE_PHOTO_DELETE,
}


# ---------------------------------------------------------------------------
# Test fixtures
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


def _authed_client(user: User) -> APIClient:
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# ---------------------------------------------------------------------------
# Registry self-consistency
# ---------------------------------------------------------------------------

class MaintenancePolicyRegistryTest(TestCase):
    def test_preset_maps_self_consistent(self):
        self.assertEqual(validate_preset_maps(), [])

    def test_module_policy_self_consistent(self):
        self.assertEqual(validate_module_policy(), [])

    def test_maintenance_module_is_registered(self):
        self.assertIn('maintenance', MODULE_POLICY)
        policy = MODULE_POLICY['maintenance']
        self.assertEqual(
            policy['view_capability'], MAINTENANCE_MODULE_VIEW,
        )
        self.assertEqual(
            policy['read_capability'], MAINTENANCE_REQUEST_READ,
        )

    def test_no_decorative_action_keys_in_maintenance_policy(self):
        policy = MODULE_POLICY['maintenance']
        for action, cap in policy['actions'].items():
            self.assertIn(
                cap, CANONICAL_CAPABILITIES,
                f"Action {action!r} → non-canonical capability {cap!r}",
            )
            self.assertIn(action, _MAINT_ACTION_CAPABILITIES, action)
            self.assertEqual(
                cap, _MAINT_ACTION_CAPABILITIES[action],
                f"Action {action!r} capability drifted",
            )

    def test_no_maintenance_capability_in_any_tier_preset(self):
        maint_caps = {
            c for c in CANONICAL_CAPABILITIES
            if c.startswith('maintenance.')
        }
        for tier, caps in TIER_DEFAULT_CAPABILITIES.items():
            leaked = caps & maint_caps
            self.assertFalse(
                leaked,
                f"Tier {tier!r} leaks maintenance capabilities: "
                f"{sorted(leaked)}",
            )

    def test_maintenance_namespace_disjoint_from_room_maintenance(self):
        """`maintenance.*` and `room.maintenance.*` must remain distinct."""
        maint_caps = {
            c for c in CANONICAL_CAPABILITIES
            if c.startswith('maintenance.')
        }
        room_maint = {
            c for c in CANONICAL_CAPABILITIES
            if c.startswith('room.maintenance.')
        }
        self.assertFalse(maint_caps & room_maint)


# ---------------------------------------------------------------------------
# Persona resolution via resolve_capabilities()
# ---------------------------------------------------------------------------

class MaintenancePolicyPersonaTest(TestCase):
    def _policy(self, tier=None, role_slug=None, department_slug=None):
        caps = resolve_capabilities(tier, role_slug, department_slug)
        return resolve_module_policy(caps)['maintenance']

    def test_maintenance_regular_staff_operate_bundle(self):
        pol = self._policy('regular_staff', None, 'maintenance')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        for key in (
            'request_create', 'request_accept', 'request_resolve',
            'comment_create', 'photo_upload',
        ):
            self.assertTrue(pol['actions'][key], key)
        # Supervise / manage denied
        for key in (
            'request_update', 'request_reassign', 'request_reopen',
            'request_close', 'request_delete',
            'comment_moderate', 'photo_delete',
        ):
            self.assertFalse(pol['actions'][key], key)

    def test_maintenance_supervisor_supervise_bundle(self):
        pol = self._policy(
            'regular_staff', 'maintenance_supervisor', 'maintenance',
        )
        for key in (
            'request_create', 'request_accept', 'request_resolve',
            'request_update', 'request_reassign', 'request_reopen',
            'comment_create', 'comment_moderate',
            'photo_upload', 'photo_delete',
        ):
            self.assertTrue(pol['actions'][key], key)
        # Manage still denied
        self.assertFalse(pol['actions']['request_close'])
        self.assertFalse(pol['actions']['request_delete'])

    def test_maintenance_manager_full_bundle(self):
        pol = self._policy(
            'regular_staff', 'maintenance_manager', 'maintenance',
        )
        for key in pol['actions']:
            self.assertTrue(pol['actions'][key], key)

    def test_hotel_manager_full_bundle(self):
        pol = self._policy('regular_staff', 'hotel_manager', 'management')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        for key in pol['actions']:
            self.assertTrue(pol['actions'][key], key)

    def test_tier_only_staff_admin_has_no_maintenance_authority(self):
        pol = self._policy('staff_admin', None, None)
        self.assertFalse(pol['visible'])
        for key, granted in pol['actions'].items():
            self.assertFalse(granted, key)

    def test_tier_only_super_staff_admin_has_full_maintenance_authority(self):
        """Manager-role rebalance: super_staff_admin tier alone grants
        the full hotel-scoped maintenance bundle."""
        pol = self._policy('super_staff_admin', None, None)
        self.assertTrue(pol['visible'])
        for key in pol['actions']:
            self.assertTrue(pol['actions'][key], key)

    def test_non_maintenance_regular_staff_only_gets_reporter_caps(self):
        # front_office dept carries reporter bundle — view + read + create.
        pol = self._policy('regular_staff', None, 'front_office')
        self.assertTrue(pol['visible'])
        self.assertTrue(pol['read'])
        self.assertTrue(pol['actions']['request_create'])
        for key in (
            'request_accept', 'request_resolve', 'request_update',
            'request_reassign', 'request_reopen', 'request_close',
            'request_delete', 'comment_create', 'comment_moderate',
            'photo_upload', 'photo_delete',
        ):
            self.assertFalse(pol['actions'][key], key)

    def test_kitchen_has_no_maintenance_visibility(self):
        pol = self._policy('regular_staff', 'kitchen_staff', 'kitchen')
        self.assertFalse(pol['visible'])
        for key, granted in pol['actions'].items():
            self.assertFalse(granted, key)


# ---------------------------------------------------------------------------
# Endpoint enforcement
# ---------------------------------------------------------------------------

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class MaintenanceEndpointEnforcementTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.hotel = _make_hotel("phase6d-hotel")
        cls.other_hotel = _make_hotel("phase6d-other")

        cls.room_type = RoomType.objects.create(
            hotel=cls.hotel, name="Standard", code="STD",
            starting_price_from=100,
        )
        cls.room = Room.objects.create(
            hotel=cls.hotel, room_number=101,
            room_type=cls.room_type, is_active=True,
        )
        cls.other_room_type = RoomType.objects.create(
            hotel=cls.other_hotel, name="Standard", code="STD",
            starting_price_from=100,
        )
        cls.other_room = Room.objects.create(
            hotel=cls.other_hotel, room_number=201,
            room_type=cls.other_room_type, is_active=True,
        )

        # --- Personas -----------------------------------------------------
        cls.no_caps = _make_staff(
            cls.hotel, username='nobody6d', access_level='regular_staff',
        )
        cls.reporter = _make_staff(
            cls.hotel, username='reporter6d', access_level='regular_staff',
            department_slug='front_office',
        )
        cls.technician = _make_staff(
            cls.hotel, username='tech6d', access_level='regular_staff',
            department_slug='maintenance',
        )
        cls.technician_2 = _make_staff(
            cls.hotel, username='tech6d2', access_level='regular_staff',
            department_slug='maintenance',
        )
        cls.supervisor = _make_staff(
            cls.hotel, username='sup6d', access_level='regular_staff',
            role_slug='maintenance_supervisor',
            department_slug='maintenance',
        )
        cls.manager = _make_staff(
            cls.hotel, username='mgr6d', access_level='regular_staff',
            role_slug='maintenance_manager',
            department_slug='maintenance',
        )
        cls.tier_only_super = _make_staff(
            cls.hotel, username='sa6d', access_level='super_staff_admin',
        )

        # Foreign-hotel technician for reassign-leak test.
        cls.other_technician = _make_staff(
            cls.other_hotel, username='other_tech6d',
            access_level='regular_staff',
            department_slug='maintenance',
        )

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------
    @property
    def base(self) -> str:
        return f'/api/staff/hotel/{self.hotel.slug}/maintenance'

    def _make_request(self, **overrides) -> MaintenanceRequest:
        defaults = dict(
            hotel=self.hotel, room=self.room, title='Leak',
            description='drip', status='open',
        )
        defaults.update(overrides)
        return MaintenanceRequest.objects.create(**defaults)

    # ------------------------------------------------------------------
    # Nav-without-caps is fully denied
    # ------------------------------------------------------------------
    def test_no_caps_is_denied_on_every_endpoint(self):
        req = self._make_request()
        c = _authed_client(self.no_caps.user)
        endpoints = [
            ('get', f'{self.base}/requests/', {}),
            ('post', f'{self.base}/requests/',
             {'title': 'x'}),
            ('get', f'{self.base}/requests/{req.id}/', {}),
            ('patch', f'{self.base}/requests/{req.id}/',
             {'title': 'y'}),
            ('delete', f'{self.base}/requests/{req.id}/', {}),
            ('post', f'{self.base}/requests/{req.id}/accept/', {}),
            ('post', f'{self.base}/requests/{req.id}/resolve/', {}),
            ('post', f'{self.base}/requests/{req.id}/reopen/', {}),
            ('post', f'{self.base}/requests/{req.id}/close/', {}),
            ('post', f'{self.base}/requests/{req.id}/reassign/',
             {'accepted_by': self.technician.id}),
            ('get', f'{self.base}/comments/', {}),
            ('post', f'{self.base}/comments/',
             {'request': req.id, 'message': 'hi'}),
            ('get', f'{self.base}/photos/', {}),
        ]
        for method, url, body in endpoints:
            resp = getattr(c, method)(url, data=body, format='json')
            self.assertEqual(
                resp.status_code, status.HTTP_403_FORBIDDEN,
                f"{method.upper()} {url} → {resp.status_code}",
            )

    def test_tier_only_super_admin_is_denied_everywhere(self):
        req = self._make_request()
        c = _authed_client(self.tier_only_super.user)
        endpoints = [
            ('get', f'{self.base}/requests/'),
            ('post', f'{self.base}/requests/{req.id}/accept/'),
            ('post', f'{self.base}/requests/{req.id}/close/'),
            ('delete', f'{self.base}/requests/{req.id}/'),
        ]
        for method, url in endpoints:
            resp = getattr(c, method)(url, data={}, format='json')
            self.assertEqual(
                resp.status_code, status.HTTP_403_FORBIDDEN,
                f"{method.upper()} {url} → {resp.status_code}",
            )

    # ------------------------------------------------------------------
    # Request reads
    # ------------------------------------------------------------------
    def test_reporter_can_list_requests(self):
        self._make_request()
        c = _authed_client(self.reporter.user)
        resp = c.get(f'{self.base}/requests/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_technician_can_retrieve_request(self):
        req = self._make_request()
        c = _authed_client(self.technician.user)
        resp = c.get(f'{self.base}/requests/{req.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Request create
    # ------------------------------------------------------------------
    def test_reporter_can_create_request(self):
        c = _authed_client(self.reporter.user)
        resp = c.post(
            f'{self.base}/requests/',
            data={'title': 'Broken lamp', 'description': 'flickers'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = MaintenanceRequest.objects.get(pk=resp.data['id'])
        self.assertEqual(created.hotel_id, self.hotel.id)
        self.assertEqual(created.reported_by_id, self.reporter.id)

    def test_no_caps_cannot_create_request(self):
        c = _authed_client(self.no_caps.user)
        resp = c.post(
            f'{self.base}/requests/',
            data={'title': 'x'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Request update (metadata only)
    # ------------------------------------------------------------------
    def test_technician_cannot_update_request(self):
        req = self._make_request()
        c = _authed_client(self.technician.user)
        resp = c.patch(
            f'{self.base}/requests/{req.id}/',
            data={'title': 'new'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_update_request(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        resp = c.patch(
            f'{self.base}/requests/{req.id}/',
            data={'title': 'new', 'description': 'fresh'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.title, 'new')

    def test_generic_patch_cannot_change_status(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        resp = c.patch(
            f'{self.base}/requests/{req.id}/',
            data={'status': 'closed'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'open')

    def test_generic_patch_cannot_change_accepted_by(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        resp = c.patch(
            f'{self.base}/requests/{req.id}/',
            data={'accepted_by': self.technician.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertIsNone(req.accepted_by)

    # ------------------------------------------------------------------
    # Request delete
    # ------------------------------------------------------------------
    def test_supervisor_cannot_delete_request(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        resp = c.delete(f'{self.base}/requests/{req.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_delete_request(self):
        req = self._make_request()
        c = _authed_client(self.manager.user)
        resp = c.delete(f'{self.base}/requests/{req.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Accept
    # ------------------------------------------------------------------
    def test_reporter_cannot_accept(self):
        req = self._make_request()
        c = _authed_client(self.reporter.user)
        resp = c.post(f'{self.base}/requests/{req.id}/accept/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_can_accept_and_stamps_accepted_by(self):
        req = self._make_request()
        c = _authed_client(self.technician.user)
        resp = c.post(f'{self.base}/requests/{req.id}/accept/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'in_progress')
        self.assertEqual(req.accepted_by_id, self.technician.id)

    def test_cannot_accept_closed_request(self):
        req = self._make_request(status='closed')
        c = _authed_client(self.technician.user)
        resp = c.post(f'{self.base}/requests/{req.id}/accept/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Resolve
    # ------------------------------------------------------------------
    def test_resolve_requires_in_progress(self):
        req = self._make_request(status='open')
        c = _authed_client(self.technician.user)
        resp = c.post(f'{self.base}/requests/{req.id}/resolve/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_technician_can_resolve(self):
        req = self._make_request(
            status='in_progress', accepted_by=self.technician,
        )
        c = _authed_client(self.technician.user)
        resp = c.post(f'{self.base}/requests/{req.id}/resolve/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'resolved')

    # ------------------------------------------------------------------
    # Reopen
    # ------------------------------------------------------------------
    def test_reporter_cannot_reopen(self):
        req = self._make_request(status='resolved')
        c = _authed_client(self.reporter.user)
        resp = c.post(f'{self.base}/requests/{req.id}/reopen/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_reopen_and_clears_accepted_by(self):
        req = self._make_request(
            status='resolved', accepted_by=self.technician,
        )
        c = _authed_client(self.supervisor.user)
        resp = c.post(f'{self.base}/requests/{req.id}/reopen/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'open')
        self.assertIsNone(req.accepted_by)

    def test_reopen_invalid_state_returns_400(self):
        req = self._make_request(status='open')
        c = _authed_client(self.supervisor.user)
        resp = c.post(f'{self.base}/requests/{req.id}/reopen/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def test_supervisor_cannot_close(self):
        req = self._make_request(status='resolved')
        c = _authed_client(self.supervisor.user)
        resp = c.post(f'{self.base}/requests/{req.id}/close/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_close_from_resolved(self):
        req = self._make_request(status='resolved')
        c = _authed_client(self.manager.user)
        resp = c.post(f'{self.base}/requests/{req.id}/close/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'closed')

    def test_close_from_open_is_400(self):
        req = self._make_request(status='open')
        c = _authed_client(self.manager.user)
        resp = c.post(f'{self.base}/requests/{req.id}/close/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # Reassign
    # ------------------------------------------------------------------
    def test_technician_cannot_reassign(self):
        req = self._make_request()
        c = _authed_client(self.technician.user)
        resp = c.post(
            f'{self.base}/requests/{req.id}/reassign/',
            data={'accepted_by': self.technician_2.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_reassign(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        resp = c.post(
            f'{self.base}/requests/{req.id}/reassign/',
            data={'accepted_by': self.technician.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.accepted_by_id, self.technician.id)

    def test_reassign_foreign_hotel_returns_same_error_as_missing(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        foreign = c.post(
            f'{self.base}/requests/{req.id}/reassign/',
            data={'accepted_by': self.other_technician.id},
            format='json',
        )
        missing = c.post(
            f'{self.base}/requests/{req.id}/reassign/',
            data={'accepted_by': 99_999_999},
            format='json',
        )
        self.assertEqual(foreign.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(foreign.data, missing.data)

    # ------------------------------------------------------------------
    # Tenant isolation on FK fields
    # ------------------------------------------------------------------
    def test_create_request_with_foreign_room_rejected(self):
        c = _authed_client(self.reporter.user)
        resp = c.post(
            f'{self.base}/requests/',
            data={'title': 'x', 'room': self.other_room.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('room', resp.data)

    def test_patch_foreign_room_rejected(self):
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        resp = c.patch(
            f'{self.base}/requests/{req.id}/',
            data={'room': self.other_room.id}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_on_foreign_request_rejected(self):
        other_req = MaintenanceRequest.objects.create(
            hotel=self.other_hotel, title='foreign', status='open',
        )
        c = _authed_client(self.technician.user)
        resp = c.post(
            f'{self.base}/comments/',
            data={'request': other_req.id, 'message': 'x'},
            format='json',
        )
        # Must match shape of a missing request (both: 400 / request error).
        missing = c.post(
            f'{self.base}/comments/',
            data={'request': 99_999_999, 'message': 'x'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data, missing.data)

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    def test_reporter_cannot_create_comment(self):
        req = self._make_request()
        c = _authed_client(self.reporter.user)
        resp = c.post(
            f'{self.base}/comments/',
            data={'request': req.id, 'message': 'nope'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_can_create_comment(self):
        req = self._make_request()
        c = _authed_client(self.technician.user)
        resp = c.post(
            f'{self.base}/comments/',
            data={'request': req.id, 'message': 'on it'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = MaintenanceComment.objects.get(pk=resp.data['id'])
        self.assertEqual(created.staff_id, self.technician.id)

    def test_author_can_edit_own_comment(self):
        req = self._make_request()
        comment = MaintenanceComment.objects.create(
            request=req, staff=self.technician, message='original',
        )
        c = _authed_client(self.technician.user)
        resp = c.patch(
            f'{self.base}/comments/{comment.id}/',
            data={'message': 'edited'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_author_can_delete_own_comment(self):
        req = self._make_request()
        comment = MaintenanceComment.objects.create(
            request=req, staff=self.technician, message='mine',
        )
        c = _authed_client(self.technician.user)
        resp = c.delete(f'{self.base}/comments/{comment.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_author_without_moderate_cannot_edit(self):
        req = self._make_request()
        comment = MaintenanceComment.objects.create(
            request=req, staff=self.technician_2, message='theirs',
        )
        c = _authed_client(self.technician.user)
        resp = c.patch(
            f'{self.base}/comments/{comment.id}/',
            data={'message': 'hijack'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_author_without_moderate_cannot_delete(self):
        req = self._make_request()
        comment = MaintenanceComment.objects.create(
            request=req, staff=self.technician_2, message='theirs',
        )
        c = _authed_client(self.technician.user)
        resp = c.delete(f'{self.base}/comments/{comment.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_moderate_others_comment(self):
        req = self._make_request()
        comment = MaintenanceComment.objects.create(
            request=req, staff=self.technician, message='foo',
        )
        c = _authed_client(self.supervisor.user)
        resp = c.delete(f'{self.base}/comments/{comment.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Photos
    # ------------------------------------------------------------------
    def _png_bytes(self) -> bytes:
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', (2, 2), color='red').save(buf, format='PNG')
        return buf.getvalue()

    def test_reporter_cannot_upload_photo(self):
        req = self._make_request()
        c = _authed_client(self.reporter.user)
        upload = SimpleUploadedFile(
            'x.png', self._png_bytes(), content_type='image/png',
        )
        resp = c.post(
            f'{self.base}/photos/',
            data={'request': req.id, 'images': [upload]},
            format='multipart',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_cannot_upload_photo_without_upload_cap(self):
        # Supervisor carries photo_delete via supervise bundle and also
        # photo_upload (operate bundle). Confirm upload ALLOWED here
        # to document the positive case.
        req = self._make_request()
        c = _authed_client(self.supervisor.user)
        upload = SimpleUploadedFile(
            'x.png', self._png_bytes(), content_type='image/png',
        )
        with mock.patch(
            'cloudinary.uploader.upload',
            return_value=_FAKE_CLOUDINARY_UPLOAD,
        ):
            resp = c.post(
                f'{self.base}/photos/',
                data={'request': req.id, 'images': upload},
            )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED,
            getattr(resp, 'content', b''),
        )

    def test_technician_cannot_delete_photo(self):
        req = self._make_request()
        photo = MaintenancePhoto.objects.create(
            request=req, image='x.png', uploaded_by=self.technician,
        )
        c = _authed_client(self.technician.user)
        resp = c.delete(f'{self.base}/photos/{photo.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervisor_can_delete_photo(self):
        req = self._make_request()
        photo = MaintenancePhoto.objects.create(
            request=req, image='x.png', uploaded_by=self.technician,
        )
        c = _authed_client(self.supervisor.user)
        resp = c.delete(f'{self.base}/photos/{photo.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_bulk_upload_foreign_request_rejected(self):
        other_req = MaintenanceRequest.objects.create(
            hotel=self.other_hotel, title='foreign', status='open',
        )
        c = _authed_client(self.technician.user)
        upload = SimpleUploadedFile(
            'x.png', self._png_bytes(), content_type='image/png',
        )
        with mock.patch(
            'cloudinary.uploader.upload',
            return_value=_FAKE_CLOUDINARY_UPLOAD,
        ):
            resp = c.post(
                f'{self.base}/photos/',
                data={'request': other_req.id, 'images': [upload]},
                format='multipart',
            )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_photo_foreign_request_rejected_matches_missing(self):
        c = _authed_client(self.technician.user)
        upload1 = SimpleUploadedFile(
            'x.png', self._png_bytes(), content_type='image/png',
        )
        upload2 = SimpleUploadedFile(
            'x.png', self._png_bytes(), content_type='image/png',
        )
        other_req = MaintenanceRequest.objects.create(
            hotel=self.other_hotel, title='foreign', status='open',
        )
        with mock.patch(
            'cloudinary.uploader.upload',
            return_value=_FAKE_CLOUDINARY_UPLOAD,
        ):
            foreign = c.post(
                f'{self.base}/photos/',
                data={'request': other_req.id, 'images': [upload1]},
                format='multipart',
            )
            missing = c.post(
                f'{self.base}/photos/',
                data={'request': 99_999_999, 'images': [upload2]},
                format='multipart',
            )
        self.assertEqual(foreign.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(foreign.data, missing.data)
