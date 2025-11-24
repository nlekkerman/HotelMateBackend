"""
Delete all images from Cloudinary and clear database references
"""
from django.core.management.base import BaseCommand
from hotel.models import Hotel, Offer, LeisureActivity
from rooms.models import RoomType
import cloudinary.uploader


class Command(BaseCommand):
    help = 'Delete all images from Cloudinary and clear database references'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all images',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'This will DELETE all images from Cloudinary and database!'
            ))
            self.stdout.write(self.style.WARNING(
                'Run with --confirm flag to proceed'
            ))
            return

        deleted_count = 0

        # Delete Hotel hero images
        self.stdout.write('Deleting hotel hero images...')
        for hotel in Hotel.objects.all():
            if hotel.hero_image:
                try:
                    # Delete from Cloudinary
                    cloudinary.uploader.destroy(hotel.hero_image.public_id)
                    self.stdout.write(f'  ✓ Deleted from Cloudinary: {hotel.name}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ! Could not delete from Cloudinary: {str(e)}'
                    ))
                
                # Clear database reference
                hotel.hero_image = None
                hotel.save()
                deleted_count += 1
                self.stdout.write(f'  ✓ Cleared DB reference: {hotel.name}')

        # Delete Room Type photos
        self.stdout.write('\nDeleting room type photos...')
        for room in RoomType.objects.all():
            if room.photo:
                try:
                    cloudinary.uploader.destroy(room.photo.public_id)
                    self.stdout.write(f'  ✓ Deleted from Cloudinary: {room.name}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ! Could not delete from Cloudinary: {str(e)}'
                    ))
                
                room.photo = None
                room.save()
                deleted_count += 1
                self.stdout.write(f'  ✓ Cleared DB reference: {room.name}')

        # Delete Offer photos
        self.stdout.write('\nDeleting offer photos...')
        for offer in Offer.objects.all():
            if offer.photo:
                try:
                    cloudinary.uploader.destroy(offer.photo.public_id)
                    self.stdout.write(f'  ✓ Deleted from Cloudinary: {offer.title}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ! Could not delete from Cloudinary: {str(e)}'
                    ))
                
                offer.photo = None
                offer.save()
                deleted_count += 1
                self.stdout.write(f'  ✓ Cleared DB reference: {offer.title}')

        # Delete Activity images
        self.stdout.write('\nDeleting activity images...')
        for activity in LeisureActivity.objects.all():
            if activity.image:
                try:
                    cloudinary.uploader.destroy(activity.image.public_id)
                    self.stdout.write(f'  ✓ Deleted from Cloudinary: {activity.name}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'  ! Could not delete from Cloudinary: {str(e)}'
                    ))
                
                activity.image = None
                activity.save()
                deleted_count += 1
                self.stdout.write(f'  ✓ Cleared DB reference: {activity.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Deleted {deleted_count} images from storage and database'
        ))
