from django.core.management.base import BaseCommand
from stock_tracker.models import CocktailRecipe
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update cocktail prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=int,
            help='Hotel ID to update cocktails for',
        )

    def handle(self, *args, **options):
        hotel_id = options.get('hotel')

        # Cocktail prices data
        cocktail_prices = [
            { "name": "At The Beach", "price": 13.50 },
            { "name": "Espresso Martini", "price": 14.00 },
            { "name": "Classic Vodka or Gin Martini", "price": 14.00 },
            { "name": "Piña Colada", "price": 14.00 },
            { "name": "Disaronno Sour", "price": 14.00 },
            { "name": "Whiskey Sour", "price": 14.00 },
            { "name": "Aperol Spritz", "price": 14.00 },
            { "name": "Campari Spritz", "price": 14.00 },
            { "name": "Sarti Spritz", "price": 14.00 },
            { "name": "Strawberry, Elderflower & Pink Gin Lemonade", "price": 14.00 },
            { "name": "Pink Grapefruit & Watermelon Vodka Lemonade", "price": 13.00 },
            { "name": "Old Fashioned", "price": 14.00 },
            { "name": "Negroni", "price": 14.00 },
            { "name": "Cosmopolitan", "price": 14.00 },
            { "name": "The Sloeberry", "price": 14.00 },
            { "name": "NY Sour", "price": 14.00 },
            { "name": "The Strawberry Tree Spicy Margarita", "price": 14.00 },
            { "name": "Passionfruit Martini", "price": 14.00 }
        ]

        updated_count = 0
        not_found = []
        already_had_price = []

        for cocktail_data in cocktail_prices:
            name = cocktail_data['name']
            price = Decimal(str(cocktail_data['price']))

            # Build query
            query = CocktailRecipe.objects.filter(name=name)
            if hotel_id:
                query = query.filter(hotel_id=hotel_id)

            cocktails = query.all()

            if not cocktails.exists():
                not_found.append(name)
                continue

            for cocktail in cocktails:
                if cocktail.price:
                    already_had_price.append(f"{name} (Hotel: {cocktail.hotel.name})")
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ '{name}' already has price €{cocktail.price} (Hotel: {cocktail.hotel.name})"
                        )
                    )
                else:
                    cocktail.price = price
                    cocktail.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Updated '{name}' with price €{price} (Hotel: {cocktail.hotel.name})"
                        )
                    )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"\n✓ Updated {updated_count} cocktails with prices"))
        
        if already_had_price:
            self.stdout.write(
                self.style.WARNING(f"⚠ {len(already_had_price)} cocktails already had prices (skipped)")
            )
        
        if not_found:
            self.stdout.write(
                self.style.ERROR(f"\n✗ {len(not_found)} cocktails not found:")
            )
            for name in not_found:
                self.stdout.write(self.style.ERROR(f"  - {name}"))
