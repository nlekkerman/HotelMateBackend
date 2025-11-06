from .models import CocktailConsumption


def ingredient_usage(hotel_id=None):
    """
    Calculate total ingredient usage from cocktail consumption.
    Returns a dict of {ingredient_name: (total_quantity, unit)}
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
    """
    Convert large quantities to more readable units.
    e.g., 1000 ml -> 1 L, 1000 g -> 1 kg
    """
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
