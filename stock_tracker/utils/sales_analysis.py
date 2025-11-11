"""
Sales Analysis Utilities
=========================

CRITICAL: These functions are for ANALYSIS/REPORTING ONLY.
They combine stock item sales with cocktail sales for business intelligence.

These functions DO NOT:
- Modify stocktake calculations
- Affect inventory valuations
- Change COGS calculations
- Touch StocktakeLine data

They are PURE functions that take data and return calculated results.
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional


def combine_sales_data(
    general_sales: Dict[str, Any],
    cocktail_sales: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Combine stock item sales with cocktail sales for reporting.
    
    Args:
        general_sales: Stock item sales data
            {
                'revenue': Decimal,
                'cost': Decimal,
                'count': int
            }
        cocktail_sales: Cocktail sales data
            {
                'revenue': Decimal,
                'cost': Decimal,
                'count': int
            }
    
    Returns:
        Combined sales data with totals and breakdown
        {
            'total_revenue': Decimal,
            'total_cost': Decimal,
            'total_count': int,
            'profit': Decimal,
            'gp_percentage': float,
            'breakdown': {
                'stock_items': {...},
                'cocktails': {...}
            }
        }
    """
    general_revenue = Decimal(str(general_sales.get('revenue', 0)))
    general_cost = Decimal(str(general_sales.get('cost', 0)))
    general_count = int(general_sales.get('count', 0))
    
    cocktail_revenue = Decimal(str(cocktail_sales.get('revenue', 0)))
    cocktail_cost = Decimal(str(cocktail_sales.get('cost', 0)))
    cocktail_count = int(cocktail_sales.get('count', 0))
    
    # Calculate totals
    total_revenue = general_revenue + cocktail_revenue
    total_cost = general_cost + cocktail_cost
    total_count = general_count + cocktail_count
    profit = total_revenue - total_cost
    
    # Calculate GP%
    gp_percentage = 0.0
    if total_revenue > 0:
        gp_percentage = float((profit / total_revenue) * 100)
    
    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_count': total_count,
        'profit': profit,
        'gp_percentage': round(gp_percentage, 2),
        'breakdown': {
            'stock_items': {
                'revenue': general_revenue,
                'cost': general_cost,
                'count': general_count,
                'profit': general_revenue - general_cost
            },
            'cocktails': {
                'revenue': cocktail_revenue,
                'cost': cocktail_cost,
                'count': cocktail_count,
                'profit': cocktail_revenue - cocktail_cost
            }
        }
    }


def calculate_percentages(
    general_sales: Dict[str, Any],
    cocktail_sales: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate percentage breakdown of sales sources.
    
    Returns:
        {
            'stock_items_percentage': float,
            'cocktails_percentage': float,
            'stock_items_cost_percentage': float,
            'cocktails_cost_percentage': float
        }
    """
    general_revenue = Decimal(str(general_sales.get('revenue', 0)))
    cocktail_revenue = Decimal(str(cocktail_sales.get('revenue', 0)))
    total_revenue = general_revenue + cocktail_revenue
    
    general_cost = Decimal(str(general_sales.get('cost', 0)))
    cocktail_cost = Decimal(str(cocktail_sales.get('cost', 0)))
    total_cost = general_cost + cocktail_cost
    
    # Revenue percentages
    stock_pct = 0.0
    cocktail_pct = 0.0
    if total_revenue > 0:
        stock_pct = float((general_revenue / total_revenue) * 100)
        cocktail_pct = float((cocktail_revenue / total_revenue) * 100)
    
    # Cost percentages
    stock_cost_pct = 0.0
    cocktail_cost_pct = 0.0
    if total_cost > 0:
        stock_cost_pct = float((general_cost / total_cost) * 100)
        cocktail_cost_pct = float((cocktail_cost / total_cost) * 100)
    
    return {
        'stock_items_percentage': round(stock_pct, 2),
        'cocktails_percentage': round(cocktail_pct, 2),
        'stock_items_cost_percentage': round(stock_cost_pct, 2),
        'cocktails_cost_percentage': round(cocktail_cost_pct, 2)
    }


def analyze_trends(periods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze trends across multiple periods.
    
    Args:
        periods: List of period data, each containing:
            {
                'period_name': str,
                'stock_revenue': Decimal,
                'cocktail_revenue': Decimal,
                'stock_cost': Decimal,
                'cocktail_cost': Decimal
            }
    
    Returns:
        Trend analysis with growth rates and averages
    """
    if not periods:
        return {
            'trend': 'insufficient_data',
            'growth_rate': 0.0,
            'average_revenue': Decimal('0.00'),
            'average_cost': Decimal('0.00')
        }
    
    # Calculate totals for each period
    period_totals = []
    for period in periods:
        stock_rev = Decimal(str(period.get('stock_revenue', 0)))
        cocktail_rev = Decimal(str(period.get('cocktail_revenue', 0)))
        stock_cost = Decimal(str(period.get('stock_cost', 0)))
        cocktail_cost = Decimal(str(period.get('cocktail_cost', 0)))
        
        total_revenue = stock_rev + cocktail_rev
        total_cost = stock_cost + cocktail_cost
        
        period_totals.append({
            'name': period.get('period_name', ''),
            'revenue': total_revenue,
            'cost': total_cost,
            'profit': total_revenue - total_cost
        })
    
    # Calculate averages
    avg_revenue = sum(p['revenue'] for p in period_totals) / len(period_totals)
    avg_cost = sum(p['cost'] for p in period_totals) / len(period_totals)
    avg_profit = sum(p['profit'] for p in period_totals) / len(period_totals)
    
    # Calculate growth rate (first to last)
    growth_rate = 0.0
    trend = 'stable'
    
    if len(period_totals) >= 2:
        first_revenue = period_totals[0]['revenue']
        last_revenue = period_totals[-1]['revenue']
        
        if first_revenue > 0:
            growth_rate = float(
                ((last_revenue - first_revenue) / first_revenue) * 100
            )
            
            if growth_rate > 5:
                trend = 'increasing'
            elif growth_rate < -5:
                trend = 'decreasing'
            else:
                trend = 'stable'
    
    return {
        'trend': trend,
        'growth_rate': round(growth_rate, 2),
        'average_revenue': avg_revenue,
        'average_cost': avg_cost,
        'average_profit': avg_profit,
        'period_count': len(period_totals),
        'periods': period_totals
    }


def get_category_breakdown(
    period_data: Dict[str, Any],
    include_cocktails: bool = True
) -> Dict[str, Any]:
    """
    Get sales breakdown by category.
    
    Args:
        period_data: Period sales data containing category breakdowns
        include_cocktails: Whether to include cocktails as separate category
    
    Returns:
        {
            'stock_categories': {
                'D': {...},
                'B': {...},
                'S': {...},
                'W': {...},
                'M': {...}
            },
            'cocktails': {...},  # Only if include_cocktails=True
            'combined_total': Decimal
        }
    """
    result = {
        'stock_categories': {},
        'combined_total': Decimal('0.00')
    }
    
    # Stock categories
    stock_categories = period_data.get('stock_categories', {})
    total = Decimal('0.00')
    
    for category_code, data in stock_categories.items():
        revenue = Decimal(str(data.get('revenue', 0)))
        cost = Decimal(str(data.get('cost', 0)))
        
        result['stock_categories'][category_code] = {
            'name': data.get('name', category_code),
            'revenue': revenue,
            'cost': cost,
            'profit': revenue - cost,
            'count': data.get('count', 0)
        }
        total += revenue
    
    # Cocktails (separate category)
    if include_cocktails:
        cocktail_data = period_data.get('cocktails', {})
        cocktail_revenue = Decimal(str(cocktail_data.get('revenue', 0)))
        cocktail_cost = Decimal(str(cocktail_data.get('cost', 0)))
        
        result['cocktails'] = {
            'name': 'Cocktails',
            'revenue': cocktail_revenue,
            'cost': cocktail_cost,
            'profit': cocktail_revenue - cocktail_cost,
            'count': cocktail_data.get('count', 0)
        }
        total += cocktail_revenue
    
    result['combined_total'] = total
    
    return result


def calculate_profitability_metrics(
    revenue: Decimal,
    cost: Decimal
) -> Dict[str, float]:
    """
    Calculate profitability metrics from revenue and cost.
    
    Returns:
        {
            'gross_profit': Decimal,
            'gp_percentage': float,
            'markup_percentage': float,
            'pour_cost_percentage': float
        }
    """
    revenue_dec = Decimal(str(revenue))
    cost_dec = Decimal(str(cost))
    profit = revenue_dec - cost_dec
    
    gp_pct = 0.0
    markup_pct = 0.0
    pour_cost_pct = 0.0
    
    if revenue_dec > 0:
        gp_pct = float((profit / revenue_dec) * 100)
        pour_cost_pct = float((cost_dec / revenue_dec) * 100)
    
    if cost_dec > 0:
        markup_pct = float((profit / cost_dec) * 100)
    
    return {
        'gross_profit': profit,
        'gp_percentage': round(gp_pct, 2),
        'markup_percentage': round(markup_pct, 2),
        'pour_cost_percentage': round(pour_cost_pct, 2)
    }
