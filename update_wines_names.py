"""
Update all Wine product names - remove numbers except for minis (1/4, 187ml, 200ml),
expand abbreviations, fix typos, keep O&G as is.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# All wine updates
wine_updates = [
    # Quarter bottles - Keep size indicator
    ("W0040", "Jack Rabbit 1/4"),  # Was "1/4 Jack Rabbit 187Ml"
    
    # 200ml minis - Keep size
    ("W31", "De Faveri Prosecco 200ml"),  # Was "200ml De Faveri Prosecco"
    ("W_MDC_PROSECCO", "MDC Prosecco 200ml"),  # Was "MDC PROSECCO DOC..."
    
    # Alvier - Fix typo
    ("W0039", "Alvier Chardonnay"),  # Was "Alvier Chardonny"
    
    # Chablis
    ("W0019", "Chablis Emeraude"),
    
    # Chateau - All unique
    ("W0025", "Chateau de Domy"),
    ("W0044", "Chateau Haut Baradiou"),
    ("W0018", "Chateau Pascaud"),
    
    # Cheval - Fix typo
    ("W2108", "Cheval Chardonnay"),  # Was "Cheval Chardonny"
    
    # Classic South
    ("W0038", "Classic South Sauvignon Blanc"),
    
    # De La Chevaliere
    ("W0032", "De La Chevaliere Rose"),
    
    # Domaine - Fix typo
    ("W0036", "Domaine Petit Chablis"),
    ("W0028", "Domaine Fleurie"),  # Was "Domiane Fleurie"
    
    # El Somo
    ("W0023", "El Somo Rioja Crianza"),
    
    # Equino
    ("W0027", "Equino Malbec"),
    
    # Fuego
    ("W0043", "Fuego Blanco"),
    
    # La Chevaliere - Fix typo
    ("W0031", "La Chevaliere Chardonnay"),  # Was "La Chevaliere Chardonny"
    
    # Les Jamelles - Expand abbreviation
    ("W0033", "Les Jamelles Sauvignon Blanc"),  # Was "Les Jamelles Sauv-Blanc"
    ("W2102", "Les Petits Jamelles Rose"),
    
    # Les Roche
    ("W1020", "Les Roche Merlot"),
    
    # Marques de Plata - Fix spacing, expand abbreviations
    ("W2589", "Marques de Plata Sauvignon Blanc"),  # Was "MarquesPlata Sauv/Blanc"
    ("W1004", "Marques de Plata Tempranillo Syrah"),  # Was "MarquesPlata Temp/Syrah"
    
    # Moilard
    ("W0024", "Moilard Macon Village"),
    
    # Non-Alcoholic
    ("W_PROSECCO_NA", "Non-Alcoholic Prosecco"),  # Was "No Alcohol Prosecco"
    
    # O&G - Keep as is, add minis 187ml
    ("W_OG_SAUV_187", "O&G Sauvignon Blanc 187ml"),  # Was "O&G SAUVIGNON BLANC 12X187ML"
    ("W_OG_SHIRAZ_187", "O&G Shiraz 187ml"),  # Was "O&G SHIRAZ 12X187ML"
    ("W_OG_SHIRAZ_75", "O&G Shiraz"),  # Was "O&G SHIRAZ 6X75CL"
    
    # Pascaud - Fix name
    ("W_PACSAUD", "Pascaud Bordeaux Superieur"),  # Was "Pacsaud Bordeaux Superior"
    
    # Pannier
    ("W1013", "Pannier"),
    
    # Pazo
    ("W0021", "Pazo Albarino"),
    
    # Pinot Grigio
    ("W_PINOT_SNIPES", "Pinot Grigio Snipes"),
    
    # Pouilly
    ("W0037", "Pouilly Fume Lucy"),  # Was "Pouilly Tume Lucy"
    
    # Primitivo
    ("W45", "Primitivo Giola Colle"),
    
    # Prosecco - Fix typo
    ("W1019", "Prosecco Colli"),  # Was "Prosecco Collie"
    
    # Real Camponia
    ("W2110", "Real Camponia Verdejo"),
    
    # Reina - Keep percentage for clarity
    ("W111", "Reina 5.5"),  # Was "Reina 5.5%"
    
    # Rialto - Remove size
    ("W1", "Rialto Prosecco"),  # Was "Rialto Prosecco 750ML"
    
    # Roquende - Expand abbreviations, fix typo
    ("W0034", "Roquende Cabernet Sauvignon"),  # Was "Roquende Cab-Sauv"
    ("W0041", "Roquende Chardonnay"),  # Was "Roquende Chardonny"
    ("W0042", "Roquende Rose"),
    
    # Santa Ana
    ("W2104", "Santa Ana Malbec"),
    
    # Serra
    ("W0029", "Serra d Conte Castelli"),
    
    # Sonnetti - Fix typo
    ("W0022", "Sonnetti Pinot Grigio"),  # Was "Sonnetti Pinot Grigo"
    
    # Tenuta - Fix apostrophe
    ("W0030", "Tenuta Barbera d'Asti"),  # Was "Tenuta Barbera dAsti DOCG"
]

print("=" * 60)
print("UPDATING ALL WINE NAMES")
print("=" * 60)

success_count = 0
error_count = 0

for sku, new_name in wine_updates:
    try:
        item = StockItem.objects.get(sku=sku)
        old_name = item.name
        item.name = new_name
        item.save()
        print(f"✓ {sku}: '{old_name}' → '{new_name}'")
        success_count += 1
    except StockItem.DoesNotExist:
        print(f"✗ {sku}: NOT FOUND - {new_name}")
        error_count += 1
    except Exception as e:
        print(f"✗ {sku}: ERROR - {e}")
        error_count += 1

print("\n" + "=" * 60)
print(f"COMPLETE: {success_count} updated, {error_count} errors")
print("=" * 60)
