import os, django, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()
from staff.models import Staff
from staff.permissions import resolve_effective_access

print("=== All active staff ===")
for s in Staff.objects.filter(is_active=True).select_related('role','department','user','hotel'):
    r = s.role.slug if s.role else None
    d = s.department.slug if s.department else None
    print(f"user={s.user.username} tier={s.access_level} role={r} dept={d} hotel={s.hotel.slug}")
    p = resolve_effective_access(s.user)
    bc = sorted(c for c in p['allowed_capabilities'] if c.startswith('booking.'))
    print("  booking caps:", bc)
    print("  rbac.bookings:", json.dumps(p['rbac']['bookings'], indent=2))
