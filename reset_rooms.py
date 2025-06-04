# reset_rooms.py

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from rooms.models import Room

def reset_all_rooms():
    updated = Room.objects.update(is_occupied=False)
    print(f"{updated} rooms set to is_occupied=False.")

if __name__ == "__main__":
    reset_all_rooms()
