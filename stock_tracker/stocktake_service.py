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
    StockMovement
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
            sales=movements['sales'],
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
    This is the sum of all movements BEFORE period_start.
    """
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
                StockMovement.SALE,
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

    Returns dict with keys: purchases, sales, waste,
    transfers_in, transfers_out, adjustments
    """
    movements = item.movements.filter(
        timestamp__gte=period_start,
        timestamp__lte=period_end
    ).aggregate(
        purchases=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.PURCHASE)
        ),
        sales=Sum(
            'quantity',
            filter=Q(movement_type=StockMovement.SALE)
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
        'sales': movements['sales'] or Decimal('0'),
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
        approved_by: User approving the stocktake

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
