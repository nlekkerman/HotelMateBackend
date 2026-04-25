"""
Remove the `operations_admin` role from every hotel.

The slug has been retired from the canonical role catalog
(staff/role_catalog.py::CANONICAL_ROLES) and from the role preset
capability map (staff/capability_catalog.py::ROLE_PRESET_CAPABILITIES).

This data migration:

1. Reassigns every Staff currently pointing at an `operations_admin`
   role to the canonical `hotel_manager` role on the same hotel,
   creating the canonical `hotel_manager` row (under the `management`
   department) when missing.

2. Deletes orphaned `operations_admin` Role rows.

Fallback strategy: Staff are reassigned to `hotel_manager` (the closest
remaining persona that carries the same staff-management /
maintenance-manage / housekeeping-supervise authority via role preset).
If the hotel is missing the `management` department, the staff's role
is set to NULL so the legacy row can be deleted; tier still gates
authority, the resolver simply receives no role preset.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    Department = apps.get_model('staff', 'Department')
    Role = apps.get_model('staff', 'Role')
    Staff = apps.get_model('staff', 'Staff')

    legacy_roles = list(Role.objects.filter(slug='operations_admin'))

    for legacy in legacy_roles:
        affected = Staff.objects.filter(role_id=legacy.id)
        for staff in affected.iterator():
            target = Role.objects.filter(
                hotel_id=staff.hotel_id, slug='hotel_manager',
            ).first()
            if target is None:
                mgmt_dept = Department.objects.filter(
                    hotel_id=staff.hotel_id, slug='management',
                ).first()
                if mgmt_dept is not None:
                    target = Role.objects.create(
                        hotel_id=staff.hotel_id,
                        department=mgmt_dept,
                        slug='hotel_manager',
                        name='Hotel Manager',
                        description='Hotel general manager.',
                    )

            if target is not None:
                Staff.objects.filter(pk=staff.pk).update(role=target)
            else:
                Staff.objects.filter(pk=staff.pk).update(role=None)

    for legacy in Role.objects.filter(slug='operations_admin'):
        if Staff.objects.filter(role_id=legacy.id).exists():
            # Defensive: should not happen after the reassignment loop.
            continue
        legacy.delete()


def backwards(apps, schema_editor):
    # Non-reversible: `operations_admin` is no longer in the canonical
    # role catalog and Role.clean() rejects it. Rollback means restoring
    # from backup.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0027_seed_canonical_roles'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
