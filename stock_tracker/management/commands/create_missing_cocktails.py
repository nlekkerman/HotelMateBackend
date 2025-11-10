from django.core.management.base import BaseCommand
from stock_tracker.models import CocktailRecipe, Ingredient, RecipeIngredient
from hotel.models import Hotel
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create missing cocktails with ingredients and prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=int,
            required=True,
            help='Hotel ID to create cocktails for',
        )

    def handle(self, *args, **options):
        hotel_id = options['hotel']
        
        try:
            hotel = Hotel.objects.get(id=hotel_id)
        except Hotel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Hotel with ID {hotel_id} does not exist')
            )
            return

        cocktails_data = [
            {
                "name": "At The Beach",
                "price": 13.50,
                "ingredients": [
                    {"ingredient": "Vodka", "amount": 45, "unit": "ml"},
                    {"ingredient": "Peach Schnapps", "amount": 15, "unit": "ml"},
                    {"ingredient": "Orange Juice", "amount": 60, "unit": "ml"},
                    {"ingredient": "Cranberry Juice", "amount": 60, "unit": "ml"},
                ]
            },
            {
                "name": "Piña Colada",
                "price": 14.00,
                "ingredients": [
                    {"ingredient": "White Rum", "amount": 60, "unit": "ml"},
                    {"ingredient": "Cream of Coconut", "amount": 30, "unit": "ml"},
                    {"ingredient": "Pineapple Juice", "amount": 180, "unit": "ml"},
                ]
            },
            {
                "name": "Strawberry, Elderflower & Pink Gin Lemonade",
                "price": 14.00,
                "ingredients": [
                    {"ingredient": "Pink Gin", "amount": 50, "unit": "ml"},
                    {"ingredient": "Elderflower Liqueur", "amount": 25, "unit": "ml"},
                    {"ingredient": "Strawberry Syrup", "amount": 25, "unit": "ml"},
                    {"ingredient": "Fresh Lemon Juice", "amount": 15, "unit": "ml"},
                    {"ingredient": "Sugar Syrup", "amount": 10, "unit": "ml"},
                    {"ingredient": "Soda Water", "amount": 60, "unit": "ml"},
                ]
            }
        ]

        created_count = 0
        skipped_count = 0

        for cocktail_data in cocktails_data:
            cocktail_name = cocktail_data['name']
            
            # Check if cocktail already exists
            if CocktailRecipe.objects.filter(
                name=cocktail_name,
                hotel=hotel
            ).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Cocktail '{cocktail_name}' already exists, skipping"
                    )
                )
                skipped_count += 1
                continue

            # Create the cocktail
            cocktail = CocktailRecipe.objects.create(
                name=cocktail_name,
                hotel=hotel,
                price=Decimal(str(cocktail_data['price']))
            )

            # Create ingredients and link them
            for ing_data in cocktail_data['ingredients']:
                ingredient_name = ing_data['ingredient']
                amount = ing_data['amount']
                unit = ing_data['unit']

                # Get or create the ingredient
                ingredient, created = Ingredient.objects.get_or_create(
                    name=ingredient_name,
                    hotel=hotel,
                    defaults={'unit': unit}
                )

                # Link ingredient to cocktail
                RecipeIngredient.objects.create(
                    cocktail=cocktail,
                    ingredient=ingredient,
                    quantity_per_cocktail=amount
                )

                if created:
                    self.stdout.write(
                        f"    + Created ingredient: {ingredient_name} ({unit})"
                    )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Created '{cocktail_name}' with price €{cocktail_data['price']} and {len(cocktail_data['ingredients'])} ingredients"
                )
            )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Created {created_count} new cocktails"
            )
        )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ Skipped {skipped_count} existing cocktails"
                )
            )
