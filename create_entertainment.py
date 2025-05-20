import os
import django
from datetime import date, timedelta

# Set up Django environment if running outside management command
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'porterproject.settings')
django.setup()

from informations.models import KidsEntertainment

# List of sample titles and descriptions for a week
sample_data = [
    ("Magic Show", "An exciting show of tricks and illusions to amaze the kids."),
    ("Arts & Crafts", "Creative time with painting, drawing, and crafts."),
    ("Story Time", "Interactive storytelling session with fairy tales and fables."),
    ("Movie Day", "Watch a family-friendly animated movie with popcorn."),
    ("Treasure Hunt", "A fun treasure hunt adventure around the hotel."),
    ("Puppet Theatre", "A puppet show featuring fun characters and moral lessons."),
    ("Kids Disco", "Music, lights, and dancing for an energetic end to the week."),
]

today = date.today()
for i in range(7):
    event_date = today + timedelta(days=i)
    title, description = sample_data[i]

    entertainment, created = KidsEntertainment.objects.get_or_create(
        date=event_date,
        defaults={
            "title": title,
            "description": description
        }
    )

    # If created and no qr_code_url yet, generate it and save
    if created and not entertainment.qr_code_url:
        # This calls the generate_qr_code method and updates the model instance
        entertainment.qr_code_url = entertainment.generate_qr_code()
        entertainment.save()

        print(f"Created: {entertainment.title} for {event_date} with QR code generated.")
    else:
        print(f"Already exists: {entertainment.title} for {event_date}")
