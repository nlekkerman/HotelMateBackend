# Generated by Django 5.2.1 on 2025-06-22 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tracker', '0002_stockmovement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockinventory',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='stockitem',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='stockmovement',
            name='quantity',
            field=models.IntegerField(help_text='Amount moved in or out (whole number only)'),
        ),
    ]
