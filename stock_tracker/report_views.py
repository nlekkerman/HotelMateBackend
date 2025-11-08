"""
Stock Value and Sales Report Views
Provides calculated data for frontend display
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal

from hotel.models import Hotel
from .models import StockPeriod, StockSnapshot, StockMovement


class StockValueReportView(APIView):
    """
    Calculate stock value report for a closed period
    Returns cost value, sales value, and potential profit
    Grouped by category and by item
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        period_id = request.query_params.get('period')
        
        if not period_id:
            return Response(
                {"error": "period parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            period = StockPeriod.objects.get(id=period_id, hotel=hotel)
        except StockPeriod.DoesNotExist:
            return Response(
                {"error": "Period not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all snapshots for this period
        snapshots = StockSnapshot.objects.filter(
            hotel=hotel,
            period=period
        ).select_related('item', 'item__category')
        
        # Initialize totals
        total_cost_value = Decimal('0.00')
        total_sales_value = Decimal('0.00')
        
        category_data = {}
        items_data = []
        
        for snapshot in snapshots:
            item = snapshot.item
            category = item.category.code
            
            # Initialize category if needed
            if category not in category_data:
                category_name = {
                    'D': 'Draught Beers',
                    'B': 'Bottled Beers',
                    'S': 'Spirits',
                    'M': 'Minerals/Syrups',
                    'W': 'Wine'
                }.get(category, category)
                
                category_data[category] = {
                    'code': category,
                    'name': category_name,
                    'cost_value': Decimal('0.00'),
                    'sales_value': Decimal('0.00'),
                    'potential_profit': Decimal('0.00'),
                    'markup_percentage': Decimal('0.00'),
                    'items_with_price': 0,
                    'items_without_price': 0
                }
            
            # Cost value (what we paid)
            cost_value = snapshot.closing_stock_value
            total_cost_value += cost_value
            category_data[category]['cost_value'] += cost_value
            
            # Calculate servings in stock
            if category in ['D', 'B', 'M']:
                servings = (snapshot.closing_full_units * item.uom) + \
                          snapshot.closing_partial_units
            else:  # S, W
                servings = (snapshot.closing_full_units * item.uom) + \
                          (snapshot.closing_partial_units * item.uom)
            
            # Sales value (what we can sell it for)
            sales_value = Decimal('0.00')
            has_price = False
            
            if category == 'W' and item.bottle_price:
                # Wine by bottle
                bottles = snapshot.closing_full_units
                sales_value = bottles * item.bottle_price
                has_price = True
            elif item.menu_price:
                # By serving
                sales_value = servings * item.menu_price
                has_price = True
            
            if has_price:
                category_data[category]['items_with_price'] += 1
            else:
                category_data[category]['items_without_price'] += 1
            
            total_sales_value += sales_value
            category_data[category]['sales_value'] += sales_value
            
            # Item data
            potential_profit = sales_value - cost_value
            markup_percentage = Decimal('0.00')
            if cost_value > 0:
                markup_percentage = (potential_profit / cost_value) * 100
            
            items_data.append({
                'item_id': item.id,
                'sku': item.sku,
                'name': item.name,
                'category': category,
                'closing_full_units': float(snapshot.closing_full_units),
                'closing_partial_units': float(snapshot.closing_partial_units),
                'servings_in_stock': float(servings),
                'cost_value': float(cost_value),
                'sales_value': float(sales_value),
                'potential_profit': float(potential_profit),
                'markup_percentage': float(markup_percentage),
                'has_menu_price': has_price,
                'menu_price': float(item.menu_price) if item.menu_price else None,
                'bottle_price': float(item.bottle_price) if item.bottle_price else None
            })
        
        # Calculate category totals and markups
        for cat_code, cat_data in category_data.items():
            cat_data['potential_profit'] = cat_data['sales_value'] - cat_data['cost_value']
            if cat_data['cost_value'] > 0:
                cat_data['markup_percentage'] = (
                    cat_data['potential_profit'] / cat_data['cost_value']
                ) * 100
            
            # Convert to float for JSON
            cat_data['cost_value'] = float(cat_data['cost_value'])
            cat_data['sales_value'] = float(cat_data['sales_value'])
            cat_data['potential_profit'] = float(cat_data['potential_profit'])
            cat_data['markup_percentage'] = float(cat_data['markup_percentage'])
        
        # Calculate overall totals
        total_potential_profit = total_sales_value - total_cost_value
        total_markup_percentage = Decimal('0.00')
        if total_cost_value > 0:
            total_markup_percentage = (
                total_potential_profit / total_cost_value
            ) * 100
        
        # Sort items by sales value descending
        items_data.sort(key=lambda x: x['sales_value'], reverse=True)
        
        # Convert category_data dict to list sorted by code
        categories_list = [
            category_data[code] for code in ['D', 'B', 'S', 'M', 'W']
            if code in category_data
        ]
        
        return Response({
            'period': {
                'id': period.id,
                'period_name': period.period_name,
                'start_date': period.start_date,
                'end_date': period.end_date,
                'is_closed': period.is_closed
            },
            'totals': {
                'cost_value': float(total_cost_value),
                'sales_value': float(total_sales_value),
                'potential_profit': float(total_potential_profit),
                'markup_percentage': float(total_markup_percentage)
            },
            'categories': categories_list,
            'items': items_data,
            'summary': {
                'total_items': len(items_data),
                'items_with_price': sum(1 for i in items_data if i['has_menu_price']),
                'items_without_price': sum(1 for i in items_data if not i['has_menu_price'])
            }
        })


class SalesReportView(APIView):
    """
    Calculate sales report for a period
    Requires September opening, October closing, and October purchases
    Returns revenue, cost of sales, gross profit
    Grouped by category and by item
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        period_id = request.query_params.get('period')
        
        if not period_id:
            return Response(
                {"error": "period parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            october_period = StockPeriod.objects.get(id=period_id, hotel=hotel)
        except StockPeriod.DoesNotExist:
            return Response(
                {"error": "Period not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get September period (previous month)
        september_period = october_period.get_previous_period()
        
        if not september_period:
            return Response(
                {"error": "Previous period (September) not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get snapshots for both periods
        sept_snapshots = list(StockSnapshot.objects.filter(
            hotel=hotel,
            period=september_period
        ).select_related('item', 'item__category'))
        
        oct_snapshots = list(StockSnapshot.objects.filter(
            hotel=hotel,
            period=october_period
        ).select_related('item', 'item__category'))
        
        # Get October purchases
        purchases = list(StockMovement.objects.filter(
            hotel=hotel,
            period=october_period,
            movement_type='PURCHASE'
        ).select_related('item'))
        
        # Check if purchases are mock data
        mock_purchases = [p for p in purchases if 'Mock delivery' in (p.notes or '')]
        has_mock_data = len(mock_purchases) > 0
        mock_purchase_value = sum(
            (p.quantity * p.unit_cost) for p in mock_purchases
        )
        
        # Create lookups
        oct_lookup = {s.item_id: s for s in oct_snapshots}
        purchase_lookup = {}
        for p in purchases:
            if p.item_id not in purchase_lookup:
                purchase_lookup[p.item_id] = Decimal('0.00')
            purchase_lookup[p.item_id] += p.quantity
        
        # Initialize totals
        total_revenue = Decimal('0.00')
        total_cost = Decimal('0.00')
        total_servings = Decimal('0.00')
        
        category_data = {}
        items_data = []
        
        # Calculate for each item
        for sept_snap in sept_snapshots:
            oct_snap = oct_lookup.get(sept_snap.item_id)
            if not oct_snap:
                continue
            
            item = sept_snap.item
            category = item.category.code
            
            # Initialize category
            if category not in category_data:
                category_name = {
                    'D': 'Draught Beers',
                    'B': 'Bottled Beers',
                    'S': 'Spirits',
                    'M': 'Minerals/Syrups',
                    'W': 'Wine'
                }.get(category, category)
                
                category_data[category] = {
                    'code': category,
                    'name': category_name,
                    'revenue': Decimal('0.00'),
                    'cost_of_sales': Decimal('0.00'),
                    'gross_profit': Decimal('0.00'),
                    'gross_profit_percentage': Decimal('0.00'),
                    'servings_sold': Decimal('0.00'),
                    'percent_of_total': Decimal('0.00')
                }
            
            # Get purchased servings
            purchased_servings = purchase_lookup.get(item.id, Decimal('0.00'))
            
            # Calculate servings
            if category in ['D', 'B', 'M']:
                sept_servings = (sept_snap.closing_full_units * item.uom) + \
                               sept_snap.closing_partial_units
                oct_servings = (oct_snap.closing_full_units * item.uom) + \
                              oct_snap.closing_partial_units
            else:  # S, W
                sept_servings = (sept_snap.closing_full_units * item.uom) + \
                               (sept_snap.closing_partial_units * item.uom)
                oct_servings = (oct_snap.closing_full_units * item.uom) + \
                              (oct_snap.closing_partial_units * item.uom)
            
            # Consumption = Opening + Purchases - Closing
            consumption = sept_servings + purchased_servings - oct_servings
            
            if consumption > 0:
                # Calculate revenue
                revenue = Decimal('0.00')
                if category == 'W' and item.bottle_price:
                    bottles = consumption / item.uom if item.uom > 0 else Decimal('0.00')
                    revenue = bottles * item.bottle_price
                elif item.menu_price:
                    revenue = consumption * item.menu_price
                
                # Calculate cost
                cost = consumption * sept_snap.cost_per_serving
                
                total_revenue += revenue
                total_cost += cost
                total_servings += consumption
                
                category_data[category]['revenue'] += revenue
                category_data[category]['cost_of_sales'] += cost
                category_data[category]['servings_sold'] += consumption
                
                # Item data
                items_data.append({
                    'item_id': item.id,
                    'sku': item.sku,
                    'name': item.name,
                    'category': category,
                    'sept_servings': float(sept_servings),
                    'purchased_servings': float(purchased_servings),
                    'oct_servings': float(oct_servings),
                    'consumption': float(consumption),
                    'revenue': float(revenue),
                    'cost': float(cost),
                    'profit': float(revenue - cost),
                    'menu_price': float(item.menu_price) if item.menu_price else None,
                    'bottle_price': float(item.bottle_price) if item.bottle_price else None
                })
        
        # Calculate category totals
        for cat_code, cat_data in category_data.items():
            cat_data['gross_profit'] = cat_data['revenue'] - cat_data['cost_of_sales']
            if cat_data['revenue'] > 0:
                cat_data['gross_profit_percentage'] = (
                    cat_data['gross_profit'] / cat_data['revenue']
                ) * 100
            if total_revenue > 0:
                cat_data['percent_of_total'] = (
                    cat_data['revenue'] / total_revenue
                ) * 100
            
            # Convert to float
            cat_data['revenue'] = float(cat_data['revenue'])
            cat_data['cost_of_sales'] = float(cat_data['cost_of_sales'])
            cat_data['gross_profit'] = float(cat_data['gross_profit'])
            cat_data['gross_profit_percentage'] = float(cat_data['gross_profit_percentage'])
            cat_data['servings_sold'] = float(cat_data['servings_sold'])
            cat_data['percent_of_total'] = float(cat_data['percent_of_total'])
        
        # Calculate totals
        gross_profit = total_revenue - total_cost
        gross_profit_percentage = Decimal('0.00')
        if total_revenue > 0:
            gross_profit_percentage = (gross_profit / total_revenue) * 100
        
        # Sort items by revenue descending
        items_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Convert category_data to list
        categories_list = [
            category_data[code] for code in ['D', 'B', 'S', 'M', 'W']
            if code in category_data
        ]
        
        # Calculate purchase totals
        total_purchase_value = sum(
            (p.quantity * p.unit_cost) for p in purchases
        )
        
        return Response({
            'period': {
                'id': october_period.id,
                'period_name': october_period.period_name,
                'start_date': october_period.start_date,
                'end_date': october_period.end_date,
                'previous_period': september_period.period_name
            },
            'totals': {
                'revenue': float(total_revenue),
                'cost_of_sales': float(total_cost),
                'gross_profit': float(gross_profit),
                'gross_profit_percentage': float(gross_profit_percentage),
                'servings_sold': float(total_servings)
            },
            'stock_movement': {
                'sept_opening': float(sum(s.closing_stock_value for s in sept_snapshots)),
                'oct_purchases': float(total_purchase_value),
                'oct_closing': float(sum(s.closing_stock_value for s in oct_snapshots)),
                'consumed': float(total_cost)
            },
            'categories': categories_list,
            'items': items_data,
            'data_quality': {
                'has_mock_data': has_mock_data,
                'mock_purchase_count': len(mock_purchases),
                'total_purchase_count': len(purchases),
                'mock_purchase_value': float(mock_purchase_value),
                'warning': 'Contains mock purchase data - Replace with actual POS figures' if has_mock_data else None
            }
        })
