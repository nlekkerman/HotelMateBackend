"""
Check for StockSnapshots in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod

snapshots = StockSnapshot.objects.all()
periods = StockPeriod.objects.all().order_by('start_date')

print(f'\n{"="*80}')
print(f'STOCK SNAPSHOTS STATUS')
print(f'{"="*80}\n')

print(f'Total snapshots: {snapshots.count()}')
print(f'Total periods: {periods.count()}\n')

if periods.exists():
    print('Periods with snapshots:')
    print('-' * 80)
    for p in periods:
        snap_count = StockSnapshot.objects.filter(period=p).count()
        status = "✓" if snap_count > 0 else "✗"
        print(f'{status} {p.period_name:<20} ({p.start_date} to {p.end_date}) - {snap_count} snapshots')
    print()
else:
    print('No periods found.\n')

if snapshots.count() > 0:
    print(f'{"="*80}')
    print(f'SNAPSHOT SAMPLE (first 10)')
    print(f'{"="*80}\n')
    
    for snap in snapshots[:10]:
        print(f'{snap.item.sku:<10} {snap.item.name:<40} Period: {snap.period.period_name}')
        print(f'  Closing: {snap.closing_full_units} full, {snap.closing_partial_units} partial')
        print(f'  Value: €{snap.closing_stock_value}\n')

print(f'{"="*80}\n')
