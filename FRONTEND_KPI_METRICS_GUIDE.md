# KPI Metrics Implementation Guide

## Overview
This document outlines the comprehensive KPI (Key Performance Indicator) metrics system for the stock analytics dashboard. The backend will calculate and provide these metrics, and the frontend will display them in intuitive summary cards.

---

## 1. Stock Value Metrics

### Purpose
Track the overall value and trends of inventory across periods.

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Total Stock Value** | Current or latest period total inventory value | Currency | €45,320.50 |
| **Average Stock Value** | Mean value across all selected periods | Currency | €42,150.75 |
| **Period with Highest Value** | Period name/date with maximum stock value | String + Currency | "October 2024 - €48,200" |
| **Period with Lowest Value** | Period name/date with minimum stock value | String + Currency | "September 2024 - €38,500" |
| **Trend Direction** | Stock value trend indicator | Enum | "increasing" / "decreasing" / "stable" |
| **Trend Percentage** | Percentage change over time | Percentage | +12.5% or -8.3% |

### Backend Response Structure
```json
{
  "stock_value_metrics": {
    "total_current_value": 45320.50,
    "average_value": 42150.75,
    "highest_period": {
      "period_name": "October 2024",
      "value": 48200.00,
      "date": "2024-10-31"
    },
    "lowest_period": {
      "period_name": "September 2024",
      "value": 38500.00,
      "date": "2024-09-30"
    },
    "trend": {
      "direction": "increasing",
      "percentage": 12.5,
      "description": "Stock value has increased by 12.5% over the selected period"
    }
  }
}
```

---

## 2. Profitability Metrics

### Purpose
Measure financial performance and profit margins.

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Average GP%** | Average Gross Profit percentage across periods | Percentage | 68.5% |
| **Period with Highest GP%** | Best performing period by profit margin | String + Percentage | "October 2024 - 72.3%" |
| **Period with Lowest GP%** | Lowest performing period by profit margin | String + Percentage | "August 2024 - 64.2%" |
| **Average Markup %** | Average markup percentage | Percentage | 185.5% |
| **Average Pour Cost %** | Average cost as percentage of selling price | Percentage | 31.5% |
| **Profitability Trend** | Trend indicator for profitability | Enum | "improving" / "declining" / "stable" |

### Backend Response Structure
```json
{
  "profitability_metrics": {
    "average_gp_percentage": 68.5,
    "highest_gp_period": {
      "period_name": "October 2024",
      "gp_percentage": 72.3,
      "date": "2024-10-31"
    },
    "lowest_gp_period": {
      "period_name": "August 2024",
      "gp_percentage": 64.2,
      "date": "2024-08-31"
    },
    "average_markup_percentage": 185.5,
    "average_pour_cost_percentage": 31.5,
    "trend": {
      "direction": "improving",
      "change": 4.8,
      "description": "Profitability has improved by 4.8 percentage points"
    }
  }
}
```

---

## 3. Category Performance

### Purpose
Identify top performing categories and their distribution.

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Top Category by Value** | Category with highest total value | String + Currency | "Spirits - €18,500" |
| **Top Category by GP%** | Category with best profit margin | String + Percentage | "Beer - 74.2%" |
| **Category with Most Growth** | Category with highest growth rate | String + Percentage | "Wine - +22.5%" |
| **Category Distribution** | Breakdown of value by category | Array | See structure below |

### Backend Response Structure
```json
{
  "category_performance": {
    "top_by_value": {
      "category_name": "Spirits",
      "total_value": 18500.00,
      "percentage_of_total": 40.8
    },
    "top_by_gp": {
      "category_name": "Beer",
      "gp_percentage": 74.2,
      "total_value": 12300.00
    },
    "most_growth": {
      "category_name": "Wine",
      "growth_percentage": 22.5,
      "value_increase": 3200.00
    },
    "distribution": [
      {
        "category_name": "Spirits",
        "value": 18500.00,
        "percentage": 40.8,
        "item_count": 45
      },
      {
        "category_name": "Beer",
        "value": 12300.00,
        "percentage": 27.1,
        "item_count": 32
      },
      {
        "category_name": "Wine",
        "value": 10200.00,
        "percentage": 22.5,
        "item_count": 28
      },
      {
        "category_name": "Soft Drinks",
        "value": 4320.50,
        "percentage": 9.6,
        "item_count": 18
      }
    ]
  }
}
```

---

## 4. Inventory Health

### Purpose
Monitor stock levels and identify inventory issues.

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Low Stock Items** | Count of items below par level | Integer | 12 items |
| **Out of Stock Items** | Count of items with zero quantity | Integer | 3 items |
| **Overstocked Items** | Items significantly above par (>150%) | Integer | 8 items |
| **Stock Turnover Rate** | Average days to turn over inventory | Days/Ratio | 15 days |
| **Dead Stock Count** | Items with no movement in period | Integer | 5 items |
| **Health Score** | Overall inventory health (0-100) | Integer | 78 |

### Backend Response Structure
```json
{
  "inventory_health": {
    "low_stock_count": 12,
    "low_stock_items": [
      {
        "item_name": "Vodka 1L",
        "current_quantity": 2,
        "par_level": 10,
        "percentage_of_par": 20
      }
    ],
    "out_of_stock_count": 3,
    "out_of_stock_items": ["Gin 750ml", "Tequila 1L", "Rum 750ml"],
    "overstocked_count": 8,
    "overstocked_items": [
      {
        "item_name": "Whiskey 1L",
        "current_quantity": 30,
        "par_level": 15,
        "percentage_of_par": 200
      }
    ],
    "stock_turnover": {
      "average_days": 15,
      "turnover_ratio": 24.3,
      "status": "healthy"
    },
    "dead_stock_count": 5,
    "dead_stock_items": ["Vermouth 750ml", "Aperol 1L"],
    "overall_health_score": 78,
    "health_rating": "Good"
  }
}
```

---

## 5. Period Comparison

### Purpose
Compare inventory changes between periods (requires 2+ periods selected).

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Total Movers Count** | Items with significant changes | Integer | 34 items |
| **Biggest Increases** | Top 3-5 items with largest increases | Array | See structure |
| **Biggest Decreases** | Top 3-5 items with largest decreases | Array | See structure |
| **Categories with Most Change** | Categories with highest variance | Array | See structure |
| **Period-over-Period Variance** | Overall variance percentage | Percentage | +8.5% |

### Backend Response Structure
```json
{
  "period_comparison": {
    "periods_compared": ["September 2024", "October 2024"],
    "total_movers_count": 34,
    "threshold_percentage": 10,
    "biggest_increases": [
      {
        "item_name": "Premium Vodka 1L",
        "category": "Spirits",
        "previous_value": 500.00,
        "current_value": 850.00,
        "change": 350.00,
        "percentage_change": 70.0
      },
      {
        "item_name": "Craft Beer Pack",
        "category": "Beer",
        "previous_value": 300.00,
        "current_value": 480.00,
        "change": 180.00,
        "percentage_change": 60.0
      }
    ],
    "biggest_decreases": [
      {
        "item_name": "House Wine 750ml",
        "category": "Wine",
        "previous_value": 600.00,
        "current_value": 350.00,
        "change": -250.00,
        "percentage_change": -41.7
      }
    ],
    "categories_with_most_change": [
      {
        "category_name": "Spirits",
        "change": 2500.00,
        "percentage_change": 15.2,
        "direction": "increase"
      },
      {
        "category_name": "Wine",
        "change": -800.00,
        "percentage_change": -8.5,
        "direction": "decrease"
      }
    ],
    "overall_variance": {
      "percentage": 8.5,
      "direction": "increase",
      "value_change": 3850.00
    }
  }
}
```

---

## 6. Efficiency/Performance Score

### Purpose
Provide an overall assessment of inventory management performance.

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Overall Score** | Composite efficiency score (0-100) | Integer | 82 |
| **Score Breakdown** | Individual component scores | Object | See structure |
| **Rating** | Qualitative assessment | Enum | "Excellent" / "Good" / "Fair" / "Poor" |
| **Key Improvement Areas** | Actionable insights | Array | See structure |

### Backend Response Structure
```json
{
  "performance_score": {
    "overall_score": 82,
    "rating": "Good",
    "breakdown": {
      "profitability_score": 85,
      "stock_health_score": 78,
      "turnover_score": 80,
      "category_balance_score": 88,
      "variance_control_score": 75
    },
    "improvement_areas": [
      {
        "area": "Stock Health",
        "current_score": 78,
        "priority": "medium",
        "recommendation": "Reduce low stock items from 12 to under 5",
        "potential_impact": "Could improve overall score to 86"
      },
      {
        "area": "Variance Control",
        "current_score": 75,
        "priority": "high",
        "recommendation": "Address items with significant variance",
        "potential_impact": "Better inventory predictability"
      }
    ],
    "strengths": [
      "Excellent category balance",
      "Strong profitability margins",
      "Good stock turnover rate"
    ]
  }
}
```

---

## 7. Additional Useful Metrics

### Purpose
Provide supplementary information for comprehensive analysis.

### Metrics Required

| Metric | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **Total Items Count** | Total number of inventory items | Integer | 123 items |
| **Active Items Count** | Items with recent movement | Integer | 98 items |
| **Total Categories** | Number of distinct categories | Integer | 8 categories |
| **Average Item Value** | Mean value per item | Currency | €368.46 |
| **Variance from Expected** | Deviation from expected levels | Percentage | -3.2% |
| **Waste/Shrinkage %** | Percentage of inventory lost | Percentage | 2.1% |
| **Purchase Frequency** | Average purchases per period | Integer | 45 purchases |

### Backend Response Structure
```json
{
  "additional_metrics": {
    "total_items_count": 123,
    "active_items_count": 98,
    "inactive_items_count": 25,
    "total_categories": 8,
    "average_item_value": 368.46,
    "variance_from_expected": {
      "percentage": -3.2,
      "direction": "below",
      "description": "Stock levels are 3.2% below expected targets"
    },
    "waste_shrinkage": {
      "percentage": 2.1,
      "total_value": 950.00,
      "status": "acceptable"
    },
    "purchase_activity": {
      "frequency": 45,
      "average_order_value": 1250.00,
      "most_purchased_category": "Beer"
    }
  }
}
```

---

## Complete API Endpoint Structure

### Endpoint
```
GET /api/stock-tracker/analytics/kpi-summary/
```

### Query Parameters
```
?period_ids=1,2,3&hotel_id=1
```

### Full Response Example
```json
{
  "success": true,
  "data": {
    "stock_value_metrics": { ... },
    "profitability_metrics": { ... },
    "category_performance": { ... },
    "inventory_health": { ... },
    "period_comparison": { ... },
    "performance_score": { ... },
    "additional_metrics": { ... }
  },
  "meta": {
    "periods_analyzed": 3,
    "date_range": {
      "from": "2024-08-01",
      "to": "2024-10-31"
    },
    "calculation_timestamp": "2024-11-10T14:30:00Z"
  }
}
```

---

## Frontend Display Recommendations

### KPI Card Components

#### 1. **Stock Value Card**
- **Primary Metric**: Total Current Value (large, prominent)
- **Secondary**: Average Value
- **Trend Indicator**: Arrow with percentage
- **Mini Chart**: Sparkline of value over periods

#### 2. **Profitability Card**
- **Primary Metric**: Average GP% (large, colored by performance)
- **Secondary**: Pour Cost %
- **Comparison**: Best vs Worst period
- **Trend Indicator**: Arrow with direction

#### 3. **Category Performance Card**
- **Primary**: Top Category by Value
- **Visual**: Donut chart with distribution
- **Highlight**: Category with most growth
- **List**: Top 3 categories

#### 4. **Inventory Health Card**
- **Primary**: Health Score (0-100 with gauge)
- **Alerts**: Low stock, Out of stock counts
- **Secondary**: Turnover rate
- **Status Indicators**: Color-coded badges

#### 5. **Period Comparison Card** (if 2+ periods)
- **Primary**: Overall Variance %
- **Lists**: Top increases/decreases
- **Visual**: Bar chart of category changes
- **Movers Count**: Total items changed

#### 6. **Performance Score Card**
- **Primary**: Overall Score (large, circular gauge)
- **Rating**: Excellent/Good/Fair/Poor badge
- **Breakdown**: Mini bars for each component
- **Insights**: Key improvement areas (expandable)

---

## Color Coding Guidelines

### Stock Health
- 🟢 **Green (Healthy)**: 80-100 score, Low alerts
- 🟡 **Yellow (Warning)**: 60-79 score, Moderate alerts
- 🔴 **Red (Critical)**: 0-59 score, High alerts

### Trend Indicators
- 🟢 **Positive**: Increasing value/profitability
- 🔴 **Negative**: Decreasing value/profitability
- ⚪ **Neutral**: Stable (within ±2%)

### Profitability Ranges
- 🟢 **Excellent**: GP% > 70%
- 🟢 **Good**: GP% 60-70%
- 🟡 **Fair**: GP% 50-60%
- 🔴 **Poor**: GP% < 50%

---

## Implementation Priority

### Phase 1 (Essential)
1. Stock Value Metrics
2. Profitability Metrics
3. Inventory Health (basic)

### Phase 2 (Important)
4. Category Performance
5. Additional Metrics

### Phase 3 (Advanced)
6. Period Comparison
7. Performance Score with AI insights

---

## Backend Calculation Notes

### Considerations
1. **Performance**: Cache calculations for frequently accessed periods
2. **Accuracy**: Use decimal precision for currency (2 decimal places)
3. **Null Handling**: Return sensible defaults for incomplete data
4. **Permissions**: Respect hotel-specific data isolation
5. **Date Ranges**: Support flexible period selection
6. **Thresholds**: Make configurable (e.g., "significant change" = 10%)

### Suggested Django Implementation
```python
# In stock_tracker/views_analytics.py or similar

class KPISummaryView(APIView):
    """
    GET /api/stock-tracker/analytics/kpi-summary/
    Query params: period_ids (comma-separated), hotel_id
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        period_ids = request.GET.get('period_ids', '').split(',')
        hotel_id = request.GET.get('hotel_id')
        
        # Calculate all metrics
        stock_metrics = self.calculate_stock_value_metrics(period_ids)
        profitability = self.calculate_profitability_metrics(period_ids)
        category_performance = self.calculate_category_performance(period_ids)
        inventory_health = self.calculate_inventory_health(period_ids)
        period_comparison = self.calculate_period_comparison(period_ids)
        performance_score = self.calculate_performance_score(period_ids)
        additional = self.calculate_additional_metrics(period_ids)
        
        return Response({
            'success': True,
            'data': {
                'stock_value_metrics': stock_metrics,
                'profitability_metrics': profitability,
                'category_performance': category_performance,
                'inventory_health': inventory_health,
                'period_comparison': period_comparison,
                'performance_score': performance_score,
                'additional_metrics': additional
            }
        })
```

---

## Testing Checklist

### Backend Tests
- [ ] Single period calculation
- [ ] Multiple periods calculation
- [ ] Edge cases (empty periods, no data)
- [ ] Permission checks
- [ ] Performance with large datasets
- [ ] Decimal precision accuracy

### Frontend Tests
- [ ] Display with 1 period
- [ ] Display with multiple periods
- [ ] Responsive layout
- [ ] Color coding accuracy
- [ ] Trend indicators
- [ ] Loading states
- [ ] Error handling

---

## Questions for Backend Team

1. **Calculation Frequency**: Should metrics be calculated in real-time or pre-calculated and cached?
2. **Threshold Configuration**: Should thresholds (low stock, significant change, etc.) be configurable per hotel?
3. **Historical Data**: How far back should trend analysis go?
4. **Performance**: Expected response time for calculations?
5. **Permissions**: Any special permission considerations beyond standard hotel access?

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2024-11-10 | 1.0 | Initial documentation created |

---

## Related Documentation
- `FRONTEND_ANALYTICS_IMPLEMENTATION.md` - Overall analytics feature guide
- `FRONTEND_STOCKTAKE_PERIOD_GUIDE.md` - Period management
- Stock Tracker API documentation

---

## Support & Questions
For questions about this implementation, contact the development team or refer to the main project documentation.
