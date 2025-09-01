from datetime import datetime, timedelta
from django.db.models import Sum, Q

from .models import CocktailConsumption, StockItem, StockInventory, StockMovement



def ingredient_usage(hotel_id=None):
    """
    Returns total ingredient usage, optionally filtered by hotel, with units.
    """
    usage_totals = {}
    consumptions = CocktailConsumption.objects.all()

    if hotel_id:
        consumptions = consumptions.filter(hotel_id=hotel_id)

    for c in consumptions:
        for ri in c.cocktail.ingredients.all():
            qty = ri.quantity_per_cocktail * c.quantity_made
            usage_totals[ri.ingredient.name] = (
                usage_totals.get(ri.ingredient.name, (0, ri.ingredient.unit))[0] + qty,
                ri.ingredient.unit
            )

    return usage_totals

def convert_units(usage: dict) -> dict:
    converted = {}
    for name, (qty, unit) in usage.items():
        if unit == "ml" and qty >= 1000:
            qty /= 1000
            unit = "L"
        elif unit == "g" and qty >= 1000:
            qty /= 1000
            unit = "kg"
        # remove leading zero and trailing .00 if present
        qty_str = f"{qty:.2f}".lstrip("0").rstrip("0").rstrip(".")
        converted[name] = f"{qty_str} {unit}"
    return converted

def parse_dates(start_date, end_date):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    return start_dt, end_dt

def get_opening_stock(item, hotel_slug):
    """Return the stock quantity as of start_date"""
    return StockInventory.objects.filter(
        item=item,
        stock__hotel__slug=hotel_slug
    ).aggregate(total=Sum('quantity'))['total'] or 0

def get_movements(item, start_dt, end_dt):
    """Return total added and removed quantities for an item in the period"""
    agg = StockMovement.objects.filter(
        item=item,
        timestamp__gte=start_dt,
        timestamp__lt=end_dt
    ).aggregate(
        added=Sum('quantity', filter=Q(direction='in')),
        removed=Sum('quantity', filter=Q(direction='out'))
    )
    return agg['added'] or 0, agg['removed'] or 0

def get_item_analytics(item, hotel_slug, start_dt, end_dt, changed_only=True):
    opening_stock = get_opening_stock(item, hotel_slug)
    added, removed = get_movements(item, start_dt, end_dt)
    closing_stock = opening_stock + added - removed

    if changed_only and added == 0 and removed == 0:
        return None

    return {
        "item_id": item.id,
        "item_name": item.name,
        "opening_stock": opening_stock,
        "added": added,
        "removed": removed,
        "closing_stock": closing_stock
    }

def get_hotel_analytics(hotel_slug, start_date, end_date, changed_only=True):
    start_dt, end_dt = parse_dates(start_date, end_date)
    items = StockItem.objects.filter(hotel__slug=hotel_slug)

    data = [get_item_analytics(item, hotel_slug, start_dt, end_dt, changed_only) for item in items]
    return [d for d in data if d is not None]