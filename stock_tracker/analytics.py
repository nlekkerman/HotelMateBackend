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

def get_opening_stock(item, hotel_slug, start_dt):
    """
    Opening stock = stock quantity at start date
    """
    # Sum all 'in' before start_dt
    added = StockMovement.objects.filter(
        item=item,
        direction=StockMovement.IN,
        timestamp__lt=start_dt
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # Subtract all removals before start_dt
    removed_storage_to_bar = StockMovement.objects.filter(
        item=item,
        direction=StockMovement.MOVE_TO_BAR,
        timestamp__lt=start_dt
    ).aggregate(total=Sum('quantity'))['total'] or 0

    removed_bar_sale = StockMovement.objects.filter(
        item=item,
        direction=StockMovement.SALE,
        timestamp__lt=start_dt
    ).aggregate(total=Sum('quantity'))['total'] or 0

    removed_bar_waste = StockMovement.objects.filter(
        item=item,
        direction=StockMovement.WASTE,
        timestamp__lt=start_dt
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_removed = removed_storage_to_bar + removed_bar_sale + removed_bar_waste

    return added - total_removed

def get_movements(item, start_dt, end_dt):
    """Return total added and removed quantities for an item in the period"""
    agg = StockMovement.objects.filter(
        item=item,
        timestamp__gte=start_dt,
        timestamp__lt=end_dt
    ).aggregate(
        added=Sum('quantity', filter=Q(direction=StockMovement.IN)),
        removed_storage_to_bar=Sum('quantity', filter=Q(direction=StockMovement.MOVE_TO_BAR)),
        removed_bar_sale=Sum('quantity', filter=Q(direction=StockMovement.SALE)),
        removed_bar_waste=Sum('quantity', filter=Q(direction=StockMovement.WASTE))
    )

    total_removed = (
        (agg['removed_storage_to_bar'] or 0) +
        (agg['removed_bar_sale'] or 0) +
        (agg['removed_bar_waste'] or 0)
    )

    return agg['added'] or 0, total_removed

def get_item_analytics(item, hotel_slug, start_dt, end_dt, changed_only=True):
    opening_storage, opening_bar = get_opening_storage_and_bar(item, start_dt)
    movements = get_period_movements(item, start_dt, end_dt)

    closing_storage = opening_storage + movements["added"] - movements["moved_to_bar"]
    closing_bar = opening_bar + movements["moved_to_bar"] - (movements["sales"] + movements["waste"])
    total_closing_stock = closing_storage + closing_bar  # ✅ total hotel stock

    if changed_only and all(v == 0 for v in movements.values()):
        return None

    return {
        "item_id": item.id,
        "item_name": item.name,
        "opening_storage": opening_storage,
        "opening_bar": opening_bar,
        "added": movements["added"],
        "moved_to_bar": movements["moved_to_bar"],
        "sales": movements["sales"],
        "waste": movements["waste"],
        "closing_storage": closing_storage,
        "closing_bar": closing_bar,
        "total_closing_stock": total_closing_stock,  # send total to frontend
    }


def get_hotel_analytics(hotel_slug, start_date, end_date, changed_only=True):
    start_dt, end_dt = parse_dates(start_date, end_date)
    items = StockItem.objects.filter(hotel__slug=hotel_slug)

    data = [get_item_analytics(item, hotel_slug, start_dt, end_dt, changed_only) for item in items]
    return [d for d in data if d is not None]

def get_opening_storage_and_bar(item, start_dt):
    """Return opening storage and bar stock at start_dt."""

    # STORAGE opening
    opening_in = item.movements.filter(
        direction=StockMovement.IN,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    opening_moved_to_bar = item.movements.filter(
        direction=StockMovement.MOVE_TO_BAR,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    opening_storage = opening_in - opening_moved_to_bar

    # BAR opening
    opening_sales = item.movements.filter(
        direction=StockMovement.SALE,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    opening_waste = item.movements.filter(
        direction=StockMovement.WASTE,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    opening_bar = opening_moved_to_bar - (opening_sales + opening_waste)

    return opening_storage, opening_bar


def get_period_movements(item, start_dt, end_dt):
    """Return all movements split by type within the period."""

    agg = item.movements.filter(
        timestamp__gte=start_dt,
        timestamp__lt=end_dt
    ).aggregate(
        added=Sum("quantity", filter=Q(direction=StockMovement.IN)),
        moved_to_bar=Sum("quantity", filter=Q(direction=StockMovement.MOVE_TO_BAR)),
        sales=Sum("quantity", filter=Q(direction=StockMovement.SALE)),
        waste=Sum("quantity", filter=Q(direction=StockMovement.WASTE)),
    )

    return {
        "added": agg["added"] or 0,
        "moved_to_bar": agg["moved_to_bar"] or 0,
        "sales": agg["sales"] or 0,
        "waste": agg["waste"] or 0,
    }


def get_item_analytics(item, hotel_slug, start_dt, end_dt, changed_only=True):
    opening_storage, opening_bar = get_opening_storage_and_bar(item, start_dt)
    movements = get_period_movements(item, start_dt, end_dt)

    closing_storage = opening_storage + movements["added"] - movements["moved_to_bar"]
    closing_bar = opening_bar + movements["moved_to_bar"] - (movements["sales"] + movements["waste"])

    if changed_only and all(v == 0 for v in movements.values()):
        return None

    return {
        "item_id": item.id,
        "item_name": item.name,
        "opening_storage": opening_storage,
        "opening_bar": opening_bar,
        "added": movements["added"],
        "moved_to_bar": movements["moved_to_bar"],
        "sales": movements["sales"],
        "waste": movements["waste"],
        "closing_storage": closing_storage,
        "closing_bar": closing_bar,
        "total_closing_stock": closing_storage + closing_bar,
    }
