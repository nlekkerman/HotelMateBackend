# Stock Tracker Implementation Guide

## Overview
This guide provides complete implementation instructions for the Stock Tracker system, covering all models, endpoints, data imports, and workflows.

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Data Models](#data-models)
3. [API Endpoints](#api-endpoints)
4. [Data Import Process](#data-import-process)
5. [Stocktake Workflow](#stocktake-workflow)
6. [Profitability Analysis](#profitability-analysis)
7. [Period Comparison](#period-comparison)
8. [Frontend Integration](#frontend-integration)

---

## System Architecture

### Core Components
- **StockCategory**: Product categories (D, B, S, W, M)
- **StockItem**: Individual products with pricing and inventory
- **StockPeriod**: Time-based periods for comparison
- **StockSnapshot**: Historical stock levels at period end
- **StockMovement**: All inventory transactions
- **Stocktake**: Physical count sessions
- **StocktakeLine**: Individual items in a stocktake
- **Location**: Storage locations (Bar, Cellar, etc.)

---

## Data Models

### 1. StockCategory
**Purpose**: Define product categories based on SKU prefix

```python
Categories:
- D: Draught Beer
- B: Bottled Beer  
- S: Spirits
- W: Wine
- M: Minerals & Syrups
```

**Fields**:
- `code` (PK): Single character (D/B/S/W/M)
- `name`: Display name

**Auto-created**: Categories are created automatically from SKU prefixes

---

### 2. StockItem
**Purpose**: Universal product model for all stock items

**Key Fields**:
```python
# Identification
hotel: ForeignKey
sku: CharField (e.g., "S0045")
name: CharField
category: ForeignKey (auto-set from SKU prefix)

# Size & Packaging
size: CharField (display: "50Lt", "70cl", "Doz")
size_value: DecimalField (numeric: 50, 70, 330)
size_unit: CharField (L, cl, ml, Doz)

# Unit of Measure (UOM) - varies by category:
# D (Draught): pints per keg
# B (Bottled): bottles per case (usually 12)
# S (Spirits): shots per bottle (typically 19.7)
# W (Wine): glasses per bottle
# M (Minerals): varies
uom: DecimalField

# Costing
unit_cost: DecimalField (cost per full unit: keg/case/bottle)

# Current Stock
current_full_units: DecimalField (kegs, cases, bottles)
current_partial_units: DecimalField (pints, loose bottles, % of bottle)

# Selling Prices
menu_price: DecimalField (per serving)
menu_price_large: DecimalField (large serving)
bottle_price: DecimalField (whole bottle)
promo_price: DecimalField (promotional price)

# Flags
available_on_menu: BooleanField
available_by_bottle: BooleanField
active: BooleanField
```

**Calculated Properties**:
```python
@property
def cost_per_serving(self):
    """Cost per serving = unit_cost ÷ uom"""
    return self.unit_cost / self.uom

@property
def total_stock_in_servings(self):
    """
    Convert all stock to servings - UNIFIED FOR ALL CATEGORIES
    
    Formula: (full_units × uom) + (partial_units × uom)
    
    Examples:
    - Draught: (2 kegs × 52.82) + (0.5 kegs × 52.82) = 132.05 pints
    - Bottled: (10 cases × 12) + (0.75 cases × 12) = 129 bottles
    - Spirits: (7 bottles × 20) + (0.70 bottles × 20) = 154 shots
    - Wine: (3 bottles × 5) + (0.25 bottles × 5) = 16.25 glasses
    
    Note: partial_units is ALWAYS a fractional amount (0.70 = 0.70 of a unit)
    NOT a percentage! 0.70 means "0.70 bottles", not "70% full"
    """
    
@property
def total_stock_value(self):
    """Total value at cost"""
    return self.total_stock_in_servings * self.cost_per_serving

@property
def gross_profit_per_serving(self):
    """menu_price - cost_per_serving"""
    
@property
def gross_profit_percentage(self):
    """((menu_price - cost) / menu_price) × 100"""
    
@property
def markup_percentage(self):
    """((menu_price - cost) / cost) × 100"""
    
@property
def pour_cost_percentage(self):
    """(cost / menu_price) × 100"""
```

**Industry Benchmarks**:
- GP% Target: 70-85%
- Pour Cost - Spirits: 15-20%
- Pour Cost - Beer: 20-25%
- Pour Cost - Wine: 25-35%

---

### 3. StockPeriod
**Purpose**: Define time periods for stock tracking and comparison

**Period Types**:
- `WEEKLY`: Week-based periods
- `MONTHLY`: Month-based periods (e.g., October 2025)
- `QUARTERLY`: Quarter-based (Q1, Q2, Q3, Q4)
- `YEARLY`: Annual periods
- `CUSTOM`: Custom date ranges

**Fields**:
```python
hotel: ForeignKey
period_type: CharField (WEEKLY/MONTHLY/QUARTERLY/YEARLY/CUSTOM)
start_date: DateField
end_date: DateField
year: IntegerField
month: IntegerField (1-12, for monthly)
quarter: IntegerField (1-4, for quarterly)
week: IntegerField (1-52, for weekly)
period_name: CharField (e.g., "October 2025")
is_closed: BooleanField
closed_at: DateTimeField
closed_by: ForeignKey(Staff)
```

**Helper Methods**:
```python
# Create monthly period
StockPeriod.create_monthly_period(hotel, year=2025, month=10)

# Create quarterly period
StockPeriod.create_quarterly_period(hotel, year=2025, quarter=4)

# Get previous period
period.get_previous_period()
```

---

### 4. StockSnapshot
**Purpose**: Freeze stock levels at period end for historical comparison

**Fields**:
```python
hotel: ForeignKey
item: ForeignKey(StockItem)
period: ForeignKey(StockPeriod)

# Frozen stock levels
closing_full_units: DecimalField
closing_partial_units: DecimalField

# Frozen costs
unit_cost: DecimalField
cost_per_serving: DecimalField
closing_stock_value: DecimalField

# Frozen prices
menu_price: DecimalField
```

**Calculated Properties**:
```python
@property
def total_servings(self):
    """Calculate total servings from frozen stock"""
```

---

### 5. StockMovement
**Purpose**: Track all inventory transactions

**Movement Types**:
- `PURCHASE`: Deliveries/purchases
- `SALE`: Sales/consumption
- `WASTE`: Breakage/spillage
- `TRANSFER_IN`: Stock transferred in
- `TRANSFER_OUT`: Stock transferred out
- `ADJUSTMENT`: Stocktake adjustments

**Fields**:
```python
hotel: ForeignKey
item: ForeignKey(StockItem)
period: ForeignKey(StockPeriod)
movement_type: CharField
quantity: DecimalField (in servings)
unit_cost: DecimalField
reference: CharField (invoice number, etc.)
notes: TextField
staff: ForeignKey(Staff)
timestamp: DateTimeField
```

**Auto-Updates Stock**:
- PURCHASE/TRANSFER_IN: Adds to `current_partial_units`
- SALE/WASTE/TRANSFER_OUT: Subtracts from `current_partial_units`
- ADJUSTMENT: Modifies `current_partial_units`

---

### 6. Stocktake
**Purpose**: Physical inventory counting session

**Status**:
- `DRAFT`: In progress, can be edited
- `APPROVED`: Locked, adjustments created

**Fields**:
```python
hotel: ForeignKey
period_start: DateField
period_end: DateField
status: CharField (DRAFT/APPROVED)
created_at: DateTimeField
approved_at: DateTimeField
approved_by: ForeignKey(Staff)
notes: TextField
```

**Properties**:
```python
@property
def is_locked(self):
    """Returns True if status == APPROVED"""
```

---

### 7. StocktakeLine
**Purpose**: Individual item count within a stocktake

**Fields**:
```python
stocktake: ForeignKey(Stocktake)
item: ForeignKey(StockItem)

# Opening balance (frozen)
opening_qty: DecimalField (in base units/servings)

# Period movements (calculated from StockMovement)
purchases: DecimalField
sales: DecimalField
waste: DecimalField
transfers_in: DecimalField
transfers_out: DecimalField
adjustments: DecimalField

# Physical count (user input)
counted_full_units: DecimalField
counted_partial_units: DecimalField

# Valuation
valuation_cost: DecimalField (frozen cost for this count)
```

**Calculated Properties**:
```python
@property
def counted_qty(self):
    """(full_units × UOM) + partial_units"""
    
@property
def expected_qty(self):
    """opening + purchases + transfers_in - sales - waste - transfers_out + adjustments"""
    
@property
def variance_qty(self):
    """counted - expected (+ surplus, - shortage)"""
    
@property
def expected_value(self):
    """expected_qty × valuation_cost"""
    
@property
def counted_value(self):
    """counted_qty × valuation_cost"""
    
@property
def variance_value(self):
    """counted_value - expected_value"""
```

---

### 8. Location
**Purpose**: Physical storage locations

**Fields**:
```python
hotel: ForeignKey
name: CharField (e.g., "Bar Storage", "Cellar A-12")
active: BooleanField
```

---

## API Endpoints

### Base URL Pattern
```
/api/hotels/{hotel_identifier}/stock/
```

### 1. Stock Categories
```
GET /api/hotels/{hotel_identifier}/stock/categories/
GET /api/hotels/{hotel_identifier}/stock/categories/{id}/
GET /api/hotels/{hotel_identifier}/stock/categories/{id}/items/
```

**Response Example**:
```json
{
  "code": "S",
  "name": "Spirits",
  "item_count": 145
}
```

---

### 2. Stock Items
```
GET    /api/hotels/{hotel_identifier}/stock/items/
POST   /api/hotels/{hotel_identifier}/stock/items/
GET    /api/hotels/{hotel_identifier}/stock/items/{id}/
PUT    /api/hotels/{hotel_identifier}/stock/items/{id}/
PATCH  /api/hotels/{hotel_identifier}/stock/items/{id}/
DELETE /api/hotels/{hotel_identifier}/stock/items/{id}/

# Custom actions:
GET /api/hotels/{hotel_identifier}/stock/items/profitability/
GET /api/hotels/{hotel_identifier}/stock/items/profitability/?category=S
GET /api/hotels/{hotel_identifier}/stock/items/low_stock/
GET /api/hotels/{hotel_identifier}/stock/items/{id}/history/
```

**Response Example**:
```json
{
  "id": 1,
  "sku": "S0045",
  "name": "Bacardi 1ltr",
  "category": "S",
  "category_code": "S",
  "category_name": "Spirits",
  "size": "1 Lt",
  "size_value": "1.0",
  "size_unit": "L",
  "uom": "28.2",
  "unit_cost": "24.82",
  "current_full_units": "7.00",
  "current_partial_units": "0.05",
  "menu_price": "5.50",
  "menu_price_large": "9.00",
  "bottle_price": "120.00",
  "available_on_menu": true,
  "available_by_bottle": true,
  "total_stock_in_servings": "197.45",
  "total_stock_value": "174.02",
  "cost_per_serving": "0.88",
  "gross_profit_per_serving": "4.62",
  "gross_profit_percentage": "84.00",
  "markup_percentage": "525.00",
  "pour_cost_percentage": "16.00"
}
```

---

### 3. Stock Periods
```
GET    /api/hotels/{hotel_identifier}/stock/periods/
POST   /api/hotels/{hotel_identifier}/stock/periods/
GET    /api/hotels/{hotel_identifier}/stock/periods/{id}/
PUT    /api/hotels/{hotel_identifier}/stock/periods/{id}/
DELETE /api/hotels/{hotel_identifier}/stock/periods/{id}/

# Custom actions:
GET /api/hotels/{hotel_identifier}/stock/periods/{id}/snapshots/
GET /api/hotels/{hotel_identifier}/stock/periods/{id}/snapshots/?category=S
GET /api/hotels/{hotel_identifier}/stock/periods/compare/?period1={id1}&period2={id2}
```

**List Response** (simple):
```json
{
  "id": 1,
  "period_type": "MONTHLY",
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "year": 2025,
  "month": 10,
  "period_name": "October 2025",
  "is_closed": true
}
```

**Detail Response** (with snapshots):
```json
{
  "id": 1,
  "period_name": "October 2025",
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "is_closed": true,
  "total_items": 145,
  "total_value": "45876.32",
  "snapshots": [
    {
      "id": 1,
      "item": {
        "id": 1,
        "sku": "S0045",
        "name": "Bacardi 1ltr",
        "category": "S",
        "size": "1 Lt",
        "unit_cost": "24.82",
        "menu_price": "5.50"
      },
      "closing_full_units": "7.00",
      "closing_partial_units": "0.05",
      "total_servings": "197.45",
      "closing_stock_value": "174.02",
      "gp_percentage": "84.00",
      "markup_percentage": "525.00",
      "pour_cost_percentage": "16.00"
    }
  ]
}
```

**Period Comparison**:
```json
{
  "period1": {
    "id": 1,
    "period_name": "September 2025"
  },
  "period2": {
    "id": 2,
    "period_name": "October 2025"
  },
  "comparison": [
    {
      "item_id": 1,
      "sku": "S0045",
      "name": "Bacardi 1ltr",
      "category": "S",
      "period1": {
        "period_name": "September 2025",
        "closing_stock": 150.00,
        "servings": 170.25
      },
      "period2": {
        "period_name": "October 2025",
        "closing_stock": 174.02,
        "servings": 197.45
      },
      "change": {
        "value": 24.02,
        "servings": 27.20,
        "percentage": 16.01
      }
    }
  ]
}
```

---

### 4. Stock Movements
```
GET  /api/hotels/{hotel_identifier}/stock/movements/
POST /api/hotels/{hotel_identifier}/stock/movements/
GET  /api/hotels/{hotel_identifier}/stock/movements/{id}/
```

**Create Movement**:
```json
POST /api/hotels/{hotel_identifier}/stock/movements/

{
  "item": 1,
  "movement_type": "PURCHASE",
  "quantity": 28.2,
  "unit_cost": 0.88,
  "reference": "INV-2025-001",
  "notes": "Weekly delivery"
}
```

**Response**:
```json
{
  "id": 1,
  "item": 1,
  "item_sku": "S0045",
  "item_name": "Bacardi 1ltr",
  "period": 1,
  "movement_type": "PURCHASE",
  "quantity": "28.2",
  "unit_cost": "0.88",
  "reference": "INV-2025-001",
  "notes": "Weekly delivery",
  "staff": 1,
  "staff_name": "John Doe",
  "timestamp": "2025-10-15T14:30:00Z"
}
```

---

### 5. Stocktakes
```
GET  /api/hotels/{hotel_identifier}/stock/stocktakes/
POST /api/hotels/{hotel_identifier}/stock/stocktakes/
GET  /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/
PUT  /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/

# Custom actions:
POST /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/populate/
POST /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/approve/
GET  /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/category_totals/
```

**Create Stocktake**:
```json
POST /api/hotels/{hotel_identifier}/stock/stocktakes/

{
  "period_start": "2025-10-01",
  "period_end": "2025-10-31",
  "notes": "Monthly stocktake for October"
}
```

**Populate Stocktake** (generates lines):
```json
POST /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/populate/

Response:
{
  "message": "Created 145 stocktake lines",
  "lines_created": 145
}
```

**Approve Stocktake** (creates adjustments):
```json
POST /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/approve/

Response:
{
  "message": "Stocktake approved",
  "adjustments_created": 23
}
```

**Category Totals**:
```json
GET /api/hotels/{hotel_identifier}/stock/stocktakes/{id}/category_totals/

Response:
[
  {
    "category": "S",
    "category_name": "Spirits",
    "total_expected_value": 12500.00,
    "total_counted_value": 12350.00,
    "total_variance_value": -150.00,
    "item_count": 85
  }
]
```

---

### 6. Stocktake Lines
```
GET   /api/hotels/{hotel_identifier}/stock/stocktake-lines/
GET   /api/hotels/{hotel_identifier}/stock/stocktake-lines/{id}/
PATCH /api/hotels/{hotel_identifier}/stock/stocktake-lines/{id}/
```

**Update Line** (user inputs count):
```json
PATCH /api/hotels/{hotel_identifier}/stock/stocktake-lines/{id}/

{
  "counted_full_units": "7.00",
  "counted_partial_units": "0.05"
}
```

**Response**:
```json
{
  "id": 1,
  "stocktake": 1,
  "item": 1,
  "item_sku": "S0045",
  "item_name": "Bacardi 1ltr",
  "category_code": "S",
  "category_name": "Spirits",
  "opening_qty": "170.25",
  "purchases": "56.40",
  "sales": "85.20",
  "waste": "2.10",
  "transfers_in": "0.00",
  "transfers_out": "0.00",
  "adjustments": "0.00",
  "counted_full_units": "7.00",
  "counted_partial_units": "0.05",
  "counted_qty": "197.45",
  "expected_qty": "139.35",
  "variance_qty": "58.10",
  "valuation_cost": "0.88",
  "expected_value": "122.63",
  "counted_value": "173.76",
  "variance_value": "51.13"
}
```

---

### 7. Locations
```
GET    /api/hotels/{hotel_identifier}/stock/locations/
POST   /api/hotels/{hotel_identifier}/stock/locations/
GET    /api/hotels/{hotel_identifier}/stock/locations/{id}/
PUT    /api/hotels/{hotel_identifier}/stock/locations/{id}/
DELETE /api/hotels/{hotel_identifier}/stock/locations/{id}/
```

---

## Data Import Process

### Importing from JSON (Spirits Example)

**JSON Structure**:
```json
[
  {
    "sku": "S0045",
    "name": "Bacardi 1ltr",
    "size": "1 Lt",
    "uom": "28.2",
    "cost_price": "24.82",
    "closing_stock_bottles": "7.00",
    "closing_stock_individuals": "0.05",
    "stock_at_cost": "174.98"
  }
]
```

**Import Script Template**:
```python
import json
from decimal import Decimal
from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel

def import_spirits_data(hotel_id, json_file_path):
    """
    Import spirits data from JSON file
    """
    hotel = Hotel.objects.get(id=hotel_id)
    
    # Ensure Spirits category exists
    category, _ = StockCategory.objects.get_or_create(
        code='S',
        defaults={'name': 'Spirits'}
    )
    
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    created_count = 0
    updated_count = 0
    
    for item_data in data:
        # Skip items without SKU
        if not item_data.get('sku'):
            continue
        
        # Parse size (e.g., "1 Lt" -> 1.0, "L")
        size = item_data.get('size', '')
        size_value, size_unit = parse_size(size)
        
        # Get or create item
        item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=item_data['sku'],
            defaults={
                'name': item_data['name'],
                'category': category,
                'size': size,
                'size_value': Decimal(str(size_value)),
                'size_unit': size_unit,
                'uom': Decimal(item_data['uom']),
                'unit_cost': Decimal(item_data['cost_price']),
                'current_full_units': Decimal(
                    item_data.get('closing_stock_bottles', '0.00')
                ),
                'current_partial_units': Decimal(
                    item_data.get('closing_stock_individuals', '0.00')
                ),
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return created_count, updated_count

def parse_size(size_str):
    """
    Parse size string to value and unit
    Examples:
    "1 Lt" -> (1.0, "L")
    "70cl" -> (70, "cl")
    "330ml" -> (330, "ml")
    """
    import re
    match = re.match(r'([\d.]+)\s*([a-zA-Z]+)', size_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        # Normalize units
        if unit.lower() == 'lt':
            unit = 'L'
        return value, unit
    return 0, ''

# Usage:
# python manage.py shell
# >>> from scripts.import_spirits import import_spirits_data
# >>> created, updated = import_spirits_data(1, 'docs/spirits.json')
# >>> print(f"Created: {created}, Updated: {updated}")
```

**Django Management Command**:
```python
# Create: stock_tracker/management/commands/import_stock_data.py

from django.core.management.base import BaseCommand
from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel
import json
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import stock data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('hotel_id', type=int)
        parser.add_argument('category', type=str, choices=['spirits', 'beers', 'wines', 'minerals'])
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        hotel_id = options['hotel_id']
        category_type = options['category']
        file_path = options['file_path']
        
        # Map category types to codes
        category_map = {
            'spirits': ('S', 'Spirits'),
            'beers': ('B', 'Bottled Beer'),
            'wines': ('W', 'Wine'),
            'minerals': ('M', 'Minerals & Syrups')
        }
        
        code, name = category_map[category_type]
        
        hotel = Hotel.objects.get(id=hotel_id)
        category, _ = StockCategory.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        created = 0
        updated = 0
        
        for item_data in data:
            if not item_data.get('sku'):
                continue
            
            item, is_new = StockItem.objects.update_or_create(
                hotel=hotel,
                sku=item_data['sku'],
                defaults={
                    'name': item_data['name'],
                    'category': category,
                    'size': item_data.get('size', ''),
                    'uom': Decimal(item_data.get('uom', '1.0')),
                    'unit_cost': Decimal(item_data.get('cost_price', '0.00')),
                    'current_full_units': Decimal(
                        item_data.get('closing_stock_bottles', '0.00')
                    ),
                    'current_partial_units': Decimal(
                        item_data.get('closing_stock_individuals', '0.00')
                    ),
                }
            )
            
            if is_new:
                created += 1
            else:
                updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created: {created}, Updated: {updated}'
            )
        )

# Usage:
# python manage.py import_stock_data 1 spirits docs/spirits.json
```

---

## Stocktake Workflow

### Step-by-Step Process

#### 1. Create Stocktake
```bash
POST /api/hotels/demo-hotel/stock/stocktakes/
{
  "period_start": "2025-10-01",
  "period_end": "2025-10-31",
  "notes": "Monthly stocktake"
}
```

#### 2. Populate Lines
```bash
POST /api/hotels/demo-hotel/stock/stocktakes/1/populate/
```

This automatically:
- Gets opening stock from previous period's closing snapshot (or current stock if no previous period)
- Calculates all movements during the period:
  - Purchases from `PURCHASE` movements
  - Sales from `SALE` movements
  - Waste from `WASTE` movements
  - Transfers from `TRANSFER_IN`/`TRANSFER_OUT` movements
  - Prior adjustments from `ADJUSTMENT` movements
- Freezes valuation cost
- Creates a line for each active stock item

#### 3. Physical Count
Staff counts inventory and updates each line:

```bash
PATCH /api/hotels/demo-hotel/stock/stocktake-lines/1/
{
  "counted_full_units": "7.00",
  "counted_partial_units": "0.05"
}
```

Repeat for all items.

#### 4. Review Variances
```bash
GET /api/hotels/demo-hotel/stock/stocktakes/1/category_totals/
```

Review variances by category to identify:
- Large discrepancies
- Categories with consistent shortages
- Potential theft or spillage issues

#### 5. Approve Stocktake
```bash
POST /api/hotels/demo-hotel/stock/stocktakes/1/approve/
```

This automatically:
- Changes status to `APPROVED`
- Locks the stocktake (cannot edit)
- Creates `ADJUSTMENT` StockMovements for all variances
- Updates `current_partial_units` for all items

---

## Profitability Analysis

### Get All Items with Profitability
```bash
GET /api/hotels/demo-hotel/stock/items/profitability/
```

**Response**:
```json
[
  {
    "id": 1,
    "sku": "S0045",
    "name": "Bacardi 1ltr",
    "category": "S",
    "unit_cost": 24.82,
    "menu_price": 5.50,
    "cost_per_serving": 0.88,
    "gross_profit": 4.62,
    "gross_profit_percentage": 84.00,
    "markup_percentage": 525.00,
    "pour_cost_percentage": 16.00,
    "current_stock_value": 174.02
  }
]
```

### Filter by Category
```bash
GET /api/hotels/demo-hotel/stock/items/profitability/?category=S
```

### Analysis Metrics

**Gross Profit %**: `((menu_price - cost) / menu_price) × 100`
- **Target**: 70-85% for bars
- **Low GP%** (<70%): Consider price increase
- **High GP%** (>85%): Excellent margins

**Markup %**: `((menu_price - cost) / cost) × 100`
- Shows how many times you mark up cost
- Industry standard: 300-500%

**Pour Cost %**: `(cost / menu_price) × 100`
- **Spirits target**: 15-20%
- **Beer target**: 20-25%
- **Wine target**: 25-35%
- **High pour cost**: Price too low or cost too high

---

## Period Comparison

### Compare Two Periods
```bash
GET /api/hotels/demo-hotel/stock/periods/compare/?period1=1&period2=2
```

**Use Cases**:
- Month-over-month comparison
- Seasonal trends
- Inventory turnover analysis
- Cost tracking

**Key Metrics**:
- Stock value change
- Servings change
- Percentage change
- Category-level changes

---

## Frontend Integration

### Dashboard Overview

**Key Displays**:
1. **Current Stock Value**: Sum of `total_stock_value` across all items
2. **Low Stock Alerts**: Items with `current_full_units <= 2`
3. **Top Profit Items**: Sorted by `gross_profit_percentage`
4. **Category Breakdown**: Stock value by category

### Stocktake UI Flow

**Screen 1: Stocktake List**
```
GET /api/hotels/{hotel}/stock/stocktakes/
Display: period_start, period_end, status, total_lines
Actions: Create New, View Details
```

**Screen 2: Stocktake Detail**
```
GET /api/hotels/{hotel}/stock/stocktakes/{id}/
Display: All lines grouped by category
For each line: item name, expected_qty, variance_qty
Input: counted_full_units, counted_partial_units
Actions: Save, Approve (if all counted)
```

**Screen 3: Category Totals**
```
GET /api/hotels/{hotel}/stock/stocktakes/{id}/category_totals/
Display: Variance summary by category
Highlight: Large variances
```

### Period Comparison UI

**Screen: Period Compare**
```
Select Period 1: Dropdown (list periods)
Select Period 2: Dropdown (list periods)
Display: Side-by-side comparison table
Columns: Item, Period1 Value, Period2 Value, Change €, Change %
Filters: By category
Sort: By change % (descending/ascending)
```

---

## Best Practices

### 1. Data Entry
- Always use consistent UOM values
- Verify unit costs regularly
- Keep menu prices updated
- Flag inactive items instead of deleting

### 2. Stocktakes
- Schedule regular stocktakes (weekly/monthly)
- Count during quiet periods
- Have 2 people count separately
- Investigate variances >5%

### 3. Movements
- Record all movements promptly
- Use references (invoice numbers)
- Track waste separately from sales
- Review movement patterns weekly

### 4. Pricing
- Review GP% monthly
- Adjust prices based on cost changes
- Consider competitor pricing
- Use promo_price for special events

### 5. Analysis
- Monitor pour cost percentages
- Track category trends
- Identify slow-moving items
- Review profitability monthly

---

## Troubleshooting

### Issue: Incorrect Stock Levels
**Solution**: Create ADJUSTMENT movement with correct quantity

### Issue: Stocktake Won't Approve
**Check**:
- All lines have counted values
- Stocktake is not already approved
- No validation errors

### Issue: Negative Stock
**Cause**: Sales/waste recorded without sufficient stock
**Solution**: Review movements, create PURCHASE adjustment

### Issue: Profitability Looks Wrong
**Check**:
- `unit_cost` is correct
- `uom` matches product type
- `menu_price` is current
- Using correct serving size

---

## Quick Reference

### Category Codes
- **D**: Draught Beer (kegs, pints)
- **B**: Bottled Beer (cases, bottles)
- **S**: Spirits (bottles, shots)
- **W**: Wine (bottles, glasses)
- **M**: Minerals & Syrups (varies)

### Movement Types
- **PURCHASE**: Stock coming in
- **SALE**: Stock going out
- **WASTE**: Breakage/spillage
- **TRANSFER_IN**: From other location
- **TRANSFER_OUT**: To other location
- **ADJUSTMENT**: Stocktake correction

### Key Formulas
```
Cost per Serving = unit_cost ÷ uom
GP% = ((menu_price - cost_per_serving) / menu_price) × 100
Markup% = ((menu_price - cost_per_serving) / cost_per_serving) × 100
Pour Cost% = (cost_per_serving / menu_price) × 100
```

---

## Support & Maintenance

### Regular Tasks
- [ ] Weekly: Review low stock items
- [ ] Weekly: Enter deliveries (PURCHASE movements)
- [ ] Weekly: Record waste (WASTE movements)
- [ ] Monthly: Complete stocktake
- [ ] Monthly: Review profitability
- [ ] Monthly: Compare with previous period
- [ ] Quarterly: Review pricing strategy
- [ ] Annually: Archive old periods

### Data Backup
- Stocktakes should be approved before month-end
- Export period snapshots for records
- Keep invoice copies with movement references

---

## Conclusion

The Stock Tracker system provides comprehensive inventory management with:
- ✅ Real-time stock tracking
- ✅ Historical period comparison
- ✅ Profitability analysis
- ✅ Variance detection
- ✅ Multi-category support
- ✅ Automated calculations

All models, serializers, and views are now synchronized and ready for production use.
