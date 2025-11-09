"""
Fetch and display all stocktakes for a hotel using Django ORM.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from stock_tracker.models import Stocktake


def fetch_stocktakes(hotel_slug=None):
    if hotel_slug:
        hotel = Hotel.objects.filter(slug=hotel_slug).first()
    else:
        hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return
    print(f"Hotel: {hotel.name}")
    stocktakes = Stocktake.objects.filter(hotel=hotel).order_by('-period_start')
    print(f"Total stocktakes: {stocktakes.count()}")
    for st in stocktakes:
        print(f"- ID: {st.id} | Period: {st.period_start} to {st.period_end} | Status: {st.status} | Lines: {st.lines.count()}")

if __name__ == "__main__":
    # Optionally pass hotel slug as argument
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else None
    fetch_stocktakes(slug)
