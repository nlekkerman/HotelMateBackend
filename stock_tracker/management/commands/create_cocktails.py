"""
Management command to create cocktail ingredients and recipes.

Usage:
    python manage.py create_cocktails --hotel=<hotel_id_or_slug>

Example:
    python manage.py create_cocktails --hotel=1
    python manage.py create_cocktails --hotel=myhotel
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from stock_tracker.models import Ingredient, CocktailRecipe, RecipeIngredient
from hotel.models import Hotel


class Command(BaseCommand):
    help = 'Create cocktail ingredients and recipes for a hotel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=str,
            required=True,
            help='Hotel ID or slug'
        )

    def handle(self, *args, **options):
        hotel_identifier = options['hotel']
        
        # Get hotel
        try:
            if hotel_identifier.isdigit():
                hotel = Hotel.objects.get(id=int(hotel_identifier))
            else:
                hotel = Hotel.objects.get(slug=hotel_identifier)
        except Hotel.DoesNotExist:
            raise CommandError(f'Hotel "{hotel_identifier}" not found')
        
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Creating cocktails for: {hotel.name}')
        self.stdout.write(f'{"="*60}\n')
        
        # Define all cocktails
        cocktails_data = [
            {
                "name": "Old Fashioned",
                "ingredients": [
                    {"name": "Dingle Whiskey", "amount": "60 ml"},
                    {"name": "Sugar Syrup", "amount": "5 ml"},
                    {"name": "Angostura Bitters", "amount": "2 dashes"},
                    {"name": "Orange Zest", "amount": "1 twist"}
                ],
                "description": "Classic whiskey cocktail built over ice with bitters, sugar, and citrus oils."
            },
            {
                "name": "Negroni",
                "ingredients": [
                    {"name": "Dingle Gin", "amount": "30 ml"},
                    {"name": "Campari", "amount": "30 ml"},
                    {"name": "Sweet Vermouth", "amount": "30 ml"},
                    {"name": "Pineapple Juice", "amount": "15 ml"}
                ],
                "description": "Bittersweet gin aperitivo with vermouth and Campari; menu version adds pineapple."
            },
            {
                "name": "Cosmopolitan",
                "ingredients": [
                    {"name": "Vodka", "amount": "40 ml"},
                    {"name": "Triple Sec", "amount": "15 ml"},
                    {"name": "Lime Juice", "amount": "15 ml"},
                    {"name": "Cranberry Juice", "amount": "30 ml"}
                ],
                "description": "Crisp vodka sour with orange liqueur, cranberry, and fresh lime."
            },
            {
                "name": "The Sloeberry",
                "ingredients": [
                    {"name": "Gin", "amount": "50 ml"},
                    {"name": "Strawberries", "amount": "3 pcs"},
                    {"name": "Fresh Lime Juice", "amount": "20 ml"},
                    {"name": "Soda Water", "amount": "top up"}
                ],
                "description": "Light, fruity gin highball with fresh strawberries and lime."
            },
            {
                "name": "NY Sour",
                "ingredients": [
                    {"name": "US Bourbon", "amount": "50 ml"},
                    {"name": "Disaronno", "amount": "15 ml"},
                    {"name": "Lemon Juice", "amount": "25 ml"},
                    {"name": "Sugar Syrup", "amount": "10 ml"},
                    {"name": "Egg White", "amount": "1"},
                    {"name": "Red Wine Foam", "amount": "10 ml"}
                ],
                "description": "Silky bourbon sour with amaretto and a red-wine foam cap."
            },
            {
                "name": "The Strawberry Tree Spicy Margarita",
                "ingredients": [
                    {"name": "Ghost Tequila", "amount": "45 ml"},
                    {"name": "Triple Sec", "amount": "20 ml"},
                    {"name": "Agave Syrup", "amount": "10 ml"},
                    {"name": "Strawberry Purée", "amount": "20 ml"},
                    {"name": "Lime Juice", "amount": "25 ml"}
                ],
                "description": "Spicy tequila margarita sweetened with agave and fresh strawberry."
            },
            {
                "name": "Passionfruit Martini",
                "ingredients": [
                    {"name": "Absolut Vanilla Vodka", "amount": "40 ml"},
                    {"name": "Passoa", "amount": "20 ml"},
                    {"name": "Passionfruit Purée", "amount": "30 ml"},
                    {"name": "Lime Juice", "amount": "15 ml"}
                ],
                "description": "Tropical, tangy vodka martini with passionfruit and vanilla notes."
            },
            {
                "name": "At the Beach",
                "ingredients": [
                    {"name": "Smirnoff", "amount": "40 ml"},
                    {"name": "Peach Schnapps", "amount": "20 ml"},
                    {"name": "Orange Juice", "amount": "60 ml"},
                    {"name": "Cranberry Juice", "amount": "30 ml"},
                    {"name": "Grenadine", "amount": "5 ml"}
                ],
                "description": "Fruity vodka cooler with peach, orange, cranberry and a grenadine blush."
            },
            {
                "name": "Espresso Martini",
                "ingredients": [
                    {"name": "Absolut Vanilla Vodka", "amount": "45 ml"},
                    {"name": "Kahlua", "amount": "30 ml"},
                    {"name": "Espresso Coffee", "amount": "30 ml"}
                ],
                "description": "Bold coffee cocktail with vanilla vodka and coffee liqueur, shaken frothy."
            },
            {
                "name": "Classic Vodka or Gin Martini",
                "ingredients": [
                    {"name": "Smirnoff or Gordon's Gin", "amount": "60 ml"},
                    {"name": "Vermouth", "amount": "10 ml"},
                    {"name": "Lemon Zest", "amount": "1 twist"},
                    {"name": "Orange Zest", "amount": "1 twist"}
                ],
                "description": "Bone-dry short drink of spirit and vermouth, finished with citrus zest."
            },
            {
                "name": "Pina Colada",
                "ingredients": [
                    {"name": "Bacardi", "amount": "45 ml"},
                    {"name": "Malibu", "amount": "20 ml"},
                    {"name": "Pineapple Juice", "amount": "90 ml"},
                    {"name": "Coconut Milk or Cream", "amount": "30 ml"}
                ],
                "description": "Creamy rum classic with coconut and pineapple."
            },
            {
                "name": "Disaronno Sour",
                "ingredients": [
                    {"name": "Disaronno", "amount": "50 ml"},
                    {"name": "Lemon Juice", "amount": "25 ml"},
                    {"name": "Sugar Syrup", "amount": "10 ml"},
                    {"name": "Egg White", "amount": "1"}
                ],
                "description": "Almond-toned sour, shaken fluffy with citrus and simple syrup."
            },
            {
                "name": "Whiskey Sour",
                "ingredients": [
                    {"name": "Jameson", "amount": "50 ml"},
                    {"name": "Lemon Juice", "amount": "25 ml"},
                    {"name": "Sugar Syrup", "amount": "15 ml"},
                    {"name": "Egg White", "amount": "1"},
                    {"name": "Angostura Bitters", "amount": "2 dashes"}
                ],
                "description": "Irish whiskey sour with bitters and a silky meringue head."
            },
            {
                "name": "Aperol Spritz",
                "ingredients": [
                    {"name": "Aperol", "amount": "60 ml"},
                    {"name": "Prosecco", "amount": "90 ml"},
                    {"name": "Soda Water", "amount": "30 ml"}
                ],
                "description": "Bright, bittersweet spritz with bubbles and a light bitter bite."
            },
            {
                "name": "Campari Spritz",
                "ingredients": [
                    {"name": "Campari", "amount": "60 ml"},
                    {"name": "Prosecco", "amount": "90 ml"},
                    {"name": "Soda Water", "amount": "30 ml"}
                ],
                "description": "Bolder, more bitter spritz built with Campari."
            },
            {
                "name": "Sarti Spritz",
                "ingredients": [
                    {"name": "Sarti", "amount": "60 ml"},
                    {"name": "Prosecco", "amount": "90 ml"},
                    {"name": "Soda Water", "amount": "30 ml"}
                ],
                "description": "House spritz variation using Sarti bitter liqueur."
            },
            {
                "name": "Strawberry Elderflower & Pink Gin Lemonade",
                "ingredients": [
                    {"name": "Pink Gin", "amount": "40 ml"},
                    {"name": "Strawberry Purée", "amount": "30 ml"},
                    {"name": "Elderflower Syrup", "amount": "15 ml"},
                    {"name": "Lemon Juice", "amount": "20 ml"},
                    {"name": "Soda Water", "amount": "top up"}
                ],
                "description": "Refreshing berry-elderflower lemonade built long over ice."
            },
            {
                "name": "Pink Grapefruit & Watermelon Vodka Lemonade",
                "ingredients": [
                    {"name": "Vodka", "amount": "40 ml"},
                    {"name": "Pink Grapefruit Juice", "amount": "60 ml"},
                    {"name": "Watermelon Syrup", "amount": "20 ml"},
                    {"name": "Lemon Juice", "amount": "15 ml"},
                    {"name": "Soda Water", "amount": "top up"}
                ],
                "description": "Citrus-melon lemonade that's bright, sweet-tart and fizzy."
            }
        ]
        
        # Extract all unique ingredients with their units
        ingredient_mapping = self._extract_ingredients(cocktails_data)
        
        with transaction.atomic():
            # Step 1: Create ingredients
            created_ingredients = self._create_ingredients(
                hotel, ingredient_mapping
            )
            
            # Step 2: Create cocktails with recipes
            created_cocktails = self._create_cocktails(
                hotel, cocktails_data, created_ingredients
            )
        
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully created {len(created_ingredients)} '
                f'ingredients and {len(created_cocktails)} cocktails!'
            )
        )
        self.stdout.write(f'{"="*60}\n')
    
    def _extract_ingredients(self, cocktails_data):
        """Extract unique ingredients and determine appropriate units"""
        ingredient_mapping = {}
        
        for cocktail in cocktails_data:
            for ing_data in cocktail['ingredients']:
                name = ing_data['name']
                amount = ing_data['amount']
                
                if name not in ingredient_mapping:
                    # Determine unit from amount string
                    unit = self._determine_unit(amount)
                    ingredient_mapping[name] = unit
        
        return ingredient_mapping
    
    def _determine_unit(self, amount_str):
        """Determine appropriate unit from amount string"""
        amount_lower = amount_str.lower()
        
        if 'ml' in amount_lower:
            return 'ml'
        elif 'dash' in amount_lower:
            return 'dashes'
        elif 'pcs' in amount_lower or 'piece' in amount_lower:
            return 'pieces'
        elif 'twist' in amount_lower:
            return 'twists'
        elif 'top up' in amount_lower:
            return 'top up'
        else:
            return 'unit'
    
    def _parse_amount(self, amount_str):
        """Extract numeric quantity from amount string"""
        import re
        
        # Handle special cases
        if 'top up' in amount_str.lower():
            return 0.0  # Will be topped up, quantity varies
        
        # Extract first number from string
        match = re.search(r'(\d+\.?\d*)', amount_str)
        if match:
            return float(match.group(1))
        
        return 1.0  # Default for things like "1 twist"
    
    def _create_ingredients(self, hotel, ingredient_mapping):
        """Create all ingredient records"""
        self.stdout.write('\n📦 Creating Ingredients...')
        self.stdout.write('-' * 60)
        
        created_ingredients = {}
        
        for name, unit in sorted(ingredient_mapping.items()):
            ingredient, created = Ingredient.objects.get_or_create(
                hotel=hotel,
                name=name,
                defaults={'unit': unit}
            )
            
            created_ingredients[name] = ingredient
            
            status = '✨ Created' if created else '✓ Exists'
            self.stdout.write(
                f'{status}: {name:40s} ({unit})'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {len(created_ingredients)} ingredients ready'
            )
        )
        
        return created_ingredients
    
    def _create_cocktails(self, hotel, cocktails_data, ingredients_dict):
        """Create all cocktail recipes with ingredients"""
        self.stdout.write('\n🍹 Creating Cocktails...')
        self.stdout.write('-' * 60)
        
        created_cocktails = []
        
        for cocktail_data in cocktails_data:
            # Create cocktail
            cocktail, created = CocktailRecipe.objects.get_or_create(
                hotel=hotel,
                name=cocktail_data['name']
            )
            
            created_cocktails.append(cocktail)
            
            status = '✨ Created' if created else '✓ Updated'
            self.stdout.write(f'\n{status}: {cocktail.name}')
            
            # Clear existing ingredients if updating
            if not created:
                cocktail.ingredients.all().delete()
            
            # Add ingredients
            for ing_data in cocktail_data['ingredients']:
                ingredient = ingredients_dict[ing_data['name']]
                quantity = self._parse_amount(ing_data['amount'])
                
                RecipeIngredient.objects.create(
                    cocktail=cocktail,
                    ingredient=ingredient,
                    quantity_per_cocktail=quantity
                )
                
                self.stdout.write(
                    f'  + {quantity:6.1f} {ingredient.unit:10s} '
                    f'{ingredient.name}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {len(created_cocktails)} cocktails created'
            )
        )
        
        return created_cocktails
