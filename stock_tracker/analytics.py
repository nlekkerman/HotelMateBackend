from datetime import date, datetime, timedelta
import calendar
from django.db.models import Sum, Q
from django.utils import timezone
from .models import CocktailConsumption, StockItem, StockInventory, StockMovement

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

    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    return start_dt, end_dt

# ----------------------
# INGREDIENT USAGE
# ----------------------
def ingredient_usage(hotel_id=None, period_type=None, reference_date=None):
    usage_totals = {}
    consumptions = CocktailConsumption.objects.all()

    if hotel_id:
        consumptions = consumptions.filter(hotel_id=hotel_id)
    if period_type:
        start_dt, end_dt = get_period_dates(period_type, reference_date)
        consumptions = consumptions.filter(timestamp__gte=start_dt, timestamp__lte=end_dt)

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
# STOCK INVENTORY HELPERS
# ----------------------
def get_inventory_totals(item):
    """Return total storage and bar quantities from StockInventory."""
    inventories = item.inventory_lines.all()
    total_storage = sum(inv.quantity for inv in inventories)
    total_bar = getattr(item, "stock_in_bar", 0)
    return total_storage, total_bar


def get_period_movements(item, start_dt, end_dt):
    """Return stock movements within a period."""
    agg = item.movements.filter(
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
    ).aggregate(
        added=Sum("quantity", filter=Q(direction=StockMovement.IN)),
        moved_to_bar=Sum("quantity", filter=Q(direction=StockMovement.MOVE_TO_BAR)),
        sales=Sum("quantity", filter=Q(direction=StockMovement.SALE)),
        waste=Sum("quantity", filter=Q(direction=StockMovement.WASTE)),
    )
    return {k: agg[k] or 0 for k in ["added", "moved_to_bar", "sales", "waste"]}


# ----------------------
# STOCK SNAPSHOT
# ----------------------
def calculate_item_snapshot(item, start_dt, end_dt):
    # 1️⃣ Baseline from StockInventory (current snapshot)
    current_storage, current_bar = get_inventory_totals(item)

    # 2️⃣ All movements BEFORE the period (to rewind to opening stock)
    prior_movements = item.movements.filter(timestamp__lt=start_dt).aggregate(
        added=Sum("quantity", filter=Q(direction=StockMovement.IN)),
        moved_to_bar=Sum("quantity", filter=Q(direction=StockMovement.MOVE_TO_BAR)),
        sales=Sum("quantity", filter=Q(direction=StockMovement.SALE)),
        waste=Sum("quantity", filter=Q(direction=StockMovement.WASTE)),
    )
    prior_movements = {k: prior_movements[k] or 0 for k in ["added", "moved_to_bar", "sales", "waste"]}

    # 3️⃣ Rewind to opening balances
    opening_storage = current_storage - prior_movements["added"] + prior_movements["moved_to_bar"]
    opening_bar = current_bar - prior_movements["moved_to_bar"] + (prior_movements["sales"] + prior_movements["waste"])

    # 4️⃣ Movements within the period
    movements = get_period_movements(item, start_dt, end_dt)

    # 5️⃣ Closing balances
    closing_storage = opening_storage + movements["added"] - movements["moved_to_bar"]
    closing_bar = opening_bar + movements["moved_to_bar"] - (movements["sales"] + movements["waste"])

    total_closing_stock = closing_storage + closing_bar

    return {
        "item_id": item.id,
        "item_name": item.name,
        "opening_storage": opening_storage,
        "opening_bar": opening_bar,
        **movements,
        "closing_storage": closing_storage,
        "closing_bar": closing_bar,
        "total_closing_stock": total_closing_stock,
    }

# ----------------------
# HOTEL ANALYTICS
# ----------------------
def get_hotel_analytics(hotel_slug, period_type=None, reference_date=None, changed_only=True):
    if period_type:
        start_dt, end_dt = get_period_dates(period_type, reference_date)
    else:
        start_dt = end_dt = timezone.now()

    items = StockItem.objects.filter(hotel__slug=hotel_slug)
    data = [calculate_item_snapshot(item, start_dt, end_dt) for item in items]

    if changed_only:
        data = [d for d in data if any(d[k] > 0 for k in ["added", "moved_to_bar", "sales", "waste"])]
    return data


def get_item_analytics(item, start_dt, end_dt, changed_only=True):
    snapshot = calculate_item_snapshot(item, start_dt, end_dt)
    if changed_only and all(snapshot[k] == 0 for k in ["added", "moved_to_bar", "sales", "waste"]):
        return None
    return snapshot
