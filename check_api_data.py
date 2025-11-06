"""
Script to compare database fields vs API serializer output
Run: python check_api_data.py
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from stock_tracker.stock_serializers import StockItemSerializer


def check_api_data():
    print("=" * 80)
    print("API DATA EXPOSURE CHECK - What Frontend Sees vs Database")
    print("=" * 80)
    
    # Get Dingle Vodka
    try:
        dingle = StockItem.objects.get(sku='S0001')
    except StockItem.DoesNotExist:
        print("❌ Dingle Vodka (S0001) not found")
        return
    
    print(f"\n📦 STOCK ITEM: {dingle.name} (SKU: {dingle.sku})")
    print("=" * 80)
    
    # Show what's in DATABASE
    print("\n🗄️  RAW DATABASE VALUES:")
    print("-" * 80)
    db_fields = {
        'sku': dingle.sku,
        'name': dingle.name,
        'size': dingle.size,
        'size_value': dingle.size_value,
        'size_unit': dingle.size_unit,
        'uom': dingle.uom,
        'base_unit': dingle.base_unit,
        'unit_cost': dingle.unit_cost,
        'cost_per_base': dingle.cost_per_base,
        'case_cost': dingle.case_cost,
        'selling_price': dingle.selling_price,
        'current_qty': dingle.current_qty,
        'par_level': dingle.par_level,
        'serving_size': dingle.serving_size,
        'serving_unit': dingle.serving_unit,
        'menu_price': dingle.menu_price,
        'vendor': dingle.vendor,
        'country': dingle.country,
        'abv_percent': dingle.abv_percent,
        'vintage': dingle.vintage,
        'active': dingle.active,
    }
    
    for field, value in db_fields.items():
        print(f"   {field:20s}: {value}")
    
    # Show calculated properties
    print("\n🧮 CALCULATED PROPERTIES (from @property methods):")
    print("-" * 80)
    calc_fields = {
        'gp_percentage': dingle.gp_percentage,
        'is_below_par': dingle.is_below_par,
        'pour_cost': dingle.pour_cost,
        'pour_cost_percentage': dingle.pour_cost_percentage,
        'profit_per_serving': dingle.profit_per_serving,
        'profit_margin_percentage': dingle.profit_margin_percentage,
    }
    
    for field, value in calc_fields.items():
        print(f"   {field:25s}: {value}")
    
    # Show what API returns
    print("\n🌐 API SERIALIZED OUTPUT (what frontend receives):")
    print("-" * 80)
    serializer = StockItemSerializer(dingle)
    api_data = serializer.data
    
    print(json.dumps(dict(api_data), indent=2, default=str))
    
    # Compare fields
    print("\n" + "=" * 80)
    print("📊 FIELD COMPARISON SUMMARY")
    print("=" * 80)
    
    all_db_fields = set(db_fields.keys()) | set(calc_fields.keys())
    api_fields = set(api_data.keys())
    
    print(f"\n✅ Fields in API: {len(api_fields)}")
    print(f"🗄️  Fields in Database: {len(all_db_fields)}")
    
    # Fields in API but not checked above
    extra_in_api = api_fields - all_db_fields
    if extra_in_api:
        print(f"\n➕ Additional fields in API response:")
        for field in sorted(extra_in_api):
            print(f"   - {field}: {api_data[field]}")
    
    # Check for missing critical data
    print("\n⚠️  MISSING/ZERO VALUES THAT AFFECT CALCULATIONS:")
    print("-" * 80)
    issues = []
    
    if not dingle.size_value or dingle.size_value == 0:
        issues.append("size_value = 0 or None (can't calculate shots per bottle)")
    
    if not dingle.uom or dingle.uom == 0:
        issues.append("uom = 0 or None (can't calculate cost per bottle)")
    
    if dingle.uom and dingle.uom < 1 and dingle.uom != 1:
        issues.append(f"uom = {dingle.uom} (should be >= 1, e.g., 12 bottles per case)")
    
    if not dingle.unit_cost or dingle.unit_cost == 0:
        issues.append("unit_cost = 0 (no pricing data)")
    
    if not dingle.serving_size or dingle.serving_size == 0:
        issues.append("serving_size = 0 (can't calculate pour cost)")
    
    if not dingle.menu_price or dingle.menu_price == 0:
        issues.append("menu_price = 0 (can't calculate GP% or profit)")
    
    if issues:
        for issue in issues:
            print(f"   ❌ {issue}")
    else:
        print("   ✅ All critical fields have values!")
    
    # Show what needs to be set
    print("\n" + "=" * 80)
    print("💡 TO FIX - SET THESE VALUES:")
    print("=" * 80)
    print(f"""
    dingle = StockItem.objects.get(sku='S0001')
    
    # Basic product info
    dingle.size_value = 700  # 70cl = 700ml
    dingle.size_unit = 'ml'
    dingle.uom = 12  # 12 bottles per case
    
    # Pricing
    dingle.unit_cost = 210.00  # £210 per case (12 bottles)
    dingle.case_cost = 210.00  # Same as unit_cost for cases
    
    # Serving info
    dingle.serving_size = 25  # 25ml shot (UK standard)
    dingle.serving_unit = 'ml'
    dingle.menu_price = 6.00  # £6 per shot
    
    # Vendor info (optional)
    dingle.vendor = 'Dingle Distillery'
    dingle.country = 'Ireland'
    dingle.abv_percent = 40.0  # 40% ABV
    
    dingle.save()
    
    # This will auto-calculate:
    # - cost_per_base = £210 ÷ 12 ÷ 700 = £0.025 per ml
    # - pour_cost = 25ml × £0.025 = £0.625 per shot
    # - pour_cost_percentage = (£0.625 ÷ £6.00) × 100 = 10.42%
    # - profit_per_serving = £6.00 - £0.625 = £5.375
    # - profit_margin_percentage = 89.58%
    # - shots_per_bottle = 700ml ÷ 25ml = 28 shots
    """)


if __name__ == "__main__":
    try:
        check_api_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
