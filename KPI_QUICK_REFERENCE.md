# 🎯 KPI ENDPOINT - QUICK REFERENCE

## THE ENDPOINT
```
GET /api/stock-tracker/{hotel_identifier}/kpi-summary/?period_ids=1,2,3
```
**`hotel_identifier`** = Hotel slug or subdomain (e.g., `carlton-hotel` or `carlton`)

## RESPONSE KEYS (Just Copy These!)

```javascript
// Stock Value
data.stock_value_metrics.total_current_value          // €45,320.50
data.stock_value_metrics.average_value                // €42,150.75
data.stock_value_metrics.trend.direction              // "increasing"
data.stock_value_metrics.trend.percentage             // 12.5
data.stock_value_metrics.period_values                // Array for charts

// Profitability
data.profitability_metrics.average_gp_percentage      // 68.5
data.profitability_metrics.average_pour_cost_percentage // 31.5
data.profitability_metrics.trend.direction            // "improving"
data.profitability_metrics.trend.change               // 4.8

// Category Performance
data.category_performance.top_by_value                // {category_name, total_value, ...}
data.category_performance.top_by_gp                   // {category_name, gp_percentage, ...}
data.category_performance.most_growth                 // {category_name, growth_percentage, ...}
data.category_performance.distribution                // Array for charts

// Inventory Health
data.inventory_health.overall_health_score            // 78 (0-100)
data.inventory_health.health_rating                   // "Good"
data.inventory_health.low_stock_count                 // 12
data.inventory_health.out_of_stock_count              // 3
data.inventory_health.overstocked_count               // 8
data.inventory_health.dead_stock_count                // 5
data.inventory_health.low_stock_items                 // Array of items
data.inventory_health.out_of_stock_items              // Array of item names

// Period Comparison (if 2+ periods)
data.period_comparison.total_movers_count             // 34
data.period_comparison.biggest_increases              // Array[5]
data.period_comparison.biggest_decreases              // Array[5]
data.period_comparison.overall_variance.percentage    // 8.5
data.period_comparison.overall_variance.direction     // "increase"

// Performance Score
data.performance_score.overall_score                  // 82 (0-100)
data.performance_score.rating                         // "Good"
data.performance_score.breakdown.profitability_score  // 85
data.performance_score.breakdown.stock_health_score   // 78
data.performance_score.breakdown.turnover_score       // 75
data.performance_score.breakdown.category_balance_score // 88
data.performance_score.breakdown.variance_control_score // 75
data.performance_score.improvement_areas              // Array of recommendations
data.performance_score.strengths                      // Array of strengths

// Additional Metrics
data.additional_metrics.total_items_count             // 123
data.additional_metrics.active_items_count            // 98
data.additional_metrics.inactive_items_count          // 25
data.additional_metrics.total_categories              // 8
data.additional_metrics.average_item_value            // 368.46
data.additional_metrics.purchase_activity.total_purchases // 135
data.additional_metrics.purchase_activity.average_per_period // 45.0
data.additional_metrics.purchase_activity.most_purchased_category // "Beer"
```

## COLOR CODING

```javascript
// Health Score Colors
if (score >= 90) return "green"    // Excellent
if (score >= 75) return "lightgreen" // Good
if (score >= 60) return "yellow"   // Fair
return "red"                        // Poor

// GP% Colors
if (gp >= 70) return "green"       // Excellent
if (gp >= 60) return "lightgreen"  // Good
if (gp >= 50) return "yellow"      // Fair
return "red"                        // Poor

// Trend Icons
if (direction === "increasing") return "↑ green"
if (direction === "decreasing") return "↓ red"
return "→ gray" // stable
```

## REACT COMPONENT TEMPLATE

```tsx
import { useEffect, useState } from 'react';

interface KPIData {
  stock_value_metrics: any;
  profitability_metrics: any;
  inventory_health: any;
  performance_score: any;
  // ... add others as needed
}

export const KPIDashboard = ({ hotelId, periodIds }: Props) => {
  const [data, setData] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch(`/api/stock-tracker/${hotelId}/kpi-summary/?period_ids=${periodIds.join(',')}`)
      .then(res => res.json())
      .then(result => {
        setData(result.data);
        setLoading(false);
      });
  }, [hotelId, periodIds]);
  
  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data</div>;
  
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Stock Value Card */}
      <Card>
        <h3>Stock Value</h3>
        <div className="text-3xl font-bold">
          €{data.stock_value_metrics.total_current_value.toLocaleString()}
        </div>
        <div className={getTrendColor(data.stock_value_metrics.trend.direction)}>
          {data.stock_value_metrics.trend.direction} {data.stock_value_metrics.trend.percentage}%
        </div>
      </Card>
      
      {/* Profitability Card */}
      <Card>
        <h3>Gross Profit</h3>
        <div className="text-3xl font-bold">
          {data.profitability_metrics.average_gp_percentage}%
        </div>
        <div className="text-sm">
          Pour Cost: {data.profitability_metrics.average_pour_cost_percentage}%
        </div>
      </Card>
      
      {/* Health Score Card */}
      <Card>
        <h3>Health Score</h3>
        <CircularGauge value={data.inventory_health.overall_health_score} max={100} />
        <Badge color={getHealthColor(data.inventory_health.health_rating)}>
          {data.inventory_health.health_rating}
        </Badge>
        <div className="mt-2 text-sm">
          ⚠️ {data.inventory_health.low_stock_count} low stock items
        </div>
      </Card>
      
      {/* Performance Score Card */}
      <Card className="col-span-2">
        <h3>Performance Score</h3>
        <div className="flex items-center gap-4">
          <div className="text-4xl font-bold">{data.performance_score.overall_score}</div>
          <Badge>{data.performance_score.rating}</Badge>
        </div>
        <div className="grid grid-cols-5 gap-2 mt-4">
          {Object.entries(data.performance_score.breakdown).map(([key, value]) => (
            <MiniBar key={key} label={key} value={value as number} />
          ))}
        </div>
      </Card>
      
      {/* More cards... */}
    </div>
  );
};
```

## FETCH EXAMPLES

### JavaScript
```javascript
// Use hotel slug or subdomain
const response = await fetch(
  `/api/stock-tracker/carlton-hotel/kpi-summary/?period_ids=1,2,3`
);
const { data } = await response.json();
console.log('Stock Value:', data.stock_value_metrics.total_current_value);
```

### Axios
```javascript
const { data } = await axios.get(
  `/api/stock-tracker/${hotelSlug}/kpi-summary/`,
  { params: { period_ids: '1,2,3' } }
);
```

### React Query
```javascript
const { data, isLoading } = useQuery(['kpi', periodIds], () =>
  fetch(`/api/stock-tracker/${hotelSlug}/kpi-summary/?period_ids=${periodIds}`)
    .then(res => res.json())
);
```

---

**Everything you need in one place!** 🎉
