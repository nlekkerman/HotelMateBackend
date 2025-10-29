"""Create a test tournament for today starting 19:00 and ending 23:00.

Run with the project virtualenv python, e.g.:
venv/Scripts/python.exe scripts/create_tournament_today_19_23.py

On success prints: CREATED <id>
If hotel not found prints: NO_HOTEL
"""
import os
import django
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.utils.timezone import get_default_timezone

import sys

# Ensure project root is on sys.path so Django settings package can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()



def make_aware(dt):
    tz = get_default_timezone()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone=tz)
    return dt


def main():
    hotel_slug = 'hotel-killarney'
    from hotel.models import Hotel
    from entertainment.models import MemoryGameTournament

    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        print('NO_HOTEL')
        return

    now = timezone.localtime()
    today = now.date()

    start_dt = datetime.combine(today, time(19, 0))
    end_dt = datetime.combine(today, time(23, 0))

    start_dt = make_aware(start_dt)
    end_dt = make_aware(end_dt)

    # Ensure unique slug
    base_slug = f"test-{today.strftime('%Y%m%d')}-19"
    slug = base_slug
    ix = 1
    while MemoryGameTournament.objects.filter(slug=slug).exists():
        ix += 1
        slug = f"{base_slug}-{ix}"

    tournament = MemoryGameTournament.objects.create(
        hotel=hotel,
        name=f"Test Tournament {today} 19:00",
        slug=slug,
        description='Automated test tournament (19:00-23:00)',
        start_date=start_dt,
        end_date=end_dt,
        registration_deadline=start_dt - timedelta(hours=1),
    )

    print(f'CREATED {tournament.id}')


if __name__ == '__main__':
    main()
