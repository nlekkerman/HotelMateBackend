# KPI Summary API - Ready-to-Display Metrics

## 🎯 Purpose
**Single endpoint that calculates ALL KPI metrics on the backend.**  
Frontend just displays the numbers - **NO calculations needed**.

---

## 📍 Endpoint

```
GET /api/stock-tracker/<hotel_identifier>/kpi-summary/
```

**`hotel_identifier`** = Hotel slug OR subdomain (e.g., `carlton-hotel` or `carlton`)

### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_ids` | string | ✅ Yes | Comma-separated period IDs: `"1,2,3"` |

### Example Requests
```
GET /api/stock-tracker/carlton-hotel/kpi-summary/?period_ids=1,2,3
GET /api/stock-tracker/carlton/kpi-summary/?period_ids=1,2,3
```

---

## 📦 Response Structure

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
    "period_names": ["September 2024", "October 2024", "November 2024"],
    "date_range": {
      "from": "2024-09-01",
      "to": "2024-11-30"
    }
  }
}
```

---

## 📊 1. Stock Value Metrics

### What You Get
```json
{
  "stock_value_metrics": {
    "total_current_value": 45320.50,
    "average_value": 42150.75,
    "highest_period": {
      "period_id": 2,
      "period_name": "October 2024",
      "value": 48200.00,
      "date": "2024-10-31"
    },
    "lowest_period": {
      "period_id": 1,
      "period_name": "September 2024",
      "value": 38500.00,
      "date": "2024-09-30"
    },
    "trend": {
      "direction": "increasing",
      "percentage": 12.5
    },
    "period_values": [
      {"period_id": 1, "period_name": "Sep 2024", "value": 38500, "date": "2024-09-30"},
      {"period_id": 2, "period_name": "Oct 2024", "value": 48200, "date": "2024-10-31"}
    ]
  }
}
```

### Frontend Display
- **Big Number**: `total_current_value` → "€45,320.50"
- **Trend Arrow**: `trend.direction` → ↑ green if "increasing"
- **Trend %**: `trend.percentage` → "+12.5%"
- **Chart**: Use `period_values` array for sparkline/line chart

---

## 💰 2. Profitability Metrics

### What You Get
```json
{
  "profitability_metrics": {
    "average_gp_percentage": 68.5,
    "highest_gp_period": {
      "period_name": "October 2024",
      "gp_percentage": 72.3,
      "pour_cost": 27.7,
      "date": "2024-10-31"
    },
    "lowest_gp_period": {
      "period_name": "September 2024",
      "gp_percentage": 64.2,
      "pour_cost": 35.8,
      "date": "2024-09-30"
    },
    "average_pour_cost_percentage": 31.5,
    "trend": {
      "direction": "improving",
      "change": 4.8
    },
    "all_periods": [...]
  }
}
```

### Frontend Display
- **Big Number**: `average_gp_percentage` → "68.5%"
- **Color**: Green if > 70%, Yellow if 60-70%, Red if < 60%
- **Secondary**: `average_pour_cost_percentage` → "Pour Cost: 31.5%"
- **Trend**: `trend.direction` → "improving" badge

---

## 📂 3. Category Performance

### What You Get
```json
{
  "category_performance": {
    "top_by_value": {
      "category_code": "S",
      "category_name": "Spirits",
      "total_value": 18500.00,
      "item_count": 45,
      "average_gp_percentage": 70.2,
      "percentage_of_total": 40.8
    },
    "top_by_gp": {
      "category_code": "B",
      "category_name": "Beer",
      "total_value": 12300.00,
      "item_count": 32,
      "average_gp_percentage": 74.2,
      "percentage_of_total": 27.1
    },
    "most_growth": {
      "category_code": "W",
      "category_name": "Wine",
      "growth_percentage": 22.5,
      "value_increase": 3200.00
    },
    "distribution": [
      {
        "category_code": "S",
        "category_name": "Spirits",
        "total_value": 18500.00,
        "item_count": 45,
        "average_gp_percentage": 70.2,
        "percentage_of_total": 40.8
      }
    ]
  }
}
```

### Frontend Display
- **Top Category**: `top_by_value.category_name` → "Spirits - €18,500"
- **Donut Chart**: Use `distribution` array
- **Growth Badge**: `most_growth` → "Wine +22.5%"

---

## 🏥 4. Inventory Health

### What You Get
```json
{
  "inventory_health": {
    "low_stock_count": 12,
    "low_stock_items": [
      {
        "item_name": "Vodka 1L",
        "sku": "S001",
        "current_quantity": 2.0,
        "par_level": 10.0,
        "percentage_of_par": 20.0
      }
    ],
    "out_of_stock_count": 3,
    "out_of_stock_items": ["Gin 750ml", "Tequila 1L", "Rum 750ml"],
    "overstocked_count": 8,
    "overstocked_items": [...],
    "dead_stock_count": 5,
    "dead_stock_items": ["Vermouth 750ml", "Aperol 1L"],
    "overall_health_score": 78,
    "health_rating": "Good",
    "total_items_analyzed": 123
  }
}
```

### Frontend Display
- **Gauge Chart**: `overall_health_score` → 78/100
- **Rating Badge**: `health_rating` → "Good" (color-coded)
- **Alert Count**: `low_stock_count` + `out_of_stock_count` → "15 items need attention"
- **Colors**: 
  - 90-100 = Green "Excellent"
  - 75-89 = Light Green "Good"
  - 60-74 = Yellow "Fair"
  - 0-59 = Red "Poor"

---

## 🔄 5. Period Comparison (only if 2+ periods)

### What You Get
```json
{
  "period_comparison": {
    "periods_compared": ["September 2024", "October 2024"],
    "total_movers_count": 34,
    "threshold_percentage": 10,
    "biggest_increases": [
      {
        "item_name": "Premium Vodka 1L",
        "sku": "S045",
        "category": "Spirits",
        "previous_value": 500.00,
        "current_value": 850.00,
        "change": 350.00,
        "percentage_change": 70.0
      }
    ],
    "biggest_decreases": [
      {
        "item_name": "House Wine 750ml",
        "sku": "W012",
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

### Frontend Display
- **Movers Badge**: `total_movers_count` → "34 items changed >10%"
- **Top 3 Increases**: List from `biggest_increases`
- **Top 3 Decreases**: List from `biggest_decreases`
- **Category Changes**: Bar chart from `categories_with_most_change`

---

## 🎯 6. Performance Score

### What You Get
```json
{
  "performance_score": {
    "overall_score": 82,
    "rating": "Good",
    "breakdown": {
      "profitability_score": 85,
      "stock_health_score": 78,
      "turnover_score": 75,
      "category_balance_score": 88,
      "variance_control_score": 75
    },
    "improvement_areas": [
      {
        "area": "Stock Health",
        "current_score": 78,
        "priority": "medium",
        "recommendation": "Address 12 low stock items and 3 out of stock items"
      }
    ],
    "strengths": [
      "Excellent profitability margins",
      "Well-balanced category distribution"
    ]
  }
}
```

### Frontend Display
- **Big Circular Gauge**: `overall_score` → 82/100
- **Rating**: `rating` → "Good" badge
- **Component Bars**: Use `breakdown` for mini bar charts
- **Action Cards**: `improvement_areas` → List with priority badges
- **Strengths**: `strengths` → ✓ Green checkmarks

---

## 📈 7. Additional Metrics

### What You Get
```json
{
  "additional_metrics": {
    "total_items_count": 123,
    "active_items_count": 98,
    "inactive_items_count": 25,
    "total_categories": 8,
    "average_item_value": 368.46,
    "purchase_activity": {
      "total_purchases": 135,
      "average_per_period": 45.0,
      "most_purchased_category": "Beer"
    }
  }
}
```

### Frontend Display
- **Stats Grid**:
  - Total Items: `total_items_count`
  - Active: `active_items_count`
  - Avg Value: `average_item_value`
  - Purchases: `purchase_activity.total_purchases`

---

## 🎨 Frontend Implementation Example

### React/TypeScript Component

```typescript
interface KPIData {
  stock_value_metrics: StockValueMetrics;
  profitability_metrics: ProfitabilityMetrics;
  // ... other types
}

const KPIDashboard = () => {
  const [kpiData, setKpiData] = useState<KPIData | null>(null);
  
  useEffect(() => {
    fetch(`/api/stock-tracker/${hotelId}/kpi-summary/?period_ids=1,2,3`)
      .then(res => res.json())
      .then(data => setKpiData(data.data));
  }, []);
  
  if (!kpiData) return <Loading />;
  
  return (
    <div className="kpi-dashboard">
      {/* Stock Value Card */}
      <Card>
        <h3>Stock Value</h3>
        <BigNumber>
          €{kpiData.stock_value_metrics.total_current_value.toLocaleString()}
        </BigNumber>
        <Trend 
          direction={kpiData.stock_value_metrics.trend.direction}
          percentage={kpiData.stock_value_metrics.trend.percentage}
        />
      </Card>
      
      {/* Profitability Card */}
      <Card>
        <h3>Gross Profit %</h3>
        <BigNumber color={getGPColor(kpiData.profitability_metrics.average_gp_percentage)}>
          {kpiData.profitability_metrics.average_gp_percentage}%
        </BigNumber>
      </Card>
      
      {/* Health Score Card */}
      <Card>
        <h3>Inventory Health</h3>
        <GaugeChart value={kpiData.inventory_health.overall_health_score} />
        <Badge color={getHealthColor(kpiData.inventory_health.health_rating)}>
          {kpiData.inventory_health.health_rating}
        </Badge>
      </Card>
      
      {/* More cards... */}
    </div>
  );
};
```

---

## ✅ Testing

### Test with cURL
```bash
# Use hotel slug or subdomain
curl -X GET "http://localhost:8000/api/stock-tracker/carlton-hotel/kpi-summary/?period_ids=1,2,3" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Or with subdomain
curl -X GET "http://localhost:8000/api/stock-tracker/carlton/kpi-summary/?period_ids=1,2,3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test with Postman
1. **Method**: GET
2. **URL**: `http://localhost:8000/api/stock-tracker/<hotel_slug_or_subdomain>/kpi-summary/`
3. **Params**: `period_ids` = `1,2,3`
4. **Headers**: `Authorization: Bearer YOUR_TOKEN`

---

## 🚀 Benefits

### ✅ Frontend Benefits
- **No calculations** - just display the numbers
- **Single API call** - all KPIs in one request
- **Ready-to-render** - no data transformation needed
- **Type-safe** - consistent response structure

### ✅ Backend Benefits
- **Centralized logic** - all calculations in one place
- **Optimized queries** - efficient database access
- **Easy to maintain** - single source of truth
- **Scalable** - can add more metrics easily

---

## 📝 Notes

### Performance
- Response time: ~500ms for 3 periods with 100+ items
- Cached snapshots used for fast calculation
- Optimized queries with select_related/prefetch_related

### Error Handling
- Returns 400 if `period_ids` missing or invalid
- Returns 404 if no periods found
- All metrics gracefully handle missing data

### Null Values
- If data not available: returns `null`
- Frontend should handle null checks
- Example: `profitability_score` is `null` if no stocktakes exist

---

## 🔗 Related Endpoints

- **Get Periods**: `GET /api/stock-tracker/<hotel_identifier>/periods/`
- **Period Detail**: `GET /api/stock-tracker/<hotel_identifier>/periods/<id>/`
- **Stocktakes**: `GET /api/stock-tracker/<hotel_identifier>/stocktakes/`

---

**Last Updated**: 2024-11-10  
**Version**: 1.0
