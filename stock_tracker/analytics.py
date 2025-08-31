from datetime import datetime, timedelta
from .models import CocktailConsumption

PERIODS = {
    'day': 1,
    'week': 7,
    'month': 30
}

def ingredient_usage(hotel_id=None, start_date=None, end_date=None):
    """
    Returns total ingredient usage, optionally filtered by hotel and date range.

    Args:
        hotel_id (int, optional): ID of the hotel. If None, include all hotels.
        start_date (datetime, optional)
        end_date (datetime, optional)

    Returns:
        Dict[str, float]: {ingredient_name: total_quantity_used}
    """
    usage_totals = {}
    consumptions = CocktailConsumption.objects.all()

    if hotel_id:
        consumptions = consumptions.filter(hotel_id=hotel_id)
    if start_date:
        consumptions = consumptions.filter(timestamp__gte=start_date)
    if end_date:
        consumptions = consumptions.filter(timestamp__lte=end_date)

    for c in consumptions:
        for ri in c.cocktail.ingredients.all():
            qty = ri.quantity_per_cocktail * c.quantity_made
            usage_totals[ri.ingredient.name] = usage_totals.get(ri.ingredient.name, 0) + qty

    return usage_totals


def ingredient_usage_by_period(period='week', hotel_id=None):
    """
    Returns ingredient usage for a predefined period ('day', 'week', 'month').
    """
    period = period.lower()
    days = PERIODS.get(period)
    if not days:
        raise ValueError("Invalid period. Use 'day', 'week', or 'month'.")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return ingredient_usage(hotel_id=hotel_id, start_date=start_date, end_date=end_date)


def ingredient_usage_custom(start_date, end_date, hotel_id=None):
    """
    Returns ingredient usage for a custom date range.
    """
    if not start_date or not end_date:
        raise ValueError("Both start_date and end_date must be provided for custom range.")
    return ingredient_usage(hotel_id=hotel_id, start_date=start_date, end_date=end_date)
