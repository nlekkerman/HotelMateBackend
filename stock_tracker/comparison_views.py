"""
Dedicated views for period comparison and analytics.
Supports multi-period comparisons for advanced visualizations.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from decimal import Decimal
from collections import defaultdict

from hotel.models import Hotel
from .models import (
    StockPeriod,
    StockSnapshot,
    StockMovement,
    StockCategory
)


class CompareCategoriesView(APIView):
    """
    Compare aggregated category data across multiple periods.
    Optimized for pie charts, stacked bar charts.
    
    GET /stock_tracker/<hotel>/compare/categories/?periods=1,2,3
    """
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        # Get period IDs from query params
        period_ids_str = request.query_params.get('periods', '').strip()
        if not period_ids_str:
            return Response({
                "error": "periods parameter required (comma-separated IDs)",
                "example": "?periods=1,2,3",
                "hint": "Get available periods from /periods/?is_closed=true"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period_ids = [
                int(pid.strip()) for pid in period_ids_str.split(',')
                if pid.strip()
            ]
        except ValueError:
            return Response({
                "error": "Invalid period IDs format",
                "received": period_ids_str,
                "example": "?periods=1,2,3"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(period_ids) < 2:
            return Response(
                {"error": "At least 2 periods required for comparison"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch periods
        periods = StockPeriod.objects.filter(
            id__in=period_ids,
            hotel=hotel,
            is_closed=True
        ).order_by('start_date')
        
        if periods.count() != len(period_ids):
            return Response(
                {"error": "One or more periods not found or not closed"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all categories
        categories = StockCategory.objects.all()
        
        # Build category data for each period
        category_data = []
        
        for category in categories:
            cat_info = {
                'code': category.code,
                'name': category.name,
                'periods_data': []
            }
            
            for period in periods:
                # Get snapshots for this category and period
                snapshots = StockSnapshot.objects.filter(
                    hotel=hotel,
                    period=period,
                    item__category=category
                )
                
                # Get movements for this category and period
                movements = StockMovement.objects.filter(
                    hotel=hotel,
                    item__category=category,
                    timestamp__gte=period.start_date,
                    timestamp__lte=period.end_date
                )
                
                # Aggregate data
                total_value = snapshots.aggregate(
                    total=Sum('closing_stock_value')
                )['total'] or Decimal('0')
                
                item_count = snapshots.count()
                
                purchases = movements.filter(
                    movement_type=StockMovement.PURCHASE
                ).aggregate(
                    total=Sum('total_cost')
                )['total'] or Decimal('0')
                
                waste = movements.filter(
                    movement_type=StockMovement.WASTE
                ).aggregate(
                    total=Sum('total_cost')
                )['total'] or Decimal('0')
                
                waste_percentage = float(
                    (waste / purchases * 100) if purchases > 0 else 0
                )
                
                period_info = {
                    'period_id': period.id,
                    'period_name': period.period_name,
                    'total_value': float(total_value),
                    'item_count': item_count,
                    'purchases': float(purchases),
                    'waste': float(waste),
                    'waste_percentage': round(waste_percentage, 2)
                }
                
                cat_info['periods_data'].append(period_info)
            
            # Calculate changes across periods
            if len(cat_info['periods_data']) >= 2:
                first = cat_info['periods_data'][0]
                last = cat_info['periods_data'][-1]
                
                value_change = last['total_value'] - first['total_value']
                value_percentage = (
                    (value_change / first['total_value'] * 100)
                    if first['total_value'] > 0 else 0
                )
                
                cat_info['overall_change'] = {
                    'value_change': round(value_change, 2),
                    'value_percentage': round(value_percentage, 2),
                    'waste_improvement': round(
                        first['waste_percentage'] - last['waste_percentage'],
                        2
                    )
                }
            
            category_data.append(cat_info)
        
        # Calculate summary
        summary = self._calculate_summary(category_data, periods)
        
        return Response({
            'periods': [
                {
                    'id': p.id,
                    'name': p.period_name,
                    'start_date': p.start_date,
                    'end_date': p.end_date,
                    'is_closed': p.is_closed
                }
                for p in periods
            ],
            'categories': category_data,
            'summary': summary
        })
    
    def _calculate_summary(self, category_data, periods):
        """Calculate summary statistics"""
        total_value_first = sum(
            cat['periods_data'][0]['total_value']
            for cat in category_data
            if cat['periods_data']
        )
        total_value_last = sum(
            cat['periods_data'][-1]['total_value']
            for cat in category_data
            if cat['periods_data']
        )
        
        # Find best/worst performers
        best_performing = None
        worst_performing = None
        max_improvement = float('-inf')
        min_improvement = float('inf')
        
        for cat in category_data:
            if 'overall_change' in cat:
                change = cat['overall_change']['value_percentage']
                if change > max_improvement:
                    max_improvement = change
                    best_performing = cat['code']
                if change < min_improvement:
                    min_improvement = change
                    worst_performing = cat['code']
        
        return {
            'total_value_change': round(
                total_value_last - total_value_first, 2
            ),
            'total_value_percentage': round(
                ((total_value_last - total_value_first) /
                 total_value_first * 100)
                if total_value_first > 0 else 0,
                2
            ),
            'best_performing_category': best_performing,
            'worst_performing_category': worst_performing,
            'periods_compared': len(periods)
        }


class TopMoversView(APIView):
    """
    Identify biggest changes between two periods.
    
    GET /stock_tracker/<hotel>/compare/top-movers/?period1=1&period2=2&limit=10
    """
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        period1_id = request.query_params.get('period1', '').strip()
        period2_id = request.query_params.get('period2', '').strip()
        
        if not period1_id or not period2_id:
            return Response({
                "error": "Both period1 and period2 required",
                "example": "?period1=1&period2=2&limit=10",
                "hint": "Get available periods from /periods/?is_closed=true"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            limit = int(request.query_params.get('limit', 10))
        except ValueError:
            limit = 10
        
        try:
            period1 = StockPeriod.objects.get(
                id=int(period1_id), hotel=hotel, is_closed=True
            )
            period2 = StockPeriod.objects.get(
                id=int(period2_id), hotel=hotel, is_closed=True
            )
        except (StockPeriod.DoesNotExist, ValueError):
            return Response({
                "error": "One or both periods not found or not closed",
                "period1": period1_id,
                "period2": period2_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get snapshots
        snapshots1 = {
            s.item_id: s for s in
            StockSnapshot.objects.filter(hotel=hotel, period=period1)
            .select_related('item', 'item__category')
        }
        snapshots2 = {
            s.item_id: s for s in
            StockSnapshot.objects.filter(hotel=hotel, period=period2)
            .select_related('item', 'item__category')
        }
        
        # Calculate changes
        changes = []
        all_item_ids = set(snapshots1.keys()) | set(snapshots2.keys())
        
        for item_id in all_item_ids:
            s1 = snapshots1.get(item_id)
            s2 = snapshots2.get(item_id)
            
            if s1 and s2:
                value_change = float(
                    s2.closing_stock_value - s1.closing_stock_value
                )
                percentage_change = (
                    (value_change / float(s1.closing_stock_value) * 100)
                    if s1.closing_stock_value > 0 else 0
                )
                
                # Determine reason
                reason = self._determine_reason(
                    s1, s2, value_change, percentage_change
                )
                
                changes.append({
                    'item_id': item_id,
                    'sku': s1.item.sku,
                    'name': s1.item.name,
                    'category': s1.item.category.code,
                    'period1_value': float(s1.closing_stock_value),
                    'period2_value': float(s2.closing_stock_value),
                    'absolute_change': value_change,
                    'percentage_change': round(percentage_change, 2),
                    'reason': reason
                })
        
        # Sort and split
        changes.sort(key=lambda x: abs(x['absolute_change']), reverse=True)
        increases = [c for c in changes if c['absolute_change'] > 0][:limit]
        decreases = [c for c in changes if c['absolute_change'] < 0][:limit]
        
        # Find new and discontinued items
        new_items = [
            {
                'item_id': item_id,
                'sku': snapshots2[item_id].item.sku,
                'name': snapshots2[item_id].item.name,
                'category': snapshots2[item_id].item.category.code,
                'value': float(snapshots2[item_id].closing_stock_value)
            }
            for item_id in (set(snapshots2.keys()) - set(snapshots1.keys()))
        ]
        
        discontinued_items = [
            {
                'item_id': item_id,
                'sku': snapshots1[item_id].item.sku,
                'name': snapshots1[item_id].item.name,
                'category': snapshots1[item_id].item.category.code,
                'last_value': float(snapshots1[item_id].closing_stock_value)
            }
            for item_id in (set(snapshots1.keys()) - set(snapshots2.keys()))
        ]
        
        return Response({
            'period1': {
                'id': period1.id,
                'name': period1.period_name,
                'start_date': period1.start_date,
                'end_date': period1.end_date
            },
            'period2': {
                'id': period2.id,
                'name': period2.period_name,
                'start_date': period2.start_date,
                'end_date': period2.end_date
            },
            'biggest_increases': increases,
            'biggest_decreases': decreases,
            'new_items': new_items,
            'discontinued_items': discontinued_items
        })
    
    def _determine_reason(self, s1, s2, value_change, percentage_change):
        """Determine likely reason for change"""
        if abs(percentage_change) > 100:
            return 'significant_change'
        elif percentage_change > 50:
            return 'stock_buildup'
        elif percentage_change > 20:
            return 'increased_stock'
        elif percentage_change < -50:
            return 'major_reduction'
        elif percentage_change < -20:
            return 'decreased_stock'
        else:
            return 'normal_variance'


class CostAnalysisView(APIView):
    """
    Detailed cost breakdown between two periods.
    
    GET /stock_tracker/<hotel>/compare/cost-analysis/?period1=1&period2=2
    """
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        period1_id = request.query_params.get('period1', '').strip()
        period2_id = request.query_params.get('period2', '').strip()
        
        if not period1_id or not period2_id:
            return Response({
                "error": "Both period1 and period2 required",
                "example": "?period1=1&period2=2",
                "hint": "Get available periods from /periods/?is_closed=true"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period1 = StockPeriod.objects.get(
                id=int(period1_id), hotel=hotel, is_closed=True
            )
            period2 = StockPeriod.objects.get(
                id=int(period2_id), hotel=hotel, is_closed=True
            )
        except (StockPeriod.DoesNotExist, ValueError):
            return Response({
                "error": "One or both periods not found or not closed",
                "period1": period1_id,
                "period2": period2_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate for both periods
        period1_data = self._calculate_period_costs(period1, hotel)
        period2_data = self._calculate_period_costs(period2, hotel)
        
        # Calculate comparison metrics
        comparison = self._calculate_comparison(period1_data, period2_data)
        
        # Build waterfall chart data for period2
        waterfall_data = [
            {
                'label': 'Opening Stock',
                'value': period2_data['opening_stock_value']
            },
            {
                'label': 'Purchases',
                'value': period2_data['purchases']
            },
            {
                'label': 'Waste',
                'value': -period2_data['waste_cost']
            },
            {
                'label': 'Transfer Net',
                'value': period2_data['transfer_net']
            },
            {
                'label': 'Adjustments',
                'value': period2_data['adjustments']
            },
            {
                'label': 'Closing Stock',
                'value': -period2_data['closing_stock_value']
            },
            {
                'label': 'Usage/COGS',
                'value': period2_data['theoretical_usage']
            }
        ]
        
        return Response({
            'period1': {
                'id': period1.id,
                'name': period1.period_name,
                **period1_data
            },
            'period2': {
                'id': period2.id,
                'name': period2.period_name,
                **period2_data
            },
            'comparison': comparison,
            'waterfall_data': waterfall_data
        })
    
    def _calculate_period_costs(self, period, hotel):
        """Calculate cost metrics for a period"""
        # Get opening stock (from previous period's closing)
        prev_period = period.get_previous_period()
        opening_stock = Decimal('0')
        
        if prev_period:
            opening_stock = StockSnapshot.objects.filter(
                hotel=hotel,
                period=prev_period
            ).aggregate(
                total=Sum('closing_stock_value')
            )['total'] or Decimal('0')
        
        # Get closing stock
        closing_stock = StockSnapshot.objects.filter(
            hotel=hotel,
            period=period
        ).aggregate(
            total=Sum('closing_stock_value')
        )['total'] or Decimal('0')
        
        # Get movements
        movements = StockMovement.objects.filter(
            hotel=hotel,
            timestamp__gte=period.start_date,
            timestamp__lte=period.end_date
        )
        
        purchases = movements.filter(
            movement_type=StockMovement.PURCHASE
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')
        
        waste = movements.filter(
            movement_type=StockMovement.WASTE
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')
        
        transfers_in = movements.filter(
            movement_type=StockMovement.TRANSFER_IN
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')
        
        transfers_out = movements.filter(
            movement_type=StockMovement.TRANSFER_OUT
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')
        
        adjustments = movements.filter(
            movement_type=StockMovement.ADJUSTMENT
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')
        
        transfer_net = transfers_in - transfers_out
        
        # Theoretical usage: Opening + Purchases - Closing
        theoretical_usage = opening_stock + purchases - closing_stock
        
        # Actual COGS includes waste
        actual_cogs = theoretical_usage + waste
        
        return {
            'opening_stock_value': float(opening_stock),
            'purchases': float(purchases),
            'closing_stock_value': float(closing_stock),
            'theoretical_usage': float(theoretical_usage),
            'waste_cost': float(waste),
            'transfer_net': float(transfer_net),
            'adjustments': float(adjustments),
            'actual_cogs': float(actual_cogs)
        }
    
    def _calculate_comparison(self, p1_data, p2_data):
        """Calculate comparison metrics"""
        cogs_change = p2_data['actual_cogs'] - p1_data['actual_cogs']
        cogs_percentage = (
            (cogs_change / p1_data['actual_cogs'] * 100)
            if p1_data['actual_cogs'] > 0 else 0
        )
        
        waste_change = p2_data['waste_cost'] - p1_data['waste_cost']
        waste_trend = (
            'increasing' if waste_change > 0
            else 'decreasing' if waste_change < 0
            else 'stable'
        )
        
        # Calculate efficiency rating (0-10)
        waste_p1_pct = (
            (p1_data['waste_cost'] / p1_data['purchases'] * 100)
            if p1_data['purchases'] > 0 else 0
        )
        waste_p2_pct = (
            (p2_data['waste_cost'] / p2_data['purchases'] * 100)
            if p2_data['purchases'] > 0 else 0
        )
        
        efficiency_rating = max(0, min(10, 10 - waste_p2_pct))
        
        return {
            'cogs_change': round(cogs_change, 2),
            'cogs_percentage': round(cogs_percentage, 2),
            'waste_trend': waste_trend,
            'waste_change': round(waste_change, 2),
            'efficiency_rating': round(efficiency_rating, 1),
            'waste_p1_percentage': round(waste_p1_pct, 2),
            'waste_p2_percentage': round(waste_p2_pct, 2)
        }


class TrendAnalysisView(APIView):
    """
    Multi-period trend analysis for visualizations.
    Supports 2+ periods for line/bar charts.
    
    GET /stock_tracker/<hotel>/compare/trend-analysis/?periods=1,2,3,4
        &category=S (optional)
        &items=123,456 (optional - specific item IDs)
    """
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        # Get period IDs
        period_ids_str = request.query_params.get('periods', '').strip()
        if not period_ids_str:
            return Response({
                "error": "periods parameter required (comma-separated IDs)",
                "example": "?periods=1,2,3,4",
                "hint": "Get available periods from /periods/?is_closed=true"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period_ids = [
                int(pid.strip()) for pid in period_ids_str.split(',')
                if pid.strip()
            ]
        except ValueError:
            return Response({
                "error": "Invalid period IDs format",
                "received": period_ids_str,
                "example": "?periods=1,2,3,4"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(period_ids) < 2:
            return Response({
                "error": "At least 2 periods required for trend analysis",
                "received_count": len(period_ids)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch periods
        periods = StockPeriod.objects.filter(
            id__in=period_ids,
            hotel=hotel,
            is_closed=True
        ).order_by('start_date')
        
        if periods.count() != len(period_ids):
            return Response(
                {"error": "One or more periods not found or not closed"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Optional filters
        category_code = request.query_params.get('category')
        item_ids_str = request.query_params.get('items')
        
        # Build base queryset
        snapshots_base = StockSnapshot.objects.filter(
            hotel=hotel,
            period__in=periods
        ).select_related('item', 'item__category', 'period')
        
        if category_code:
            snapshots_base = snapshots_base.filter(
                item__category__code=category_code
            )
        
        if item_ids_str:
            try:
                item_ids = [int(iid) for iid in item_ids_str.split(',')]
                snapshots_base = snapshots_base.filter(item_id__in=item_ids)
            except ValueError:
                return Response(
                    {"error": "Invalid item IDs format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Group by item
        items_data = defaultdict(lambda: {
            'item_info': None,
            'trend_data': []
        })
        
        for snapshot in snapshots_base:
            item_id = snapshot.item_id
            
            if items_data[item_id]['item_info'] is None:
                items_data[item_id]['item_info'] = {
                    'item_id': item_id,
                    'sku': snapshot.item.sku,
                    'name': snapshot.item.name,
                    'category': snapshot.item.category.code
                }
            
            # Get waste for this item in this period
            waste = StockMovement.objects.filter(
                hotel=hotel,
                item_id=item_id,
                movement_type=StockMovement.WASTE,
                timestamp__gte=snapshot.period.start_date,
                timestamp__lte=snapshot.period.end_date
            ).aggregate(
                total=Sum('total_cost')
            )['total'] or Decimal('0')
            
            items_data[item_id]['trend_data'].append({
                'period_id': snapshot.period_id,
                'value': float(snapshot.closing_stock_value),
                'servings': float(snapshot.total_servings),
                'waste': float(waste)
            })
        
        # Calculate trends and volatility
        items_list = []
        for item_id, data in items_data.items():
            # Sort trend data by period
            data['trend_data'].sort(key=lambda x: x['period_id'])
            
            # Calculate statistics
            values = [td['value'] for td in data['trend_data']]
            avg_value = sum(values) / len(values) if values else 0
            
            # Determine trend direction
            if len(values) >= 2:
                first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
                second_half_avg = sum(values[len(values)//2:]) / (
                    len(values) - len(values)//2
                )
                
                if second_half_avg > first_half_avg * 1.1:
                    trend_direction = 'increasing'
                elif second_half_avg < first_half_avg * 0.9:
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'stable'
            
            # Calculate volatility (coefficient of variation)
            if avg_value > 0 and len(values) > 1:
                variance = sum((v - avg_value) ** 2 for v in values) / len(values)
                std_dev = variance ** 0.5
                cv = (std_dev / avg_value) * 100
                
                if cv > 30:
                    volatility = 'high'
                elif cv > 15:
                    volatility = 'medium'
                else:
                    volatility = 'low'
            else:
                volatility = 'low'
            
            items_list.append({
                **data['item_info'],
                'trend_data': data['trend_data'],
                'trend_direction': trend_direction,
                'average_value': round(avg_value, 2),
                'volatility': volatility
            })
        
        return Response({
            'periods': [
                {
                    'id': p.id,
                    'name': p.period_name,
                    'start_date': p.start_date,
                    'end_date': p.end_date
                }
                for p in periods
            ],
            'items': items_list,
            'filters': {
                'category': category_code,
                'item_count': len(items_list)
            }
        })


class VarianceHeatmapView(APIView):
    """
    Generate heatmap data showing variance across categories and periods.
    
    GET /stock_tracker/<hotel>/compare/variance-heatmap/?periods=1,2,3,4
    """
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        # Get period IDs
        period_ids_str = request.query_params.get('periods', '').strip()
        if not period_ids_str:
            return Response({
                "error": "periods parameter required (comma-separated IDs)",
                "example": "?periods=1,2,3,4",
                "hint": "Get available periods from /periods/?is_closed=true"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period_ids = [
                int(pid.strip()) for pid in period_ids_str.split(',')
                if pid.strip()
            ]
        except ValueError:
            return Response({
                "error": "Invalid period IDs format",
                "received": period_ids_str,
                "example": "?periods=1,2,3,4"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(period_ids) < 2:
            return Response({
                "error": "At least 2 periods required",
                "received_count": len(period_ids)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch periods
        periods = list(StockPeriod.objects.filter(
            id__in=period_ids,
            hotel=hotel,
            is_closed=True
        ).order_by('start_date'))
        
        if len(periods) != len(period_ids):
            return Response(
                {"error": "One or more periods not found or not closed"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all categories
        categories = list(StockCategory.objects.all())
        
        # Build heatmap data
        heatmap_data = []
        
        for period_idx, period in enumerate(periods):
            for cat_idx, category in enumerate(categories):
                # Get value for this period and category
                current_value = StockSnapshot.objects.filter(
                    hotel=hotel,
                    period=period,
                    item__category=category
                ).aggregate(
                    total=Sum('closing_stock_value')
                )['total'] or Decimal('0')
                
                # Get previous period value (if not first period)
                if period_idx > 0:
                    prev_period = periods[period_idx - 1]
                    prev_value = StockSnapshot.objects.filter(
                        hotel=hotel,
                        period=prev_period,
                        item__category=category
                    ).aggregate(
                        total=Sum('closing_stock_value')
                    )['total'] or Decimal('0')
                    
                    # Calculate variance
                    if prev_value > 0:
                        variance = float(
                            (current_value - prev_value) / prev_value * 100
                        )
                    else:
                        variance = 0
                else:
                    variance = 0
                
                # Determine severity
                abs_variance = abs(variance)
                if abs_variance > 30:
                    severity = 'high'
                elif abs_variance > 15:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                # [period_index, category_index, variance_value, severity]
                heatmap_data.append([
                    period_idx,
                    cat_idx,
                    round(variance, 2),
                    severity
                ])
        
        return Response({
            'periods': [p.period_name for p in periods],
            'categories': [c.code for c in categories],
            'heatmap_data': heatmap_data,
            'color_scale': {
                'low': '#90EE90',
                'medium': '#FFD700',
                'high': '#FF6347'
            }
        })


class PerformanceScorecardView(APIView):
    """
    Overall performance metrics comparing two periods.
    
    GET /stock_tracker/<hotel>/compare/performance-scorecard/
        ?period1=1&period2=2
    """
    
    def get(self, request, hotel_identifier):
        hotel = get_object_or_404(
            Hotel,
            Q(slug=hotel_identifier) | Q(subdomain=hotel_identifier)
        )
        
        period1_id = request.query_params.get('period1', '').strip()
        period2_id = request.query_params.get('period2', '').strip()
        
        if not period1_id or not period2_id:
            return Response({
                "error": "Both period1 and period2 required",
                "example": "?period1=1&period2=2",
                "hint": "Get available periods from /periods/?is_closed=true"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            period1 = StockPeriod.objects.get(
                id=int(period1_id), hotel=hotel, is_closed=True
            )
            period2 = StockPeriod.objects.get(
                id=int(period2_id), hotel=hotel, is_closed=True
            )
        except (StockPeriod.DoesNotExist, ValueError):
            return Response({
                "error": "One or both periods not found or not closed",
                "period1": period1_id,
                "period2": period2_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate scores for each period
        p1_scores = self._calculate_scores(period1, hotel)
        p2_scores = self._calculate_scores(period2, hotel)
        
        # Build metrics comparison
        metrics = [
            {
                'name': 'Stock Value Management',
                'period1_score': p1_scores['value_mgmt'],
                'period2_score': p2_scores['value_mgmt'],
                'weight': 0.3,
                'status': self._get_status(
                    p1_scores['value_mgmt'],
                    p2_scores['value_mgmt']
                )
            },
            {
                'name': 'Waste Control',
                'period1_score': p1_scores['waste_control'],
                'period2_score': p2_scores['waste_control'],
                'weight': 0.25,
                'status': self._get_status(
                    p1_scores['waste_control'],
                    p2_scores['waste_control']
                )
            },
            {
                'name': 'Stock Turnover',
                'period1_score': p1_scores['turnover'],
                'period2_score': p2_scores['turnover'],
                'weight': 0.25,
                'status': self._get_status(
                    p1_scores['turnover'],
                    p2_scores['turnover']
                )
            },
            {
                'name': 'Variance Control',
                'period1_score': p1_scores['variance'],
                'period2_score': p2_scores['variance'],
                'weight': 0.2,
                'status': self._get_status(
                    p1_scores['variance'],
                    p2_scores['variance']
                )
            }
        ]
        
        # Calculate overall scores
        p1_overall = sum(m['period1_score'] * m['weight'] for m in metrics)
        p2_overall = sum(m['period2_score'] * m['weight'] for m in metrics)
        
        overall_score = {
            'period1': int(p1_overall),
            'period2': int(p2_overall),
            'improvement': int(p2_overall - p1_overall)
        }
        
        # Radar chart data
        radar_chart_data = {
            'labels': [
                'Value Mgmt',
                'Waste Control',
                'Turnover',
                'Variance'
            ],
            'period1': [
                p1_scores['value_mgmt'],
                p1_scores['waste_control'],
                p1_scores['turnover'],
                p1_scores['variance']
            ],
            'period2': [
                p2_scores['value_mgmt'],
                p2_scores['waste_control'],
                p2_scores['turnover'],
                p2_scores['variance']
            ]
        }
        
        return Response({
            'period1': {
                'id': period1.id,
                'name': period1.period_name
            },
            'period2': {
                'id': period2.id,
                'name': period2.period_name
            },
            'overall_score': overall_score,
            'metrics': metrics,
            'radar_chart_data': radar_chart_data
        })
    
    def _calculate_scores(self, period, hotel):
        """Calculate performance scores (0-100) for a period"""
        # Get stock value
        total_stock_value = StockSnapshot.objects.filter(
            hotel=hotel,
            period=period
        ).aggregate(
            total=Sum('closing_stock_value')
        )['total'] or Decimal('0')
        
        # Get movements
        movements = StockMovement.objects.filter(
            hotel=hotel,
            timestamp__gte=period.start_date,
            timestamp__lte=period.end_date
        )
        
        purchases = movements.filter(
            movement_type=StockMovement.PURCHASE
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0')
        
        waste = movements.filter(
            movement_type=StockMovement.WASTE
        ).aggregate(total=Sum('total_cost'))['total'] or Decimal('0')
        
        # Value Management Score (stock value relative to purchases)
        if purchases > 0:
            value_ratio = float(total_stock_value / purchases)
            value_mgmt = min(100, max(0, 100 - abs(value_ratio - 1.5) * 20))
        else:
            value_mgmt = 50
        
        # Waste Control Score (lower waste % = higher score)
        if purchases > 0:
            waste_pct = float(waste / purchases * 100)
            waste_control = max(0, min(100, 100 - waste_pct * 10))
        else:
            waste_control = 50
        
        # Turnover Score (simulated - higher is better)
        if total_stock_value > 0:
            turnover_ratio = float(purchases / total_stock_value)
            turnover = min(100, max(0, turnover_ratio * 50))
        else:
            turnover = 50
        
        # Variance Score (lower variance = higher score)
        # Simplified: based on waste percentage
        variance = max(0, min(100, 100 - waste_pct * 5))
        
        return {
            'value_mgmt': int(value_mgmt),
            'waste_control': int(waste_control),
            'turnover': int(turnover),
            'variance': int(variance)
        }
    
    def _get_status(self, score1, score2):
        """Determine improvement status"""
        diff = score2 - score1
        if diff >= 10:
            return 'significantly_improved'
        elif diff > 0:
            return 'improved'
        elif diff == 0:
            return 'unchanged'
        elif diff > -10:
            return 'slightly_declined'
        else:
            return 'declined'
