# API Profitability Metrics Update

## Overview
This update introduces new profitability metrics to the backend API for both Stocktake (period summary) and Sale (transaction) objects. These metrics are now pre-calculated and exposed in API responses, allowing the frontend to display them directly with minimal processing.

## New Fields Exposed
For both Stocktake and Sale objects, the following fields are now available:

- `total_cogs`: Total cost of goods sold for the period or sale
- `total_revenue`: Total sales revenue for the period or sale
- `gross_profit_percentage`: Gross Profit % (GP%)
- `pour_cost_percentage`: Pour Cost %

## Example API Response
```json
{
  "total_cogs": 1234.56,
  "total_revenue": 2345.67,
  "gross_profit_percentage": 47.36,
  "pour_cost_percentage": 52.64
}
```

## Frontend Integration Guide
- **No calculations required:** All metrics are pre-calculated by the backend. Use the values as provided.
- **Display directly:** Map these fields from the API response to your UI components (tables, charts, summaries).
- **Field names:** Use the exact field names above for consistency.

## What to Avoid
- Do not re-calculate GP% or Pour Cost % on the frontend.
- Do not sum or derive COGS/Revenue from line items unless you need custom breakdowns.

## Next Steps for Frontend
1. Update your data models to include the new fields.
2. Map and display these metrics wherever profitability information is needed.
3. Test API responses to ensure the new fields are present and accurate.

## Questions?
Contact the backend team for further details or if you need sample API calls or UI mapping examples.
