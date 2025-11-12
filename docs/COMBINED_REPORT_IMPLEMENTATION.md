# Combined Report Endpoint - Implementation Summary

## ✅ What Was Created

### New Combined PDF Generator
**File:** `stock_tracker/utils/combined_pdf_generator.py`

Generates a single PDF containing:
- **Part 1: Stocktake Report** - Opening, Purchases, Expected, Counted, Variance
- **Part 2: Period Closing Stock Report** - Closing stock values, category breakdown

### New API Endpoint
**Function:** `StocktakeViewSet.download_combined_pdf()`

## 📋 API Usage

### Access Method 1: By ID
```
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-combined-pdf/
```

### Access Method 2: By Date Range
```
GET /api/stock-tracker/{hotel_identifier}/stocktakes/download-combined-pdf/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

### Query Parameters
- `start_date` (optional for ID method, required for date method): Period start date
- `end_date` (optional for ID method, required for date method): Period end date
- `include_cocktails` (optional): Include cocktail data in period section (default: true)

## 📄 PDF Structure

### Page 1: Stocktake Data
- **Header**: Hotel name, period dates, status, approval info
- **Summary**: Total items, expected/counted/variance values, COGS, Revenue, GP%, Pour Cost%
- **Category Totals**: Breakdown by category (Draught Beer, Bottled Beer, Spirits, Wine, Minerals)

### Page 2+: Period Data
- **Header**: Period name, dates, type, status
- **Summary**: Total items, closing stock value, cocktail sales (if included)
- **Category Breakdown**: Items, value, and percentage by category
- **Closing Stock Details**: First 50 items with SKU, name, quantities, and values

## 🔧 How It Works

1. **Finds Stocktake**: By ID or date range
2. **Finds Matching Period**: Searches for period with same start/end dates
3. **Generates Combined PDF**: Merges both reports into one document
4. **Returns File**: Single PDF download with both datasets

## ⚠️ Important Notes

- **Requires Matching Dates**: Period must exist with exact same start_date and end_date as stocktake
- **Error Handling**: Returns 404 if either stocktake or period not found
- **File Size**: Period section shows first 50 items (use Excel for complete list)

## 🧪 Testing

Run the test script:
```bash
python test_downloads.py
```

The script will test both access methods and save the combined PDF to `test_downloads_output/`

## 💡 Frontend Integration Example

```javascript
// Download combined report by ID
const downloadCombinedReport = async (stocktakeId) => {
  const response = await fetch(
    `/api/stock-tracker/${hotelSlug}/stocktakes/${stocktakeId}/download-combined-pdf/`,
    {
      headers: { 'Authorization': `Token ${token}` }
    }
  );
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `combined_report_${stocktakeId}.pdf`;
  a.click();
};

// Download combined report by date
const downloadCombinedReportByDate = async (startDate, endDate) => {
  const response = await fetch(
    `/api/stock-tracker/${hotelSlug}/stocktakes/download-combined-pdf/?start_date=${startDate}&end_date=${endDate}`,
    {
      headers: { 'Authorization': `Token ${token}` }
    }
  );
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `combined_report_${startDate}_to_${endDate}.pdf`;
  a.click();
};
```

## ✅ Benefits

1. **Single Download**: One file instead of two separate downloads
2. **Complete Picture**: Both variance analysis (stocktake) and closing stock (period) together
3. **Flexible Access**: Use ID when known, or dates for intuitive access
4. **Professional Format**: Multi-page PDF with clear section separation
5. **Same Date Range**: Ensures stocktake and period data match perfectly

## 🎯 Next Steps

1. Test the endpoint with your data
2. Update frontend to use the new combined endpoint
3. Optionally create a combined Excel version if needed
