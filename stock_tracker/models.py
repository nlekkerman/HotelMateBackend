# models.py
from django.db import models
from hotel.models import Hotel


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="ingredients"
    )

    class Meta:
        unique_together = ("name", "hotel")

    def __str__(self):
        return f"{self.name} ({self.unit})"


class CocktailRecipe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="cocktails"
    )

    class Meta:
        unique_together = ("name", "hotel")

    def __str__(self):
        return f"{self.name} ({self.hotel.name})"


class RecipeIngredient(models.Model):
    """
    Links a cocktail recipe to its ingredients and quantity per cocktail.
    """
    cocktail = models.ForeignKey(
        CocktailRecipe,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    quantity_per_cocktail = models.FloatField(
        help_text="Quantity required per single cocktail"
    )

    class Meta:
        unique_together = ('cocktail', 'ingredient')

    def __str__(self):
        return (
            f"{self.quantity_per_cocktail} {self.ingredient.unit} of "
            f"{self.ingredient.name} for {self.cocktail.name}"
        )


class CocktailConsumption(models.Model):
    cocktail = models.ForeignKey(
        CocktailRecipe,
        on_delete=models.CASCADE,
        related_name='consumptions'
    )
    quantity_made = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="consumptions"
    )

    def __str__(self):
        date_str = self.timestamp.strftime('%Y-%m-%d')
        return f"{self.quantity_made} x {self.cocktail.name} on {date_str}"

    def total_ingredient_usage(self):
        """
        Returns a dict of {ingredient_name: (total_quantity, unit)}
        """
        usage = {}
        for ri in self.cocktail.ingredients.all():
            total_qty = ri.quantity_per_cocktail * self.quantity_made
            usage[ri.ingredient.name] = (total_qty, ri.ingredient.unit)
        return usage
