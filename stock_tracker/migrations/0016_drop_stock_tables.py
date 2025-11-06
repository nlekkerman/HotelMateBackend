# Generated manually to drop old stock tables

from django.db import migrations


def drop_stock_tables(apps, schema_editor):
    """Manually drop all stock-related tables"""
    with schema_editor.connection.cursor() as cursor:
        tables = [
            'stock_tracker_stockperioditem',
            'stock_tracker_stockperiod',
            'stock_tracker_stockmovement',
            'stock_tracker_stockinventory',
            'stock_tracker_stock',
            'stock_tracker_stockitem',
            'stock_tracker_stockitemtype',
            'stock_tracker_stockcategory',
        ]
        for table in tables:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
            except Exception as e:
                print(f"Could not drop {table}: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tracker', '0015_remove_stockinventory_stock_and_more'),
    ]

    operations = [
        migrations.RunPython(drop_stock_tables, migrations.RunPython.noop),
    ]
