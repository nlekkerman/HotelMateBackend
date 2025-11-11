# Stock Tracker Export API Documentation

This document describes the PDF and Excel export endpoints for stocktakes and periods.

## Base URL Structure

All endpoints follow this pattern:
```
/api/stock-tracker/{hotel_identifier}/...
```

Where `{hotel_identifier}` is either the hotel's slug or subdomain.

---

## Stocktake Export Endpoints

### 1. Download Stocktake as PDF

**Two Access Methods:**

#### Method A: By ID
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-pdf/`

**Parameters:**
- `id` (path parameter): Stocktake ID

#### Method B: By Date Range
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/stocktakes/download-pdf/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Query Parameters:**
- `start_date` (required): Period start date (YYYY-MM-DD format)
- `end_date` (required): Period end date (YYYY-MM-DD format)

**Description:** Generates and downloads a formatted PDF report for a stocktake. Use the ID method when you know the stocktake ID, or use the date range method when you know the period dates (useful when the same month has multiple stocktakes with different IDs).

**Authentication:** Required

**Response:**
- **Content-Type:** `application/pdf`
- **File:** PDF document with filename format: `stocktake_{hotel_name}_{start_date}_to_{end_date}.pdf`

**PDF Contents:**
1. **Header**: Hotel name, period dates, status
2. **Summary**: Total items, expected/counted/variance values, COGS, Revenue, GP%, Pour Cost%
3. **Category Breakdown**: Totals grouped by category (D, B, S, W, M)
4. **Detailed Items**: All line items with opening, purchases, expected, counted, variance

**Example Requests:**
```bash
# By ID
GET /api/stock-tracker/my-hotel/stocktakes/42/download-pdf/

# By Date Range
GET /api/stock-tracker/my-hotel/stocktakes/download-pdf/?start_date=2024-11-01&end_date=2024-11-30
```

**Example Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="stocktake_My_Hotel_2024-11-01_to_2024-11-30.pdf"
```

**Error Responses (Date Method):**
- `400 Bad Request`: Missing or invalid date parameters
- `404 Not Found`: No stocktake found for specified date range

---

### 2. Download Stocktake as Excel

**Two Access Methods:**

#### Method A: By ID
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-excel/`

**Parameters:**
- `id` (path parameter): Stocktake ID

#### Method B: By Date Range
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/stocktakes/download-excel/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Query Parameters:**
- `start_date` (required): Period start date (YYYY-MM-DD format)
- `end_date` (required): Period end date (YYYY-MM-DD format)

**Description:** Generates and downloads an Excel workbook for a stocktake with multiple sheets. Use the ID method when you know the stocktake ID, or use the date range method when you know the period dates.

**Authentication:** Required

**Response:**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **File:** Excel workbook with filename format: `stocktake_{hotel_name}_{start_date}_to_{end_date}.xlsx`

**Excel Workbook Structure:**

#### Sheet 1: Summary
- Period information (dates, status, approval info)
- Summary totals (items, values, profitability metrics)
- Category breakdown table with totals

#### Sheet 2: All Items
- Complete list of all stocktake lines
- Columns: SKU, Name, Category, Opening Qty, Purchases, Expected Qty, Counted Full, Counted Partial, Counted Qty, Variance Qty, Expected Value, Counted Value, Variance Value

#### Sheet 3: Variance Report
- Only items with variance (non-zero difference)
- Columns: SKU, Name, Category, Expected Qty, Counted Qty, Variance Qty, Variance Value, % Variance
- Useful for identifying problem items

**Example Requests:**
```bash
# By ID
GET /api/stock-tracker/my-hotel/stocktakes/42/download-excel/

# By Date Range
GET /api/stock-tracker/my-hotel/stocktakes/download-excel/?start_date=2024-11-01&end_date=2024-11-30
```

**Example Response Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="stocktake_My_Hotel_2024-11-01_to_2024-11-30.xlsx"
```

**Error Responses (Date Method):**
- `400 Bad Request`: Missing or invalid date parameters
- `404 Not Found`: No stocktake found for specified date range

---

## Period Export Endpoints

### 3. Download Period as PDF

**Two Access Methods:**

#### Method A: By ID
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/periods/{id}/download-pdf/`

**Parameters:**
- `id` (path parameter): Period ID

#### Method B: By Date Range
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/periods/download-pdf/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Query Parameters:**
- `start_date` (required): Period start date (YYYY-MM-DD format)
- `end_date` (required): Period end date (YYYY-MM-DD format)
- `include_cocktails` (optional): Include cocktail sales data (default: `true`)

**Description:** Generates and downloads a formatted PDF report for a stock period. Use the ID method when you know the period ID, or use the date range method when you know the period dates (useful when the same month has multiple periods with different IDs).

**Authentication:** Required

**Response:**
- **Content-Type:** `application/pdf`
- **File:** PDF document with filename format: `period_{hotel_name}_{period_name}.pdf`

**PDF Contents:**
1. **Header**: Hotel name, period name, dates, type, status
2. **Summary**: Total items, closing stock value, cocktail sales (if included)
3. **Category Breakdown**: Stock value by category with percentages
4. **Detailed Snapshots**: All items grouped by category with full/partial units and values

**Example Requests:**
```bash
# By ID with cocktails (default)
GET /api/stock-tracker/my-hotel/periods/15/download-pdf/

# By ID without cocktails
GET /api/stock-tracker/my-hotel/periods/15/download-pdf/?include_cocktails=false

# By Date Range
GET /api/stock-tracker/my-hotel/periods/download-pdf/?start_date=2024-11-01&end_date=2024-11-30

# By Date Range without cocktails
GET /api/stock-tracker/my-hotel/periods/download-pdf/?start_date=2024-11-01&end_date=2024-11-30&include_cocktails=false
```

**Example Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="period_My_Hotel_November_2024.pdf"
```

**Error Responses (Date Method):**
- `400 Bad Request`: Missing or invalid date parameters
- `404 Not Found`: No period found for specified date range

---

### 4. Download Period as Excel

**Two Access Methods:**

#### Method A: By ID
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/periods/{id}/download-excel/`

**Parameters:**
- `id` (path parameter): Period ID

#### Method B: By Date Range
**Endpoint:** `GET /api/stock-tracker/{hotel_identifier}/periods/download-excel/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Query Parameters:**
- `start_date` (required): Period start date (YYYY-MM-DD format)
- `end_date` (required): Period end date (YYYY-MM-DD format)
- `include_cocktails` (optional): Include cocktail sales data (default: `true`)

**Description:** Generates and downloads an Excel workbook for a period with multiple sheets. Use the ID method when you know the period ID, or use the date range method when you know the period dates.

**Authentication:** Required

**Response:**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **File:** Excel workbook with filename format: `period_{hotel_name}_{period_name}.xlsx`

**Excel Workbook Structure:**

#### Sheet 1: Summary
- Period information (name, dates, type, status)
- Summary totals (items, closing value, cocktail data)
- Category breakdown with values and percentages

#### Sheet 2: Stock Snapshots
- All items with closing stock details
- Columns: SKU, Name, Category, Size, Full Units, Partial Units, Total Servings, Value

**Example Requests:**
```bash
# By ID with cocktails (default)
GET /api/stock-tracker/my-hotel/periods/15/download-excel/

# By ID without cocktails
GET /api/stock-tracker/my-hotel/periods/15/download-excel/?include_cocktails=false

# By Date Range
GET /api/stock-tracker/my-hotel/periods/download-excel/?start_date=2024-11-01&end_date=2024-11-30

# By Date Range without cocktails
GET /api/stock-tracker/my-hotel/periods/download-excel/?start_date=2024-11-01&end_date=2024-11-30&include_cocktails=false
```

**Example Response Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="period_My_Hotel_November_2024.xlsx"
```

**Error Responses (Date Method):**
- `400 Bad Request`: Missing or invalid date parameters
- `404 Not Found`: No period found for specified date range

---

## Frontend Integration Guide

### React/JavaScript Example

```javascript
// Function to download stocktake PDF
async function downloadStocktakePDF(hotelIdentifier, stocktakeId) {
  const url = `/api/stock-tracker/${hotelIdentifier}/stocktakes/${stocktakeId}/download-pdf/`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${yourAuthToken}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Download failed');
    }
    
    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1].replace(/"/g, '')
      : 'stocktake.pdf';
    
    // Create blob and trigger download
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
    
  } catch (error) {
    console.error('Download error:', error);
  }
}

// Function to download period Excel with options
async function downloadPeriodExcel(hotelIdentifier, periodId, includeCocktails = true) {
  const url = `/api/stock-tracker/${hotelIdentifier}/periods/${periodId}/download-excel/?include_cocktails=${includeCocktails}`;
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${yourAuthToken}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Download failed');
    }
    
    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1].replace(/"/g, '')
      : 'period.xlsx';
    
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
    
  } catch (error) {
    console.error('Download error:', error);
  }
}
```

### React Component Example

```jsx
import React from 'react';
import { Button } from '@/components/ui/button';
import { FileDown, FileSpreadsheet } from 'lucide-react';

function StocktakeDownloadButtons({ hotelIdentifier, stocktakeId }) {
  const [downloading, setDownloading] = React.useState(false);
  
  const handleDownload = async (format) => {
    setDownloading(true);
    
    const endpoint = format === 'pdf' ? 'download-pdf' : 'download-excel';
    const url = `/api/stock-tracker/${hotelIdentifier}/stocktakes/${stocktakeId}/${endpoint}/`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (!response.ok) throw new Error('Download failed');
      
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `stocktake.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download file');
    } finally {
      setDownloading(false);
    }
  };
  
  return (
    <div className="flex gap-2">
      <Button
        onClick={() => handleDownload('pdf')}
        disabled={downloading}
        variant="outline"
      >
        <FileDown className="mr-2 h-4 w-4" />
        Download PDF
      </Button>
      <Button
        onClick={() => handleDownload('excel')}
        disabled={downloading}
        variant="outline"
      >
        <FileSpreadsheet className="mr-2 h-4 w-4" />
        Download Excel
      </Button>
    </div>
  );
}

export default StocktakeDownloadButtons;
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "error": "Invalid parameters"
}
```

### 403 Forbidden
```json
{
  "error": "You do not have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "Stocktake not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to generate report"
}
```

---

## Notes

1. **Authentication Required**: All endpoints require valid authentication tokens
2. **File Sizes**: PDF files are typically 100KB-2MB, Excel files 50KB-5MB depending on data volume
3. **Generation Time**: Reports typically generate in 1-3 seconds
4. **Browser Compatibility**: Download functionality works in all modern browsers
5. **Mobile Support**: Downloads work on mobile devices with appropriate handlers
6. **Permissions**: Users must have view permission for the stocktake/period

---

## Rate Limiting

Standard API rate limits apply:
- 100 requests per minute per user
- 1000 requests per hour per user

---

## Support

For issues or questions:
- Backend API: Check Django logs for generation errors
- Frontend Integration: Verify authentication tokens and URL structure
- File Format Issues: Ensure browser supports PDF/Excel downloads

---

## Version History

- **v1.0** (November 2025): Initial release with PDF and Excel exports for stocktakes and periods
