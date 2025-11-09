# Generated manually on 2025-11-09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tracker', '0002_alter_stockitem_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocktakeline',
            name='manual_purchases_value',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Manual override: Purchase value in period (€)',
                max_digits=15,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='stocktakeline',
            name='manual_sales_profit',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Manual override: Sales profit in period (€)',
                max_digits=15,
                null=True
            ),
        ),
    ]
