"""
Stocktake calculation service implementing formulas from
Stocktake_Formulas.md.

All calculations work in base units (ml, grams, pieces).
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from .models import (
    Stocktake,
    StocktakeLine,
    StockItem,
    StockMovement,
    StockPeriod,
    StockSnapshot
)


def populate_stocktake(stocktake):
    """
    Generate stocktake lines with opening balances and period movements.
    Freezes valuation_cost at populate time.

    Args:
        stocktake: Stocktake instance

    Returns:
        int: Number of lines created
    """
    if stocktake.status != Stocktake.DRAFT:
        raise ValueError("Can only populate draft stocktakes")

    # Clear existing lines if re-populating
    stocktake.lines.all().delete()

    items = StockItem.objects.filter(hotel=stocktake.hotel)
    lines_created = 0

    for item in items:
        # Get opening balance (snapshot at period_start)
        opening_qty = _get_opening_balance(
            item,
            stocktake.period_start
        )

        # Calculate period movements
        movements = _calculate_period_movements(
            item,
            stocktake.period_start,
            stocktake.period_end
        )

        # Freeze valuation cost (using current unit_cost / UOM)
        valuation_cost = item.unit_cost / item.uom

        # Create line
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=opening_qty,
            purchases=movements['purchases'],
            waste=movements['waste'],
            transfers_in=movements['transfers_in'],
            transfers_out=movements['transfers_out'],
            adjustments=movements['adjustments'],
            valuation_cost=valuation_cost,
        )
        lines_created += 1

    return lines_created


def _get_opening_balance(item, period_start):
    """
    Calculate opening balance at period_start.
    
    Priority order:
    1. Use previous period's closing stock (from StockSnapshot)
    2. Use current stock levels if first stocktake (no movements/snapshots)
    3. Calculate from movements (legacy/backup method)
    """
    # OPTION 1: Try to find previous period's closing snapshot
    previous_snapshot = StockSnapshot.objects.filter(
        item=item,
        period__end_date__lt=period_start,
        period__hotel=item.hotel
    ).order_by('-period__end_date').first()
    
    if previous_snapshot:
        # Return previous period's closing as this period's opening
        # Use total_servings to include both full units + partial units
        return previous_snapshot.total_servings
    
    # No previous snapshot found - return 0 as opening balance
    # This ensures we only use period-based snapshots, not live inventory
    return Decimal('0')
    
    # LEGACY: Calculate from historical movements (kept for reference)
    # This code is no longer used but kept for backward compatibility
    movements_before = item.movements.filter(
        timestamp__lt=period_start
    ).aggregate(
        purchases=Sum(
            'quantity',
            filter=Q(movement_type__in=[
                StockMovement.PURCHASE,
                StockMovement.TRANSFER_IN
            ])
        ),
        outflows=Sum(
            'quantity',
            filter=Q(movement_type__in=[
                StockMovement.WASTE,
                StockMovement.TRANSFER_OUT
            ])
        ),
        adjustments=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.ADJUSTMENT)
        )
    )

    purchases = movements_before['purchases'] or Decimal('0')
    outflows = movements_before['outflows'] or Decimal('0')
    adjustments = movements_before['adjustments'] or Decimal('0')

    return purchases - outflows + adjustments


def _calculate_period_movements(item, period_start, period_end):
    """
    Calculate movements within the stocktake period.

    Returns dict with keys: purchases, waste,
    transfers_in, transfers_out, adjustments
    """
    from django.utils import timezone
    from datetime import datetime, time
    
    # Convert date to datetime for proper comparison
    # period_start (date) → datetime at 00:00:00
    # period_end (date) → datetime at 23:59:59
    start_dt = timezone.make_aware(datetime.combine(period_start, time.min))
    end_dt = timezone.make_aware(datetime.combine(period_end, time.max))
    
    movements = item.movements.filter(
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
    ).aggregate(
        purchases=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.PURCHASE)
        ),
        waste=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.WASTE)
        ),
        transfers_in=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.TRANSFER_IN)
        ),
        transfers_out=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.TRANSFER_OUT)
        ),
        adjustments=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.ADJUSTMENT)
        )
    )

    return {
        'purchases': movements['purchases'] or Decimal('0'),
        'waste': movements['waste'] or Decimal('0'),
        'transfers_in': movements['transfers_in'] or Decimal('0'),
        'transfers_out': movements['transfers_out'] or Decimal('0'),
        'adjustments': movements['adjustments'] or Decimal('0'),
    }


def approve_stocktake(stocktake, approved_by):
    """
    Approve stocktake and create ADJUSTMENT movements for variances.

    Args:
        stocktake: Stocktake instance
        approved_by: Staff approving the stocktake

    Returns:
        int: Number of adjustment movements created
    """
    if stocktake.status != Stocktake.DRAFT:
        raise ValueError("Can only approve draft stocktakes")

    adjustments_created = 0

    for line in stocktake.lines.all():
        variance = line.variance_qty

        if variance != Decimal('0'):
            # Create adjustment movement
            StockMovement.objects.create(
                hotel=stocktake.hotel,
                item=line.item,
                movement_type=StockMovement.ADJUSTMENT,
                quantity=variance,
                unit_cost=line.valuation_cost,
                reference=f"Stocktake-{stocktake.id}",
                notes=(
                    f"Stocktake adjustment: counted {line.counted_qty}, "
                    f"expected {line.expected_qty}"
                ),
                staff=approved_by,
            )
            adjustments_created += 1

    # Mark as approved
    stocktake.status = Stocktake.APPROVED
    stocktake.approved_at = timezone.now()
    stocktake.approved_by = approved_by
    stocktake.save()

    return adjustments_created


def calculate_category_totals(stocktake):
    """
    Calculate totals grouped by category.

    Returns:
        dict: {category_name: {expected_value, counted_value,
                               variance_value}}
    """
    totals = {}

    for line in stocktake.lines.select_related('item__category'):
        category_name = (
            line.item.category.name if line.item.category
            else 'Uncategorized'
        )

        if category_name not in totals:
            totals[category_name] = {
                'expected_value': Decimal('0'),
                'counted_value': Decimal('0'),
                'variance_value': Decimal('0'),
            }

        totals[category_name]['expected_value'] += line.expected_value
        totals[category_name]['counted_value'] += line.counted_value
        totals[category_name]['variance_value'] += line.variance_value

    return totals


def round_decimal(value, places=4):
    """
    Round Decimal to specified places (default 4 as per spec).
    """
    if isinstance(value, Decimal):
        return value.quantize(Decimal(10) ** -places)
    return Decimal(str(value)).quantize(Decimal(10) ** -places)


def populate_period_opening_stock(period):
    """
    Populate a new stock period with opening stock from last closed period.
    
    Opening stock = Last closed period's closing stock + movements between
    
    Args:
        period: StockPeriod instance to populate
    
    Returns:
        dict: {
            'snapshots_created': int,
            'previous_period': StockPeriod or None,
            'total_value': Decimal
        }
    
    Raises:
        ValueError: If period is already closed or has existing snapshots
    """
    if period.is_closed:
        raise ValueError("Cannot populate a closed period")
    
    # Check for existing snapshots
    existing_count = StockSnapshot.objects.filter(period=period).count()
    if existing_count > 0:
        raise ValueError(
            f"Period already has {existing_count} snapshots. "
            "Delete them first to repopulate."
        )
    
    # Get the previous closed period
    previous_period = period.get_previous_period()
    
    if not previous_period:
        # No previous period - this is the first period
        # Create snapshots from current stock levels
        return _create_snapshots_from_current_stock(period)
    
    if not previous_period.is_closed:
        raise ValueError(
            f"Previous period {previous_period.period_name} is not closed. "
            "Close it first before populating this period."
        )
    
    # Get all items from previous period's snapshots
    previous_snapshots = StockSnapshot.objects.filter(
        period=previous_period
    ).select_related('item', 'item__category')
    
    snapshots_created = 0
    total_value = Decimal('0.00')
    
    for prev_snapshot in previous_snapshots:
        item = prev_snapshot.item
        
        # Start with previous period's closing stock
        opening_full = prev_snapshot.closing_full_units
        opening_partial = prev_snapshot.closing_partial_units
        
        # Add any movements between periods
        movements_between = _calculate_movements_between_periods(
            item,
            previous_period.end_date,
            period.start_date
        )
        
        # Apply movements to opening stock
        # Movements are in servings, need to convert back to units
        movement_servings = movements_between['net_movement']
        
        # Convert servings to units based on category
        if movement_servings != Decimal('0'):
            # For simplicity, add to partial units
            # Frontend/user will adjust during stocktake entry
            opening_partial += movement_servings / item.uom
        
        # Calculate opening stock value using current costs
        # (costs may have changed since last period)
        category = item.category_id
        
        if category in ['D', 'B', 'M']:
            # Draught, Bottles, Mixers: partial = servings
            full_value = opening_full * item.unit_cost
            partial_value = opening_partial * item.cost_per_serving
        else:
            # Spirits, Wine: partial = fractional units
            full_value = opening_full * item.unit_cost
            partial_value = opening_partial * item.unit_cost
        
        opening_value = (full_value + partial_value).quantize(
            Decimal('0.01')
        )
        
        # Create snapshot with opening stock
        StockSnapshot.objects.create(
            hotel=period.hotel,
            item=item,
            period=period,
            closing_full_units=opening_full,
            closing_partial_units=opening_partial,
            unit_cost=item.unit_cost,
            cost_per_serving=item.cost_per_serving,
            closing_stock_value=opening_value,
            menu_price=item.menu_price or Decimal('0.00')
        )
        
        snapshots_created += 1
        total_value += opening_value
    
    return {
        'snapshots_created': snapshots_created,
        'previous_period': previous_period,
        'total_value': total_value
    }


def _create_snapshots_from_current_stock(period):
    """
    Create snapshots from current stock levels (for first period).
    """
    items = StockItem.objects.filter(
        hotel=period.hotel,
        active=True
    ).select_related('category')
    
    snapshots_created = 0
    total_value = Decimal('0.00')
    
    for item in items:
        StockSnapshot.objects.create(
            hotel=period.hotel,
            item=item,
            period=period,
            closing_full_units=item.current_full_units,
            closing_partial_units=item.current_partial_units,
            unit_cost=item.unit_cost,
            cost_per_serving=item.cost_per_serving,
            closing_stock_value=item.total_stock_value,
            menu_price=item.menu_price or Decimal('0.00')
        )
        snapshots_created += 1
        total_value += item.total_stock_value
    
    return {
        'snapshots_created': snapshots_created,
        'previous_period': None,
        'total_value': total_value
    }


def _calculate_movements_between_periods(item, previous_end_date, current_start_date):
    """
    Calculate net movements between two periods.
    
    Args:
        item: StockItem
        previous_end_date: End date of previous period
        current_start_date: Start date of current period
    
    Returns:
        dict: {'net_movement': Decimal} (positive = increase, negative = decrease)
    """
    # Get movements after previous period ended and before current period starts
    movements = StockMovement.objects.filter(
        item=item,
        timestamp__gt=previous_end_date,
        timestamp__lt=current_start_date
    ).aggregate(
        purchases=Sum(
            'quantity',
            filter=Q(movement_type__in=[
                StockMovement.PURCHASE,
                StockMovement.TRANSFER_IN
            ])
        ),
        outflows=Sum(
            'quantity',
            filter=Q(movement_type__in=[
                StockMovement.WASTE,
                StockMovement.TRANSFER_OUT
            ])
        ),
        adjustments=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.ADJUSTMENT)
        )
    )
    
    purchases = movements['purchases'] or Decimal('0')
    outflows = movements['outflows'] or Decimal('0')
    adjustments = movements['adjustments'] or Decimal('0')
    
    net_movement = purchases - outflows + adjustments
    
    return {
        'net_movement': net_movement,
        'purchases': purchases,
        'outflows': outflows,
        'adjustments': adjustments
    }
