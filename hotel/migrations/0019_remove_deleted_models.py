# Generated manually to remove deleted models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0018_remove_hotel_gallery'),
    ]

    operations = [
        # Remove applied_offer foreign key from PricingQuote
        migrations.RemoveField(
            model_name='pricingquote',
            name='applied_offer',
        ),
        
        # Drop HotelPublicSettings model
        migrations.DeleteModel(
            name='HotelPublicSettings',
        ),
        
        # Drop GalleryImage model (must be before Gallery due to FK)
        migrations.DeleteModel(
            name='GalleryImage',
        ),
        
        # Drop Gallery model
        migrations.DeleteModel(
            name='Gallery',
        ),
        
        # Drop Offer model
        migrations.DeleteModel(
            name='Offer',
        ),
        
        # Drop LeisureActivity model
        migrations.DeleteModel(
            name='LeisureActivity',
        ),
    ]
