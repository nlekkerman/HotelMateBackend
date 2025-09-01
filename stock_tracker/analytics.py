from .models import CocktailConsumption


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
