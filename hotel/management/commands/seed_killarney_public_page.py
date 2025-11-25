"""
Management command to seed Hotel Killarney (id=2) with public page sections.

Usage:
    python manage.py seed_killarney_public_page

This command is idempotent - it will wipe existing sections and recreate them each time.
"""

from django.core.management.base import BaseCommand
from hotel.models import Hotel, PublicSection, PublicElement, PublicElementItem


class Command(BaseCommand):
    help = 'Seeds Hotel Killarney (id=2) with mock public page sections, elements and items'

    def handle(self, *args, **options):
        # Look up Hotel Killarney
        try:
            hotel = Hotel.objects.get(id=2)
        except Hotel.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Hotel with id=2 does not exist. Please check your database.')
            )
            return

        self.stdout.write(f'Found hotel: {hotel.name}')

        # Delete existing sections (cascades to elements and items)
        deleted_count = PublicSection.objects.filter(hotel=hotel).count()
        PublicSection.objects.filter(hotel=hotel).delete()
        self.stdout.write(f'Deleted {deleted_count} existing section(s)')

        # ============================================================
        # SECTION 1 — Hero
        # ============================================================
        hero_section = PublicSection.objects.create(
            hotel=hotel,
            position=0,
            name="hero",
            is_active=True
        )

        PublicElement.objects.create(
            section=hero_section,
            element_type="hero",
            title="Welcome to Hotel Killarney",
            subtitle="Your perfect stay in the heart of Kerry",
            body="Enjoy comfortable rooms, great food, and family-friendly facilities in one of Ireland's most beautiful regions.",
            image_url="",
            settings={
                "primary_cta_label": "Book Now",
                "primary_cta_url": "/guest/hotels/hotel-killarney/book/",
                "align": "center"
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ Created hero section'))

        # ============================================================
        # SECTION 2 — Rooms List
        # ============================================================
        rooms_section = PublicSection.objects.create(
            hotel=hotel,
            position=1,
            name="rooms",
            is_active=True
        )

        PublicElement.objects.create(
            section=rooms_section,
            element_type="rooms_list",
            title="Our Rooms & Suites",
            subtitle="Find the perfect room for your stay",
            body="",
            image_url="",
            settings={
                "show_price_from": True,
                "show_occupancy": True,
                "columns": 2
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ Created rooms_list section'))

        # ============================================================
        # SECTION 3 — Highlights (cards_list)
        # ============================================================
        highlights_section = PublicSection.objects.create(
            hotel=hotel,
            position=2,
            name="highlights",
            is_active=True
        )

        highlights_element = PublicElement.objects.create(
            section=highlights_section,
            element_type="cards_list",
            title="Why Guests Love Us",
            subtitle="",
            body="",
            image_url="",
            settings={
                "columns": 3
            }
        )

        # Highlights items
        PublicElementItem.objects.create(
            element=highlights_element,
            title="Family Friendly",
            subtitle="Perfect for all ages",
            body="Spacious family rooms, kids' activities, and flexible dining options.",
            image_url="",
            badge="Families",
            cta_label="",
            cta_url="",
            sort_order=0,
            meta={"icon": "family"}
        )

        PublicElementItem.objects.create(
            element=highlights_element,
            title="Great Location",
            subtitle="Killarney & National Park",
            body="Minutes away from Killarney town, lakes, and scenic national park trails.",
            image_url="",
            badge="Location",
            cta_label="",
            cta_url="",
            sort_order=1,
            meta={"icon": "location"}
        )

        PublicElementItem.objects.create(
            element=highlights_element,
            title="Leisure & Relaxation",
            subtitle="Pool, gym and more",
            body="Enjoy full leisure facilities, including swimming pool and fitness center.",
            image_url="",
            badge="Leisure",
            cta_label="",
            cta_url="",
            sort_order=2,
            meta={"icon": "spa"}
        )

        self.stdout.write(self.style.SUCCESS('✓ Created highlights section with 3 items'))

        # ============================================================
        # SECTION 4 — Gallery
        # ============================================================
        gallery_section = PublicSection.objects.create(
            hotel=hotel,
            position=3,
            name="gallery",
            is_active=True
        )

        gallery_element = PublicElement.objects.create(
            section=gallery_section,
            element_type="gallery",
            title="Explore the Hotel",
            subtitle="",
            body="",
            image_url="",
            settings={
                "layout": "grid"
            }
        )

        # Gallery items
        PublicElementItem.objects.create(
            element=gallery_element,
            title="Lobby",
            subtitle="",
            body="",
            image_url="https://via.placeholder.com/800x500?text=Lobby",
            badge="",
            cta_label="",
            cta_url="",
            sort_order=0,
            meta={}
        )

        PublicElementItem.objects.create(
            element=gallery_element,
            title="Restaurant",
            subtitle="",
            body="",
            image_url="https://via.placeholder.com/800x500?text=Restaurant",
            badge="",
            cta_label="",
            cta_url="",
            sort_order=1,
            meta={}
        )

        PublicElementItem.objects.create(
            element=gallery_element,
            title="Pool",
            subtitle="",
            body="",
            image_url="https://via.placeholder.com/800x500?text=Pool",
            badge="",
            cta_label="",
            cta_url="",
            sort_order=2,
            meta={}
        )

        self.stdout.write(self.style.SUCCESS('✓ Created gallery section with 3 items'))

        # ============================================================
        # SECTION 5 — Reviews
        # ============================================================
        reviews_section = PublicSection.objects.create(
            hotel=hotel,
            position=4,
            name="reviews",
            is_active=True
        )

        reviews_element = PublicElement.objects.create(
            section=reviews_section,
            element_type="reviews_list",
            title="What Our Guests Say",
            subtitle="",
            body="",
            image_url="",
            settings={}
        )

        # Review items
        PublicElementItem.objects.create(
            element=reviews_element,
            title="Amazing family break",
            subtitle="Sarah, Dublin",
            body="We loved our stay – staff were friendly, kids had a great time, and the location is perfect.",
            image_url="",
            badge="5★",
            cta_label="",
            cta_url="",
            sort_order=0,
            meta={"rating": 5.0, "source": "Google"}
        )

        PublicElementItem.objects.create(
            element=reviews_element,
            title="Great base for exploring Killarney",
            subtitle="John, London",
            body="Comfortable rooms, good breakfast, and easy access to the park and town.",
            image_url="",
            badge="4.5★",
            cta_label="",
            cta_url="",
            sort_order=1,
            meta={"rating": 4.5, "source": "Booking.com"}
        )

        self.stdout.write(self.style.SUCCESS('✓ Created reviews section with 2 items'))

        # ============================================================
        # SECTION 6 — Contact / Map
        # ============================================================
        contact_section = PublicSection.objects.create(
            hotel=hotel,
            position=5,
            name="contact",
            is_active=True
        )

        PublicElement.objects.create(
            section=contact_section,
            element_type="contact_block",
            title="Contact & Find Us",
            subtitle="",
            body="For any questions about your stay, get in touch or find us on the map below.",
            image_url="",
            settings={
                "show_phone": True,
                "show_email": True,
                "show_address": True
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ Created contact section'))

        # ============================================================
        # Summary
        # ============================================================
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Seeded public sections for {hotel.name} (id={hotel.id})'
            )
        )
        self.stdout.write(f'Total sections created: 6')
        self.stdout.write(f'Total items created: 8')
