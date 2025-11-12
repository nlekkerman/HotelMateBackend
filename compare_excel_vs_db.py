import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot

print("=" * 100)
print("COMPARING EXCEL DATA WITH DATABASE - OCTOBER 2025")
print("=" * 100)

# Excel data (current period = October, previous = September)
excel_data = {
    'D': {  # Draught Beers
        'name': 'Draught Beers',
        'october': Decimal('5311.62'),
        'september': Decimal('5303.15'),
        'variance': Decimal('8.47')
    },
    'B': {  # Bottled Beers
        'name': 'Bottled Beers',
        'october': Decimal('2288.46'),
        'september': Decimal('3079.04'),
        'variance': Decimal('-790.58')
    },
    'S': {  # Spirits
        'name': 'Spirits',
        'october': Decimal('11063.66'),
        'september': Decimal('10406.35'),
        'variance': Decimal('657.30')
    },
    'M': {  # Minerals/Syrups
        'name': 'Minerals/Syrups',
        'october': Decimal('3062.43'),
        'september': Decimal('4185.61'),
        'variance': Decimal('-1123.18')
    },
    'W': {  # Wine
        'name': 'Wine',
        'october': Decimal('5580.35'),
        'september': Decimal('4466.13'),
        'variance': Decimal('1114.21')
    }
}

# Calculate Excel totals
excel_october_total = sum(cat['october'] for cat in excel_data.values())
excel_september_total = sum(cat['september'] for cat in excel_data.values())
excel_variance_total = sum(cat['variance'] for cat in excel_data.values())

print("\n📊 EXCEL DATA:")
print("-" * 100)
print(f"{'Category':<20} {'October (Current)':<20} {'September (Previous)':<20} {'Variance':<15}")
print("-" * 100)
for code, data in excel_data.items():
    print(f"{data['name']:<20} €{data['october']:>12,.2f}     €{data['september']:>12,.2f}     €{data['variance']:>12,.2f}")
print("-" * 100)
print(f"{'TOTAL':<20} €{excel_october_total:>12,.2f}     €{excel_september_total:>12,.2f}     €{excel_variance_total:>12,.2f}")
print("=" * 100)

# Get database data
print("\n🔍 FETCHING DATABASE DATA...")

# Find October and September periods
try:
    october_period = StockPeriod.objects.get(
        hotel_id=2,
        start_date='2025-10-01',
        end_date='2025-10-31'
    )
    print(f"✅ October period found: ID={october_period.id}, {october_period.period_name}")
except StockPeriod.DoesNotExist:
    print("❌ October period NOT FOUND")
    exit(1)

try:
    september_period = StockPeriod.objects.get(
        hotel_id=2,
        start_date='2025-09-01',
        end_date='2025-09-30'
    )
    print(f"✅ September period found: ID={september_period.id}, {september_period.period_name}")
except StockPeriod.DoesNotExist:
    print("❌ September period NOT FOUND")
    exit(1)

# Get snapshots by category
print("\n📦 DATABASE SNAPSHOTS:")
print("-" * 100)
print(f"{'Category':<20} {'October (DB)':<20} {'September (DB)':<20} {'Variance (DB)':<15}")
print("-" * 100)

db_october_total = Decimal('0')
db_september_total = Decimal('0')
db_variance_total = Decimal('0')

for code in ['D', 'B', 'S', 'M', 'W']:
    # October snapshots
    october_snapshots = StockSnapshot.objects.filter(
        period=october_period,
        item__category__code=code
    )
    october_total = sum(
        (s.closing_stock_value for s in october_snapshots),
        Decimal('0')
    )
    
    # September snapshots
    september_snapshots = StockSnapshot.objects.filter(
        period=september_period,
        item__category__code=code
    )
    september_total = sum(
        (s.closing_stock_value for s in september_snapshots),
        Decimal('0')
    )
    
    variance = october_total - september_total
    
    db_october_total += october_total
    db_september_total += september_total
    db_variance_total += variance
    
    category_name = excel_data[code]['name']
    print(f"{category_name:<20} €{october_total:>12,.2f}     €{september_total:>12,.2f}     €{variance:>12,.2f}")

print("-" * 100)
print(f"{'TOTAL':<20} €{db_october_total:>12,.2f}     €{db_september_total:>12,.2f}     €{db_variance_total:>12,.2f}")
print("=" * 100)

# COMPARISON
print("\n🔍 COMPARISON: EXCEL vs DATABASE")
print("=" * 100)
print(f"{'Category':<20} {'Oct Diff':<15} {'Sept Diff':<15} {'Var Diff':<15} {'Status':<10}")
print("-" * 100)

all_match = True
for code in ['D', 'B', 'S', 'M', 'W']:
    excel = excel_data[code]
    
    # Get DB values
    october_snapshots = StockSnapshot.objects.filter(
        period=october_period,
        item__category__code=code
    )
    db_october = sum((s.closing_stock_value for s in october_snapshots), Decimal('0'))
    
    september_snapshots = StockSnapshot.objects.filter(
        period=september_period,
        item__category__code=code
    )
    db_september = sum((s.closing_stock_value for s in september_snapshots), Decimal('0'))
    
    db_variance = db_october - db_september
    
    # Calculate differences
    oct_diff = excel['october'] - db_october
    sept_diff = excel['september'] - db_september
    var_diff = excel['variance'] - db_variance
    
    # Check if match (allow 0.01 difference for rounding)
    oct_match = abs(oct_diff) < Decimal('0.02')
    sept_match = abs(sept_diff) < Decimal('0.02')
    var_match = abs(var_diff) < Decimal('0.02')
    
    status = "✅ MATCH" if (oct_match and sept_match and var_match) else "❌ DIFF"
    
    if status == "❌ DIFF":
        all_match = False
    
    print(f"{excel['name']:<20} €{oct_diff:>10,.2f}   €{sept_diff:>10,.2f}   €{var_diff:>10,.2f}   {status}")

print("-" * 100)

# Total comparison
total_oct_diff = excel_october_total - db_october_total
total_sept_diff = excel_september_total - db_september_total
total_var_diff = excel_variance_total - db_variance_total

total_match = (
    abs(total_oct_diff) < Decimal('0.02') and 
    abs(total_sept_diff) < Decimal('0.02') and 
    abs(total_var_diff) < Decimal('0.02')
)

total_status = "✅ MATCH" if total_match else "❌ DIFF"
print(f"{'TOTAL':<20} €{total_oct_diff:>10,.2f}   €{total_sept_diff:>10,.2f}   €{total_var_diff:>10,.2f}   {total_status}")

print("=" * 100)

if all_match and total_match:
    print("\n✅ SUCCESS: All data matches between Excel and Database!")
else:
    print("\n❌ MISMATCH: Some values differ between Excel and Database")
    print("\nPossible reasons:")
    print("  1. Excel data is rounded differently")
    print("  2. Missing items in database")
    print("  3. Incorrect item categories in database")
    print("  4. Missing snapshots for some items")
    print("  5. Period dates don't match exactly")

print("\n" + "=" * 100)
