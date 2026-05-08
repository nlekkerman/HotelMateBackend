"""
RBAC Phase 5 — nav / capability consistency validators.

These tests pin the diagnostic validators added in Phase 5:
- ``validate_nav_capability_consistency``
- ``validate_visibility_read_coherence``

They run alongside the existing ``validate_module_policy`` /
``validate_preset_maps`` checks already covered by the per-domain RBAC test
modules (``test_rbac_bookings.py``, ``test_rbac_rooms.py``, …).

Architecture invariants pinned here:

1. Visibility/read coherence — for every preset bundle (tier, role,
   department), ``module.view_capability`` and ``module.read_capability``
   are either both granted or both absent. Authority-only bundles such
   as ``_SUPERVISOR_AUTHORITY`` (chat moderate / staff_chat moderate
   without module view) are intentionally non-projecting and remain
   coherent because they carry neither view nor read for those modules.

2. Nav drift — ``TIER_DEFAULT_NAVS`` lists nav slugs whose
   ``module.view_capability`` is not on the same tier bundle. This is
   acceptable iff role / department presets fill the gap. The test
   pins the *expected* drift set so any future preset change that
   introduces additional drift fails this test.

3. Canonical roles do not currently seed ``Role.default_navigation_items``
   in the DB; the canonical-role coverage branch of
   ``validate_nav_capability_consistency`` runs against the live DB
   snapshot and asserts no role emits a nav slug it cannot see.
"""

from django.test import TestCase

from hotel.models import Hotel
from staff.capability_catalog import (
    validate_nav_capability_consistency,
    validate_preset_maps,
    validate_visibility_read_coherence,
)
from staff.models import Role
from staff.module_policy import validate_module_policy


# Tier nav slugs whose ``view_capability`` is not on the same tier
# bundle. Each entry is acceptable because the corresponding nav slug
# only resolves into ``allowed_navs`` when the staff row also carries a
# role / department preset that grants the missing view_capability.
# Adding a new entry here requires a deliberate review of the nav
# rendering contract (frontend gates on ``rbac.<module>.visible`` AND
# ``allowed_navs`` — see ``RBAC_OPERATIONAL_REBALANCE_AUDIT.md`` §4.4).
EXPECTED_TIER_NAV_DRIFT: frozenset[str] = frozenset({
    # super_staff_admin tier carries _HOTEL_FULL_AUTHORITY (Manager-role
    # rebalance) so every hotel-scoped nav slug projects from the tier
    # bundle. No drift entries are expected for super_staff_admin.
    # staff_admin — relies on department-head role presets.
    "TIER_DEFAULT_NAVS['staff_admin'] nav='chat' -> module='chat':"
    " view_capability 'chat.module.view' not granted by tier bundle"
    " (relies on role/department preset to be visible)",
    "TIER_DEFAULT_NAVS['staff_admin'] nav='hotel_info' ->"
    " module='hotel_info': view_capability 'hotel_info.module.view' not"
    " granted by tier bundle (relies on role/department preset to be"
    " visible)",
    "TIER_DEFAULT_NAVS['staff_admin'] nav='housekeeping' ->"
    " module='housekeeping': view_capability 'housekeeping.module.view'"
    " not granted by tier bundle (relies on role/department preset to"
    " be visible)",
    "TIER_DEFAULT_NAVS['staff_admin'] nav='maintenance' ->"
    " module='maintenance': view_capability 'maintenance.module.view'"
    " not granted by tier bundle (relies on role/department preset to"
    " be visible)",
    "TIER_DEFAULT_NAVS['staff_admin'] nav='restaurant_bookings' ->"
    " module='restaurant_bookings': view_capability"
    " 'restaurant_booking.module.view' not granted by tier bundle"
    " (relies on role/department preset to be visible)",
    "TIER_DEFAULT_NAVS['staff_admin'] nav='room_bookings' ->"
    " module='bookings': view_capability 'booking.module.view' not"
    " granted by tier bundle (relies on role/department preset to be"
    " visible)",
    "TIER_DEFAULT_NAVS['staff_admin'] nav='rooms' -> module='rooms':"
    " view_capability 'room.module.view' not granted by tier bundle"
    " (relies on role/department preset to be visible)",
    # regular_staff — chat nav only renders when role/dept grants
    # chat.module.view (front_office / guest_relations / management /
    # duty_manager / hotel_manager / GR roles).
    "TIER_DEFAULT_NAVS['regular_staff'] nav='chat' -> module='chat':"
    " view_capability 'chat.module.view' not granted by tier bundle"
    " (relies on role/department preset to be visible)",
})


class NavCapabilityConsistencyTest(TestCase):
    """Phase 5 — nav <-> capability drift validators."""

    def test_preset_maps_self_consistent(self):
        self.assertEqual(validate_preset_maps(), [])

    def test_module_policy_self_consistent(self):
        self.assertEqual(validate_module_policy(), [])

    def test_visibility_read_coherence(self):
        """No preset bundle has visible≠read for any module."""
        self.assertEqual(validate_visibility_read_coherence(), [])

    def test_nav_capability_drift_matches_documented_set(self):
        """Static nav drift exactly matches the documented exception set.

        Any new tier-level nav drift fails this test, forcing a review.
        """
        actual = set(validate_nav_capability_consistency())
        self.assertEqual(
            actual, EXPECTED_TIER_NAV_DRIFT,
            "Tier nav drift changed. Either fix the preset / nav default "
            "or update EXPECTED_TIER_NAV_DRIFT after auditing the change.",
        )

    def test_canonical_role_default_navs_have_no_orphans(self):
        """Every Role.default_navigation_items entry is reachable.

        For every Role row with default_navigation_items, assert that
        the role's resolved capability bundle (regular_staff tier ∪
        role preset ∪ canonical-dept preset) grants
        ``module.view_capability`` for every nav slug projected to a
        module. Roles with no nav assignments (current DB state) pass
        trivially.
        """
        # Need a hotel to materialize nav rows, but we only assert that
        # *existing* role default-nav assignments project consistently.
        Hotel.objects.create(name="Test Hotel", slug="test-hotel-phase5",
                             timezone="UTC")

        snapshots: list[tuple[str, str | None, list[str]]] = []
        for role in Role.objects.select_related('department').all():
            slugs = list(
                role.default_navigation_items.filter(is_active=True)
                .values_list('slug', flat=True)
            )
            if not slugs:
                continue
            dept_slug = role.department.slug if role.department else None
            snapshots.append((role.slug, dept_slug, slugs))

        # Run the validator with only the canonical-role coverage branch
        # by filtering its output for role-level findings.
        findings = validate_nav_capability_consistency(
            role_default_navs=snapshots,
        )
        role_findings = [f for f in findings if f.startswith('Role[')]
        self.assertEqual(
            role_findings, [],
            "Role.default_navigation_items contain orphaned entries: "
            f"{role_findings}",
        )
