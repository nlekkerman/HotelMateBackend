import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel

hotel = Hotel.objects.first()
if hotel:
    print(f"✓ Hotel: {hotel.name}")
    print(f"✓ Has access_config: {hasattr(hotel, 'access_config')}")
    print(f"✓ Guest base path: {hotel.guest_base_path}")
    print(f"✓ Staff base path: {hotel.staff_base_path}")
    print(f"✓ Is active: {hotel.is_active}")
    print(f"✓ Sort order: {hotel.sort_order}")
    print(f"✓ City: {hotel.city or '(empty)'}")
    print(f"✓ Country: {hotel.country or '(empty)'}")
    
    if hasattr(hotel, 'access_config'):
        config = hotel.access_config
        print(f"\n✓ Access Config:")
        print(f"  - Guest portal enabled: {config.guest_portal_enabled}")
        print(f"  - Staff portal enabled: {config.staff_portal_enabled}")
        print(f"  - Requires room PIN: {config.requires_room_pin}")
else:
    print("No hotels in database")
