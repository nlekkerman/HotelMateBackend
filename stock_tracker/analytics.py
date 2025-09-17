from datetime import date, timedelta
import calendar
from django.db.models import Sum, Q
from .models import CocktailConsumption, StockItem, StockMovement


# ----------------------
# PERIOD HELPERS
# ----------------------
def get_period_dates(period_type: str, reference_date=None):
    reference_date = reference_date or date.today()

    if period_type == "week":
        start = reference_date - timedelta(days=reference_date.weekday())
        end = start + timedelta(days=6)
    elif period_type == "month":
        start = reference_date.replace(day=1)
        last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
        end = reference_date.replace(day=last_day)
    elif period_type == "half_year":
        if reference_date.month <= 6:
            start = date(reference_date.year, 1, 1)
            end = date(reference_date.year, 6, 30)
        else:
            start = date(reference_date.year, 7, 1)
            end = date(reference_date.year, 12, 31)
    elif period_type == "year":
        start = date(reference_date.year, 1, 1)
        end = date(reference_date.year, 12, 31)
    else:
        raise ValueError("Unknown period type")

    return start, end


# ----------------------
# INGREDIENT USAGE
# ----------------------
def ingredient_usage(hotel_id=None, period_type=None, reference_date=None):
    """
    Returns total ingredient usage in a period, optionally filtered by hotel.
    """
    usage_totals = {}
    consumptions = CocktailConsumption.objects.all()

    if hotel_id:
        consumptions = consumptions.filter(hotel_id=hotel_id)

    if period_type:
        start_dt, end_dt = get_period_dates(period_type, reference_date)
        # filter by timestamp in period
        consumptions = consumptions.filter(timestamp__date__gte=start_dt, timestamp__date__lte=end_dt)

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
        qty_str = f"{qty:.2f}".lstrip("0").rstrip("0").rstrip(".")
        converted[name] = f"{qty_str} {unit}"
    return converted


# ----------------------
# STOCK ANALYTICS
# ----------------------
def get_opening_storage_and_bar(item, start_dt):
    """Return opening storage and bar stock at the start of a period."""
    opening_in = item.movements.filter(
        direction=StockMovement.IN,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    moved_to_bar = item.movements.filter(
        direction=StockMovement.MOVE_TO_BAR,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    sales = item.movements.filter(
        direction=StockMovement.SALE,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    waste = item.movements.filter(
        direction=StockMovement.WASTE,
        timestamp__lt=start_dt
    ).aggregate(Sum("quantity"))["quantity__sum"] or 0

    opening_storage = opening_in - moved_to_bar
    opening_bar = moved_to_bar - (sales + waste)

    return opening_storage, opening_bar


def get_period_movements(item, start_dt, end_dt):
    """Return all movements split by type within the period."""
    agg = item.movements.filter(
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
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


def get_opening_balances(item, start_dt):
    """Return opening balances before the period (all movements < start_dt)."""
    agg = item.movements.filter(
        timestamp__lt=start_dt
    ).aggregate(
        added=Sum("quantity", filter=Q(direction=StockMovement.IN)),
        moved_to_bar=Sum("quantity", filter=Q(direction=StockMovement.MOVE_TO_BAR)),
        sales=Sum("quantity", filter=Q(direction=StockMovement.SALE)),
        waste=Sum("quantity", filter=Q(direction=StockMovement.WASTE)),
    )

    opening_storage = (agg["added"] or 0) - (agg["moved_to_bar"] or 0)
    opening_bar = (agg["moved_to_bar"] or 0) - ((agg["sales"] or 0) + (agg["waste"] or 0))

    return opening_storage, opening_bar

# ----------------------
# STOCK ANALYTICS
# ----------------------
def calculate_item_snapshot(item, start_dt, end_dt):
    """Calculate full stock snapshot for an item in a given period."""
    opening_storage, opening_bar = get_opening_balances(item, start_dt)
    movements = get_period_movements(item, start_dt, end_dt)

    closing_storage = opening_storage + movements["added"] - movements["moved_to_bar"]
    closing_bar = opening_bar + movements["moved_to_bar"] - (
        movements["sales"] + movements["waste"]
    )

    # 🔍 Debugging
    print(f"Item: {item.name} (ID: {item.id})")
    print("Opening:", opening_storage, opening_bar)
    print("Movements:", movements)
    print("Closing:", closing_storage, closing_bar)
    print("-" * 40)

    return {
        "item_id": item.id,
        "item_name": item.name,
        "opening_storage": opening_storage,
        "opening_bar": opening_bar,
        **movements,
        "closing_storage": closing_storage,
        "closing_bar": closing_bar,
        "total_closing_stock": closing_storage + closing_bar,
    }


def get_hotel_analytics(hotel_slug, period_type=None, reference_date=None, changed_only=True):
    """Return analytics for all items in a hotel for a given period."""
    if period_type:
        start_dt, end_dt = get_period_dates(period_type, reference_date)
    else:
        start_dt = end_dt = None  # fallback

    items = StockItem.objects.filter(hotel__slug=hotel_slug)
    data = [
        calculate_item_snapshot(item, start_dt, end_dt)
        for item in items
    ]

    if changed_only:
        data = [
            d for d in data
            if any(d[k] > 0 for k in ["added", "moved_to_bar", "sales", "waste"])
        ]
    return data


def get_item_analytics(item, start_dt, end_dt, changed_only=True):
    snapshot = calculate_item_snapshot(item, start_dt, end_dt)

    if changed_only and all(
        snapshot[k] == 0 for k in ["added", "moved_to_bar", "sales", "waste"]
    ):
        return None

    return snapshot
