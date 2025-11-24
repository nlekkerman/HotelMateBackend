"""
Update all hotels with random hotel types
"""
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel

# Hotel type choices
HOTEL_TYPES = [
    'Resort',
    'SpaHotel',
    'WellnessHotel',
    'FamilyHotel',
    'BusinessHotel',
    'LuxuryHotel',
    'BoutiqueHotel',
    'BudgetHotel',
    'Hostel',
    'Aparthotel',
    'EcoHotel',
    'ConferenceHotel',
    'BeachHotel',
    'MountainHotel',
    'CasinoHotel',
    'GolfHotel',
    'AirportHotel',
    'AdventureHotel',
    'CityHotel',
    'HistoricHotel',
]

# Special assignments
SPECIAL_ASSIGNMENTS = {
    'hotel-killarney': 'FamilyHotel',
}

def update_hotel_types():
    hotels = Hotel.objects.all()
    
    print(f"Updating {hotels.count()} hotels with types...\n")
    
    for hotel in hotels:
        # Check if hotel has special assignment
        if hotel.slug in SPECIAL_ASSIGNMENTS:
            hotel.hotel_type = SPECIAL_ASSIGNMENTS[hotel.slug]
            print(f"✓ {hotel.name} → {hotel.hotel_type} (special assignment)")
        else:
            # Assign random type
            hotel.hotel_type = random.choice(HOTEL_TYPES)
            print(f"✓ {hotel.name} → {hotel.hotel_type}")
        
        hotel.save()
    
    print(f"\n✅ Updated {hotels.count()} hotels")
    
    # Show distribution
    print("\n📊 Type Distribution:")
    type_counts = {}
    for hotel in Hotel.objects.all():
        type_counts[hotel.hotel_type] = type_counts.get(hotel.hotel_type, 0) + 1
    
    for hotel_type, count in sorted(type_counts.items()):
        display_name = dict(Hotel.HOTEL_TYPE_CHOICES).get(hotel_type, hotel_type)
        print(f"  {display_name}: {count}")

if __name__ == '__main__':
    update_hotel_types()
