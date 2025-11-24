"""
Fix Cloudinary URLs - replace backslashes with forward slashes
"""
from django.core.management.base import BaseCommand
from hotel.models import Hotel, Offer, LeisureActivity
from rooms.models import RoomType


class Command(BaseCommand):
    help = 'Fix Cloudinary URLs by replacing backslashes with forward slashes'

    def handle(self, *args, **options):
        fixed_count = 0

        # Fix Hotel hero images
        for hotel in Hotel.objects.all():
            if hotel.hero_image:
                old_url = str(hotel.hero_image)
                if '\\' in old_url:
                    # Cloudinary stores the path, we need to fix it
                    new_path = old_url.replace('\\', '/')
                    hotel.hero_image = new_path
                    hotel.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Fixed hotel hero: {hotel.name}'
                    ))

        # Fix Room Type photos
        for room in RoomType.objects.all():
            if room.photo:
                old_url = str(room.photo)
                if '\\' in old_url:
                    new_path = old_url.replace('\\', '/')
                    room.photo = new_path
                    room.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Fixed room: {room.name}'
                    ))

        # Fix Offer photos
        for offer in Offer.objects.all():
            if offer.photo:
                old_url = str(offer.photo)
                if '\\' in old_url:
                    new_path = old_url.replace('\\', '/')
                    offer.photo = new_path
                    offer.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Fixed offer: {offer.title}'
                    ))

        # Fix Activity images
        for activity in LeisureActivity.objects.all():
            if activity.image:
                old_url = str(activity.image)
                if '\\' in old_url:
                    new_path = old_url.replace('\\', '/')
                    activity.image = new_path
                    activity.save()
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Fixed activity: {activity.name}'
                    ))

        if fixed_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Fixed {fixed_count} image URLs'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '✅ No URLs needed fixing'
            ))
