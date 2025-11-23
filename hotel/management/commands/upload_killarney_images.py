"""
Upload images for Hotel Killarney from local files
"""
from django.core.management.base import BaseCommand
from hotel.models import Hotel, Offer, LeisureActivity
from rooms.models import RoomType
import os


class Command(BaseCommand):
    help = 'Upload Hotel Killarney images from local directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--images-dir',
            type=str,
            default=r'issues\documantation',
            help='Directory containing the images'
        )

    def handle(self, *args, **options):
        images_dir = options['images_dir']
        
        # Check if directory exists
        if not os.path.exists(images_dir):
            self.stdout.write(self.style.ERROR(
                f'Directory not found: {images_dir}'
            ))
            return

        # Get Hotel Killarney
        try:
            hotel = Hotel.objects.get(id=2, slug='hotel-killarney')
        except Hotel.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Hotel Killarney (id=2) not found'
            ))
            return

        self.stdout.write(f'Uploading images for: {hotel.name}')

        # 1. Upload hero image
        hero_path = os.path.join(images_dir, 'hero.jpg')
        if os.path.exists(hero_path) and not hotel.hero_image:
            self.stdout.write('Uploading hero image...')
            hotel.hero_image = hero_path
            hotel.save()
            self.stdout.write(self.style.SUCCESS(
                f'✓ Hero image uploaded'
            ))
        elif hotel.hero_image:
            self.stdout.write(self.style.SUCCESS(
                '✓ Hero image already exists'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Hero image not found: {hero_path}'
            ))

        # 2. Upload room type images
        room_images = {
            'Deluxe Double Room': 'bedroom.jpg',
            'Family Suite': 'superior.webp',
            'Executive Suite': 'superior.webp',  # Reuse for now
        }

        for room_name, image_file in room_images.items():
            image_path = os.path.join(images_dir, image_file)
            if os.path.exists(image_path):
                try:
                    room = RoomType.objects.get(hotel=hotel, name=room_name)
                    self.stdout.write(f'Uploading image for {room_name}...')
                    
                    room.photo = image_path
                    room.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ {room_name} image uploaded'
                    ))
                except RoomType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'Room type not found: {room_name}'
                    ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Image not found: {image_path}'
                ))

        # 3. Upload leisure activity image (use laisure.webp for first activity)
        leisure_path = os.path.join(images_dir, 'laisure.webp')
        if os.path.exists(leisure_path):
            activities = LeisureActivity.objects.filter(hotel=hotel)[:3]
            for activity in activities:
                self.stdout.write(f'Uploading image for {activity.name}...')
                
                activity.image = leisure_path
                activity.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ {activity.name} image uploaded'
                ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Leisure image not found: {leisure_path}'
            ))

        # 4. Upload offer images (use bedroom.jpg for offers)
        offer_image_path = os.path.join(images_dir, 'bedroom.jpg')
        if os.path.exists(offer_image_path):
            offers = Offer.objects.filter(hotel=hotel)
            for offer in offers:
                self.stdout.write(f'Uploading image for {offer.title}...')
                
                offer.photo = offer_image_path
                offer.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ {offer.title} image uploaded'
                ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Offer image not found: {offer_image_path}'
            ))

        self.stdout.write(self.style.SUCCESS(
            '\n✅ All images uploaded successfully!'
        ))
