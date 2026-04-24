"""
Phase 6A.1 — Bookings RBAC Validation Pass

Break-test harness. Prints:
  A) Actual rbac.bookings payloads for real staff users
  B) Endpoint coverage table (view → required capabilities)
  C) Bucket separation pass/fail (read/operate/supervise/manage)
  D) Domain isolation check (room bookings vs restaurant bookings)
  E) Capability distribution weak points
"""
import os
import django
import json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotelmate.settings")
django.setup()

from collections import defaultdict
from staff.models import Staff
from staff.permissions import (
    resolve_effective_access,
    resolve_tier,
    has_capability,
)
from staff.module_policy import (
    MODULE_POLICY,
    resolve_module_policy,
    validate_module_policy,
    BOOKINGS_ACTIONS,
)
from staff.capability_catalog import (
    CANONICAL_CAPABILITIES,
    TIER_DEFAULT_CAPABILITIES,
    ROLE_PRESET_CAPABILITIES,
    DEPARTMENT_PRESET_CAPABILITIES,
    resolve_capabilities,
    BOOKING_MODULE_VIEW,
    BOOKING_RECORD_READ,
    BOOKING_RECORD_UPDATE,
    BOOKING_RECORD_CANCEL,
    BOOKING_ROOM_ASSIGN,
    BOOKING_STAY_CHECKIN,
    BOOKING_STAY_CHECKOUT,
    BOOKING_GUEST_COMMUNICATE,
    BOOKING_OVERRIDE_SUPERVISE,
    BOOKING_CONFIG_MANAGE,
)


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


def section(t):
    print("\n--- " + t + " ---")


# ---------------------------------------------------------------------------
# 0. Registry self-check
# ---------------------------------------------------------------------------
hdr("0. Registry self-check")
print("validate_module_policy():", validate_module_policy())
print("MODULE_POLICY keys:", list(MODULE_POLICY.keys()))
print("BOOKINGS_ACTIONS keys:", sorted(BOOKINGS_ACTIONS.keys()))


# ---------------------------------------------------------------------------
# A. Real staff payload validation
# ---------------------------------------------------------------------------
hdr("A. Real staff rbac.bookings payload (live DB)")

# Try to find representative users:
# Front desk agent (role), a supervisor (staff_admin or super_staff_admin + front_office),
# a manager (super_staff_admin tier).

def _resolve_for_staff(staff):
    tier = staff.access_level
    # Our resolver accepts user, so emulate via user lookup
    return resolve_effective_access(staff.user)


targets = []
# front desk agent
fd = Staff.objects.filter(role__slug='front_desk_agent', is_active=True).select_related('user', 'role', 'department', 'hotel').first()
if fd:
    targets.append(('front_desk_agent', fd))

# supervisor: anyone on staff_admin tier
sup = Staff.objects.filter(access_level='staff_admin', is_active=True).exclude(pk=fd.pk if fd else 0).select_related('user','role','department','hotel').first()
if sup:
    targets.append(('staff_admin (supervisor tier)', sup))

# manager: super_staff_admin tier, ideally front_office_manager
mgr = Staff.objects.filter(access_level='super_staff_admin', is_active=True).select_related('user','role','department','hotel').first()
if mgr:
    targets.append(('super_staff_admin (manager tier)', mgr))

# operations_admin
ops = Staff.objects.filter(role__slug='operations_admin', is_active=True).select_related('user','role','department','hotel').first()
if ops:
    targets.append(('operations_admin role', ops))

# porter (should have ZERO booking caps)
porter = Staff.objects.filter(role__slug='porter', is_active=True).select_related('user','role','department','hotel').first()
if porter:
    targets.append(('porter (should be zero)', porter))

# housekeeper
hk = Staff.objects.filter(department__slug='housekeeping', is_active=True).exclude(access_level__in=['staff_admin','super_staff_admin']).select_related('user','role','department','hotel').first()
if hk:
    targets.append(('housekeeping regular_staff (should be zero)', hk))

for label, s in targets:
    section(f"{label}: user={s.user.username} tier={s.access_level} role={s.role.slug if s.role else None} dept={s.department.slug if s.department else None}")
    payload = _resolve_for_staff(s)
    caps = payload.get('allowed_capabilities', [])
    booking_caps = [c for c in caps if c.startswith('booking.')]
    print("  booking capabilities:", booking_caps)
    rbac = payload.get('rbac', {})
    print("  rbac.bookings:")
    print(json.dumps(rbac.get('bookings', {}), indent=4))


# ---------------------------------------------------------------------------
# B. Endpoint → capability mapping (static doc, cross-checked)
# ---------------------------------------------------------------------------
hdr("B. Endpoint coverage table")

ENDPOINT_MAP = [
    # (method, path, view class, required booking capabilities)
    ("GET",  "/api/staff/hotel/{slug}/room-bookings/",                       "StaffBookingsListView",     ["booking.module.view","booking.record.read"]),
    ("GET",  "/api/staff/hotel/{slug}/room-bookings/{id}/",                  "StaffBookingDetailView",    ["booking.module.view","booking.record.read"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/mark-seen/",        "StaffBookingMarkSeenView",  ["booking.module.view","booking.record.read"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/confirm/",          "StaffBookingConfirmView",   ["booking.module.view","booking.record.read","booking.record.update"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/cancel/",           "StaffBookingCancelView",    ["booking.module.view","booking.record.read","booking.record.cancel"]),
    ("GET",  "/api/staff/hotel/{slug}/room-bookings/{id}/party/",            "BookingPartyManagementView (GET)",  ["booking.module.view","booking.record.read"]),
    ("PUT",  "/api/staff/hotel/{slug}/room-bookings/{id}/party/companions/", "BookingPartyManagementView (PUT)",  ["booking.module.view","booking.record.read","booking.record.update"]),
    ("GET",  "/api/staff/hotel/{slug}/room-bookings/{id}/available-rooms/",  "AvailableRoomsView",        ["booking.module.view","booking.record.read"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/safe-assign-room/", "SafeAssignRoomView",        ["booking.module.view","booking.record.read","booking.room.assign"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/unassign-room/",    "UnassignRoomView",          ["booking.module.view","booking.record.read","booking.room.assign"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/move-room/",        "MoveRoomView",              ["booking.module.view","booking.record.read","booking.room.assign"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/check-in/",         "BookingCheckInView",        ["booking.module.view","booking.record.read","booking.stay.checkin"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/check-out/",        "BookingCheckOutView",       ["booking.module.view","booking.record.read","booking.stay.checkout"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/send-precheckin-link/", "SendPrecheckinLinkView","booking.module.view + record.read + guest.communicate".split(' + ')),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/send-survey-link/", "SendSurveyLinkView",        ["booking.module.view","booking.record.read","booking.guest.communicate"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/approve/",          "StaffBookingAcceptView",    ["booking.module.view","booking.record.read","booking.override.supervise"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/decline/",          "StaffBookingDeclineView",   ["booking.module.view","booking.record.read","booking.override.supervise"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/overstay/acknowledge/", "OverstayAcknowledgeView", ["booking.module.view","booking.record.read","booking.override.supervise"]),
    ("POST", "/api/staff/hotel/{slug}/room-bookings/{id}/overstay/extend/",  "OverstayExtendView",        ["booking.module.view","booking.record.read","booking.override.supervise"]),
    ("GET",  "/api/staff/hotel/{slug}/room-bookings/{id}/overstay/status/",  "OverstayStatusView",        ["booking.module.view","booking.record.read"]),
]

for m, p, v, caps in ENDPOINT_MAP:
    print(f"  [{m:4}] {p:70s} {v:45s} caps={caps}")


# Simulate each endpoint's decision for each persona
hdr("B.1 Simulate allow/deny for each persona × endpoint")

def _staff_has_all(caps_list, required):
    return all(r in caps_list for r in required)

personas = []
for label, s in targets:
    payload = _resolve_for_staff(s)
    personas.append((label, payload.get('allowed_capabilities', [])))

header = f"{'persona':50s} | " + " | ".join(
    [v[:40] for _, _, v, _ in ENDPOINT_MAP]
)
# Simpler: per persona, list denied endpoints
for label, caps in personas:
    section(f"persona: {label}")
    denied = []
    allowed_mut = []
    for m, p, v, required in ENDPOINT_MAP:
        ok = _staff_has_all(caps, required)
        if m in ("GET","HEAD","OPTIONS"):
            # read gates: CanViewBookings + CanReadBookings have safe_methods_bypass=False
            # — they DO enforce read caps on GET. Mutation gates bypass GET.
            required_gets = [c for c in required if c in ('booking.module.view','booking.record.read')]
            ok = _staff_has_all(caps, required_gets)
        if ok:
            if m != 'GET':
                allowed_mut.append(f"{m} {v}")
        else:
            denied.append(f"{m} {v} (missing: {[c for c in required if c not in caps]})")
    print(f"  allowed mutations: {allowed_mut}")
    print(f"  denied: {denied}")


# ---------------------------------------------------------------------------
# C. Bucket separation
# ---------------------------------------------------------------------------
hdr("C. Bucket separation (synthetic capability sets)")

def _probe(caps_set):
    pol = resolve_module_policy(caps_set)['bookings']
    return pol

scenarios = {
    'read_only':        {BOOKING_MODULE_VIEW, BOOKING_RECORD_READ},
    'operate_only':     {BOOKING_MODULE_VIEW, BOOKING_RECORD_READ,
                         BOOKING_RECORD_UPDATE, BOOKING_RECORD_CANCEL,
                         BOOKING_ROOM_ASSIGN, BOOKING_STAY_CHECKIN, BOOKING_STAY_CHECKOUT,
                         BOOKING_GUEST_COMMUNICATE},
    'supervise_only':   {BOOKING_MODULE_VIEW, BOOKING_RECORD_READ, BOOKING_OVERRIDE_SUPERVISE},
    'manage_only':      {BOOKING_MODULE_VIEW, BOOKING_RECORD_READ, BOOKING_CONFIG_MANAGE},
}
for name, caps in scenarios.items():
    pol = _probe(caps)
    section(name)
    print(json.dumps(pol, indent=2))

# explicit pass/fail:
read_caps = scenarios['read_only']
operate_caps = scenarios['operate_only']
super_caps = scenarios['supervise_only']
manage_caps = scenarios['manage_only']

def _can(caps, action):
    return resolve_module_policy(caps)['bookings']['actions'].get(action, False)

checks = [
    ('read has NO operate actions',      not any(_can(read_caps, a) for a in ('create','update','cancel','assign_room','checkin','checkout','communicate'))),
    ('operate has NO supervise actions', not any(_can(operate_caps, a) for a in ('override_conflicts','force_checkin','force_checkout','resolve_overstay','modify_locked','extend'))),
    ('supervise has NO manage actions',  not _can(super_caps, 'manage_rules')),
    ('manage has NO operate actions',    not any(_can(manage_caps, a) for a in ('create','update','cancel','assign_room','checkin','checkout','communicate'))),
    ('supervise has NO operate actions', not any(_can(super_caps, a) for a in ('create','update','cancel','assign_room','checkin','checkout','communicate'))),
]
for c, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}: {c}")


# ---------------------------------------------------------------------------
# Tier defaults — what does each tier actually get?
# ---------------------------------------------------------------------------
hdr("C.1 Tier default bundles (booking.* only)")
for tier, caps in TIER_DEFAULT_CAPABILITIES.items():
    book = sorted(c for c in caps if c.startswith('booking.'))
    print(f"  tier={tier}: {book}")

hdr("C.2 Role preset bundles (booking.*)")
for role, caps in ROLE_PRESET_CAPABILITIES.items():
    book = sorted(c for c in caps if c.startswith('booking.'))
    print(f"  role={role}: {book}")

hdr("C.3 Department preset bundles (booking.*)")
for dept, caps in DEPARTMENT_PRESET_CAPABILITIES.items():
    book = sorted(c for c in caps if c.startswith('booking.'))
    print(f"  dept={dept}: {book}")


# ---------------------------------------------------------------------------
# D. Domain isolation
# ---------------------------------------------------------------------------
hdr("D. Domain isolation")
section("grep booking.* usage across apps")

import subprocess, re
# Walk apps and count references
import pathlib
root = pathlib.Path(__file__).parent
booking_cap_slugs = [c for c in CANONICAL_CAPABILITIES if c.startswith('booking.')]
hits = defaultdict(list)
for p in root.rglob('*.py'):
    # skip venv
    if 'venv' in p.parts or '__pycache__' in p.parts:
        continue
    try:
        text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for slug in booking_cap_slugs:
        if slug in text:
            hits[slug].append(str(p.relative_to(root)))

for slug, files in sorted(hits.items()):
    print(f"  {slug}: {len(files)} files")
    for f in files[:10]:
        print(f"    - {f}")

section("Restaurant bookings (bookings/views.py) still uses CanManageRestaurantBookings (tier-based)")
print("  -- this is the legacy restaurant domain, outside Phase 6A scope.")
print("  -- Confirm: no room booking BOOKING_* capability referenced in bookings/*.py")
rest = []
for slug in booking_cap_slugs:
    for f in hits.get(slug, []):
        if f.startswith('bookings/') or f.startswith('bookings\\'):
            rest.append((slug, f))
print("  leaks into bookings/:", rest if rest else "NONE")


# ---------------------------------------------------------------------------
# E. Capability distribution checks
# ---------------------------------------------------------------------------
hdr("E. Capability distribution quality")

# Front desk agent: MUST do create, update, cancel, assign_room, checkin,
# checkout, extend, communicate.
fda_caps = resolve_capabilities(
    tier='regular_staff', role_slug='front_desk_agent', department_slug='front_office'
)
print("front_desk_agent(regular_staff, front_office) caps:")
print("  booking.*:", sorted(c for c in fda_caps if c.startswith('booking.')))

fda_pol = resolve_module_policy(fda_caps)['bookings']
print("  rbac.bookings.actions:", fda_pol['actions'])

missing = [a for a, flag in fda_pol['actions'].items() if not flag and a in ('create','update','cancel','assign_room','checkin','checkout','extend','communicate')]
print("  MISSING operate actions for front desk agent:", missing)

# supervisor on staff_admin: operate yes, supervise NO
sup_caps = resolve_capabilities(tier='staff_admin', role_slug=None, department_slug='front_office')
sup_pol = resolve_module_policy(sup_caps)['bookings']
print("\nstaff_admin(+front_office) rbac.bookings.actions:")
print(" ", sup_pol['actions'])

mgr_caps = resolve_capabilities(tier='super_staff_admin', role_slug='front_office_manager', department_slug='front_office')
mgr_pol = resolve_module_policy(mgr_caps)['bookings']
print("\nsuper_staff_admin(+front_office_manager+front_office) rbac.bookings.actions:")
print(" ", mgr_pol['actions'])

print("\nDONE")
