# Generated migration
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tracker', '0018_ingredient_linked_stock_item_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='subcategory',
            field=models.CharField(
                blank=True,
                choices=[
                    ('SOFT_DRINKS', 'Soft Drinks (Bottled)'),
                    ('SYRUPS', 'Syrups & Flavourings'),
                    ('JUICES', 'Juices & Lemonades'),
                    ('CORDIALS', 'Cordials'),
                    ('BIB', 'Bag-in-Box (18L)'),
                ],
                help_text='Sub-category for Minerals (M) items only',
                max_length=20,
                null=True,
            ),
        ),
    ]
