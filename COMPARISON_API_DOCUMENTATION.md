# Period Comparison & Analytics API Documentation

## Overview
Enhanced comparison endpoints supporting multi-period analysis for frontend charts and visualizations. All endpoints require **closed periods only**.

Base URL: `/stock_tracker/<hotel_identifier>/compare/`

---

## 1. Compare Categories
**Endpoint:** `GET /compare/categories/`

Compare aggregated category data across **2 or more periods**.

### Query Parameters
- `periods` (required): Comma-separated period IDs (e.g., `1,2,3,4`)

### Example Request
```
GET /stock_tracker/my-hotel/compare/categories/?periods=1,2,3
```

### Response
```json
{
  "periods": [
    {
      "id": 1,
      "name": "September 2024",
      "start_date": "2024-09-01",
      "end_date": "2024-09-30",
      "is_closed": true
    },
    {
      "id": 2,
      "name": "October 2024",
      "start_date": "2024-10-01",
      "end_date": "2024-10-31",
      "is_closed": true
    }
  ],
  "categories": [
    {
      "code": "S",
      "name": "Spirits",
      "periods_data": [
        {
          "period_id": 1,
          "period_name": "September 2024",
          "total_value": 15000.00,
          "item_count": 25,
          "purchases": 8000.00,
          "waste": 500.00,
          "waste_percentage": 6.25
        },
        {
          "period_id": 2,
          "period_name": "October 2024",
          "total_value": 17000.00,
          "item_count": 27,
          "purchases": 9000.00,
          "waste": 450.00,
          "waste_percentage": 5.00
        }
      ],
      "overall_change": {
        "value_change": 2000.00,
        "value_percentage": 13.33,
        "waste_improvement": 1.25
      }
    }
  ],
  "summary": {
    "total_value_change": 5000.00,
    "total_value_percentage": 10.50,
    "best_performing_category": "S",
    "worst_performing_category": "B",
    "periods_compared": 2
  }
}
```

### Frontend Use Cases
- **Pie Charts**: Category distribution per period
- **Stacked Bar Charts**: Category values across periods
- **Line Charts**: Category trends over time

---

## 2. Top Movers
**Endpoint:** `GET /compare/top-movers/`

Identify biggest value changes between **two periods**.

### Query Parameters
- `period1` (required): First period ID
- `period2` (required): Second period ID
- `limit` (optional): Number of results (default: 10)

### Example Request
```
GET /stock_tracker/my-hotel/compare/top-movers/?period1=1&period2=2&limit=10
```

### Response
```json
{
  "period1": {
    "id": 1,
    "name": "September 2024",
    "start_date": "2024-09-01",
    "end_date": "2024-09-30"
  },
  "period2": {
    "id": 2,
    "name": "October 2024",
    "start_date": "2024-10-01",
    "end_date": "2024-10-31"
  },
  "biggest_increases": [
    {
      "item_id": 123,
      "sku": "BEV001",
      "name": "Premium Vodka 1L",
      "category": "S",
      "period1_value": 1000.00,
      "period2_value": 2500.00,
      "absolute_change": 1500.00,
      "percentage_change": 150.00,
      "reason": "significant_change"
    }
  ],
  "biggest_decreases": [
    {
      "item_id": 456,
      "sku": "BEV002",
      "name": "House Wine",
      "category": "W",
      "period1_value": 3000.00,
      "period2_value": 1500.00,
      "absolute_change": -1500.00,
      "percentage_change": -50.00,
      "reason": "major_reduction"
    }
  ],
  "new_items": [
    {
      "item_id": 789,
      "sku": "NEW001",
      "name": "New Product",
      "category": "S",
      "value": 500.00
    }
  ],
  "discontinued_items": [
    {
      "item_id": 321,
      "sku": "OLD001",
      "name": "Discontinued Item",
      "category": "B",
      "last_value": 300.00
    }
  ]
}
```

### Reason Values
- `significant_change`: >100% change
- `stock_buildup`: 50-100% increase
- `increased_stock`: 20-50% increase
- `major_reduction`: <-50% decrease
- `decreased_stock`: -20 to -50% decrease
- `normal_variance`: <20% change

### Frontend Use Cases
- **Alert Cards**: Show items needing attention
- **Bar Charts**: Top 10 increases/decreases
- **Tables**: Sortable list of changes

---

## 3. Cost Analysis
**Endpoint:** `GET /compare/cost-analysis/`

Detailed cost breakdown between **two periods**.

### Query Parameters
- `period1` (required): First period ID
- `period2` (required): Second period ID

### Example Request
```
GET /stock_tracker/my-hotel/compare/cost-analysis/?period1=1&period2=2
```

### Response
```json
{
  "period1": {
    "id": 1,
    "name": "September 2024",
    "opening_stock_value": 25000.00,
    "purchases": 15000.00,
    "closing_stock_value": 28000.00,
    "theoretical_usage": 12000.00,
    "waste_cost": 1000.00,
    "transfer_net": 200.00,
    "adjustments": 0.00,
    "actual_cogs": 13200.00
  },
  "period2": {
    "id": 2,
    "name": "October 2024",
    "opening_stock_value": 28000.00,
    "purchases": 18000.00,
    "closing_stock_value": 30000.00,
    "theoretical_usage": 16000.00,
    "waste_cost": 1200.00,
    "transfer_net": -150.00,
    "adjustments": 0.00,
    "actual_cogs": 17350.00
  },
  "comparison": {
    "cogs_change": 4150.00,
    "cogs_percentage": 31.44,
    "waste_trend": "increasing",
    "waste_change": 200.00,
    "efficiency_rating": 7.5,
    "waste_p1_percentage": 6.67,
    "waste_p2_percentage": 6.67
  },
  "waterfall_data": [
    {
      "label": "Opening Stock",
      "value": 28000.00
    },
    {
      "label": "Purchases",
      "value": 18000.00
    },
    {
      "label": "Waste",
      "value": -1200.00
    },
    {
      "label": "Transfer Net",
      "value": -150.00
    },
    {
      "label": "Adjustments",
      "value": 0.00
    },
    {
      "label": "Closing Stock",
      "value": -30000.00
    },
    {
      "label": "Usage/COGS",
      "value": 17350.00
    }
  ]
}
```

### Frontend Use Cases
- **Waterfall Chart**: Cost flow visualization
- **Metric Cards**: Key financial indicators
- **Comparison Table**: Side-by-side period comparison

---

## 4. Trend Analysis
**Endpoint:** `GET /compare/trend-analysis/`

Multi-period trend analysis (**2+ periods**).

### Query Parameters
- `periods` (required): Comma-separated period IDs (e.g., `1,2,3,4,5`)
- `category` (optional): Filter by category code (e.g., `S`, `W`, `B`)
- `items` (optional): Comma-separated item IDs (e.g., `123,456,789`)

### Example Request
```
GET /stock_tracker/my-hotel/compare/trend-analysis/?periods=1,2,3,4&category=S
```

### Response
```json
{
  "periods": [
    {
      "id": 1,
      "name": "September 2024",
      "start_date": "2024-09-01",
      "end_date": "2024-09-30"
    },
    {
      "id": 2,
      "name": "October 2024",
      "start_date": "2024-10-01",
      "end_date": "2024-10-31"
    }
  ],
  "items": [
    {
      "item_id": 123,
      "sku": "BEV001",
      "name": "Premium Vodka",
      "category": "S",
      "trend_data": [
        {
          "period_id": 1,
          "value": 1500.00,
          "servings": 150.00,
          "waste": 50.00
        },
        {
          "period_id": 2,
          "value": 1750.00,
          "servings": 175.00,
          "waste": 45.00
        }
      ],
      "trend_direction": "increasing",
      "average_value": 1616.67,
      "volatility": "low"
    }
  ],
  "filters": {
    "category": "S",
    "item_count": 25
  }
}
```

### Trend Direction Values
- `increasing`: Upward trend
- `decreasing`: Downward trend
- `stable`: No significant change

### Volatility Values
- `low`: CV < 15%
- `medium`: CV 15-30%
- `high`: CV > 30%

### Frontend Use Cases
- **Line Charts**: Multi-period trends
- **Area Charts**: Stacked category trends
- **Sparklines**: Individual item mini-trends

---

## 5. Variance Heatmap
**Endpoint:** `GET /compare/variance-heatmap/`

Heatmap data showing variance across categories and periods.

### Query Parameters
- `periods` (required): Comma-separated period IDs (minimum 2)

### Example Request
```
GET /stock_tracker/my-hotel/compare/variance-heatmap/?periods=1,2,3,4
```

### Response
```json
{
  "periods": ["Sept 2024", "Oct 2024", "Nov 2024", "Dec 2024"],
  "categories": ["D", "B", "S", "W", "M"],
  "heatmap_data": [
    [0, 0, 5.5, "low"],
    [0, 1, -12.3, "medium"],
    [0, 2, 35.7, "high"],
    [1, 0, 8.2, "low"],
    [1, 1, 25.4, "high"]
  ],
  "color_scale": {
    "low": "#90EE90",
    "medium": "#FFD700",
    "high": "#FF6347"
  }
}
```

### Heatmap Data Format
Each entry: `[period_index, category_index, variance_percentage, severity]`

### Severity Levels
- `low`: <15% variance
- `medium`: 15-30% variance
- `high`: >30% variance

### Frontend Use Cases
- **Heatmap Chart**: Color-coded variance matrix
- **Pattern Analysis**: Identify trends and anomalies

---

## 6. Performance Scorecard
**Endpoint:** `GET /compare/performance-scorecard/`

KPI comparison between **two periods**.

### Query Parameters
- `period1` (required): First period ID
- `period2` (required): Second period ID

### Example Request
```
GET /stock_tracker/my-hotel/compare/performance-scorecard/?period1=1&period2=2
```

### Response
```json
{
  "period1": {
    "id": 1,
    "name": "September 2024"
  },
  "period2": {
    "id": 2,
    "name": "October 2024"
  },
  "overall_score": {
    "period1": 75,
    "period2": 82,
    "improvement": 7
  },
  "metrics": [
    {
      "name": "Stock Value Management",
      "period1_score": 80,
      "period2_score": 85,
      "weight": 0.3,
      "status": "improved"
    },
    {
      "name": "Waste Control",
      "period1_score": 70,
      "period2_score": 78,
      "weight": 0.25,
      "status": "improved"
    },
    {
      "name": "Stock Turnover",
      "period1_score": 75,
      "period2_score": 80,
      "weight": 0.25,
      "status": "improved"
    },
    {
      "name": "Variance Control",
      "period1_score": 72,
      "period2_score": 85,
      "weight": 0.2,
      "status": "significantly_improved"
    }
  ],
  "radar_chart_data": {
    "labels": ["Value Mgmt", "Waste Control", "Turnover", "Variance"],
    "period1": [80, 70, 75, 72],
    "period2": [85, 78, 80, 85]
  }
}
```

### Status Values
- `significantly_improved`: +10 or more points
- `improved`: +1 to +9 points
- `unchanged`: 0 points change
- `slightly_declined`: -1 to -9 points
- `declined`: -10 or more points

### Frontend Use Cases
- **Radar Chart**: Multi-dimensional performance
- **Score Cards**: Individual metric displays
- **Progress Bars**: Visual improvement indicators

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "periods parameter required (comma-separated IDs)"
}
```

### 404 Not Found
```json
{
  "error": "One or more periods not found or not closed"
}
```

---

## Notes

1. **All endpoints require closed periods only** - Open periods cannot be compared
2. **Multi-period support**: Most endpoints support 2+ periods for richer analysis
3. **Optimized for frontend**: Response structures designed for chart libraries
4. **Performance**: Uses aggregation queries for efficient data retrieval
5. **Filtering**: Some endpoints support category/item filtering for focused analysis
