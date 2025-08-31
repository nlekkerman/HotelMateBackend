#!/usr/bin/env python
"""
Standalone script to create basic cocktail ingredients in Django.
Run with: python populate_ingredients.py
"""

import os
import django
import sys

# --- Configure Django settings ---
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from stock_tracker.models import Ingredient

# --- List of basic cocktail ingredients ---
ingredients = [
    {"name": "White Rum", "unit": "ml"},
    {"name": "Dark Rum", "unit": "ml"},
    {"name": "Vodka", "unit": "ml"},
    {"name": "Gin", "unit": "ml"},
    {"name": "Tequila", "unit": "ml"},
    {"name": "Triple Sec", "unit": "ml"},
    {"name": "Lime Juice", "unit": "ml"},
    {"name": "Lemon Juice", "unit": "ml"},
    {"name": "Simple Syrup", "unit": "ml"},
    {"name": "Mint Leaves", "unit": "pcs"},
    {"name": "Sugar", "unit": "g"},
    {"name": "Soda Water", "unit": "ml"},
    {"name": "Ice Cubes", "unit": "pcs"},
    {"name": "Cranberry Juice", "unit": "ml"},
    {"name": "Orange Juice", "unit": "ml"},
    {"name": "Cola", "unit": "ml"},
]

created_count = 0
for ing in ingredients:
    obj, created = Ingredient.objects.get_or_create(
        name=ing["name"],
        defaults={"unit": ing["unit"]}
    )
    if created:
        created_count += 1
        print(f"Created ingredient: {obj.name} ({obj.unit})")
    else:
        print(f"Ingredient already exists: {obj.name}")

print(f"\nDone! {created_count} new ingredients created.")
