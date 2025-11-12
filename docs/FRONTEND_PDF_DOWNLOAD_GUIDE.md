# Frontend PDF Download Integration Guide

## Overview

This guide explains how to integrate PDF download functionality for stocktakes and period reports in the frontend application.

---

## API Endpoints

### 1. Download Stocktake PDF Only

**Endpoint:**
```
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-pdf/
```

**Example:**
```
GET /api/stock-tracker/hotel-killarney/stocktakes/17/download-pdf/
```

**Response:**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="Stocktake_17_HotelKillarney_2025-09-30.pdf"`
- **Body:** Binary PDF data

**Status Support:**
- ✅ Works with **DRAFT** stocktakes
- ✅ Works with **APPROVED** stocktakes
- ✅ Works with **IN_PROGRESS** stocktakes
- No restrictions based on status

**What it includes:**
- Stocktake header (hotel name, dates, status)
- Summary totals (expected value, counted value, variance)
- Category totals table
- Detailed line items grouped by category
- Variance highlighting (red for negative, green for positive)

---

### 2. Download Period Closing Stock PDF Only

**Endpoint (by ID):**
```
GET /api/stock-tracker/{hotel_identifier}/periods/{id}/download-pdf/
```

**Example:**
```
GET /api/stock-tracker/hotel-killarney/periods/9/download-pdf/
```

**Alternative (by date filters):**
```
GET /api/stock-tracker/{hotel_identifier}/periods/download-pdf/?year=2025&month=9
```

**Response:**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="ClosingStock_September_2025_HotelKillarney.pdf"`
- **Body:** Binary PDF data

**What it includes:**
- Period header (hotel name, date range)
- Closing stock value summary
- Category breakdown with percentages
- Detailed closing stock by item (SKU, name, category, quantities, value)

---

### 3. Download Combined Report (Stocktake + Period)

**Endpoint:**
```
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-combined-pdf/
```

**Example:**
```
GET /api/stock-tracker/hotel-killarney/stocktakes/17/download-combined-pdf/
```

**With optional cocktail data:**
```
GET /api/stock-tracker/hotel-killarney/stocktakes/17/download-combined-pdf/?include_cocktails=true
```

**Response:**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="Combined_Report_17_September_2025.pdf"`
- **Body:** Binary PDF data

**What it includes:**

**Part 1: Stocktake Report**
- Hotel and date information
- Status and approval details
- Summary totals (expected, counted, variance)
- Profitability metrics (COGS, Revenue, GP%, Pour Cost%)
- Category summary table

**Part 2: Period Closing Stock Report**
- Period information
- Closing stock value summary
- Category breakdown with percentages
- Detailed item-by-item closing stock

---

## Excel Downloads (Alternative Format)

Replace `/download-pdf/` with `/download-excel/` for Excel format:

**Stocktake Excel:**
```
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-excel/
```

**Period Excel:**
```
GET /api/stock-tracker/{hotel_identifier}/periods/{id}/download-excel/
```

**Response:**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Body:** Excel file with multiple sheets

---

## Frontend Implementation

### React/TypeScript Implementation

#### Download Stocktake PDF

```typescript
const downloadStocktakePDF = async (hotelSlug: string, stocktakeId: number) => {
  try {
    const response = await fetch(
      `/api/stock-tracker/${hotelSlug}/stocktakes/${stocktakeId}/download-pdf/`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Stocktake_${stocktakeId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading stocktake PDF:', error);
    throw error;
  }
};
```

#### Download Period PDF

```typescript
const downloadPeriodPDF = async (hotelSlug: string, periodId: number) => {
  try {
    const response = await fetch(
      `/api/stock-tracker/${hotelSlug}/periods/${periodId}/download-pdf/`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Period_${periodId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading period PDF:', error);
    throw error;
  }
};
```

#### Download Combined Report

```typescript
const downloadCombinedPDF = async (
  hotelSlug: string,
  stocktakeId: number,
  includeCocktails: boolean = false
) => {
  try {
    const queryString = includeCocktails ? '?include_cocktails=true' : '';
    const response = await fetch(
      `/api/stock-tracker/${hotelSlug}/stocktakes/${stocktakeId}/download-combined-pdf/${queryString}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Combined_Report_${stocktakeId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading combined PDF:', error);
    throw error;
  }
};
```

---

### React Component Example

```tsx
import React, { useState } from 'react';

interface DownloadButtonsProps {
  hotelSlug: string;
  stocktakeId: number;
  periodId: number;
}

const DownloadButtons: React.FC<DownloadButtonsProps> = ({
  hotelSlug,
  stocktakeId,
  periodId,
}) => {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async (
    type: 'stocktake' | 'period' | 'combined',
    format: 'pdf' | 'excel' = 'pdf'
  ) => {
    setLoading(type);
    setError(null);

    try {
      let url = '';
      let filename = '';

      switch (type) {
        case 'stocktake':
          url = `/api/stock-tracker/${hotelSlug}/stocktakes/${stocktakeId}/download-${format}/`;
          filename = `Stocktake_${stocktakeId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
          break;
        case 'period':
          url = `/api/stock-tracker/${hotelSlug}/periods/${periodId}/download-${format}/`;
          filename = `Period_${periodId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
          break;
        case 'combined':
          url = `/api/stock-tracker/${hotelSlug}/stocktakes/${stocktakeId}/download-combined-${format}/`;
          filename = `Combined_${stocktakeId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
          break;
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to download: ${response.statusText}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message);
      console.error('Download error:', err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="download-buttons">
      <h3>Download Reports</h3>
      
      {error && (
        <div className="error-message" style={{ color: 'red', marginBottom: '10px' }}>
          Error: {error}
        </div>
      )}

      <div className="button-group">
        <button
          onClick={() => handleDownload('stocktake', 'pdf')}
          disabled={loading !== null}
        >
          {loading === 'stocktake' ? 'Downloading...' : '📄 Download Stocktake PDF'}
        </button>

        <button
          onClick={() => handleDownload('period', 'pdf')}
          disabled={loading !== null}
        >
          {loading === 'period' ? 'Downloading...' : '📊 Download Period PDF'}
        </button>

        <button
          onClick={() => handleDownload('combined', 'pdf')}
          disabled={loading !== null}
        >
          {loading === 'combined' ? 'Downloading...' : '📑 Download Combined Report'}
        </button>
      </div>

      <div className="button-group" style={{ marginTop: '10px' }}>
        <small>Excel format:</small>
        <button
          onClick={() => handleDownload('stocktake', 'excel')}
          disabled={loading !== null}
          style={{ fontSize: '12px' }}
        >
          📊 Stocktake Excel
        </button>
        <button
          onClick={() => handleDownload('period', 'excel')}
          disabled={loading !== null}
          style={{ fontSize: '12px' }}
        >
          📊 Period Excel
        </button>
      </div>
    </div>
  );
};

export default DownloadButtons;
```

---

## Error Handling

### Comprehensive Error Handling

```typescript
const downloadWithErrorHandling = async (
  url: string,
  filename: string
): Promise<void> => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    // Handle specific status codes
    if (response.status === 401) {
      throw new Error('Authentication required. Please log in again.');
    }

    if (response.status === 403) {
      throw new Error('You do not have permission to download this report.');
    }

    if (response.status === 404) {
      throw new Error('Report not found.');
    }

    if (response.status === 500) {
      throw new Error('Server error. Please try again later.');
    }

    if (!response.ok) {
      throw new Error(`Download failed with status: ${response.status}`);
    }

    // Check content type
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/pdf') && 
        !contentType?.includes('spreadsheet')) {
      throw new Error('Invalid file type received');
    }

    // Download the file
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    }, 100);

  } catch (error: any) {
    console.error('Download error:', error);
    
    // User-friendly error messages
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Network error. Please check your connection.');
    }
    
    throw error;
  }
};
```

---

## Using Axios (Alternative)

If you prefer using Axios instead of fetch:

```typescript
import axios from 'axios';

const downloadPDFWithAxios = async (
  hotelSlug: string,
  stocktakeId: number
) => {
  try {
    const response = await axios.get(
      `/api/stock-tracker/${hotelSlug}/stocktakes/${stocktakeId}/download-pdf/`,
      {
        responseType: 'blob',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Stocktake_${stocktakeId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Download error:', error);
    throw error;
  }
};
```

---

## Important Notes

### 1. Authentication
All endpoints require a valid authentication token in the `Authorization` header.

### 2. Response Format
- **PDF downloads:** Binary data with `Content-Type: application/pdf`
- **Excel downloads:** Binary data with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### 3. File Size
- Typical PDF size: 50-500KB depending on data volume
- Excel files are generally larger (100KB-2MB)

### 4. Browser Compatibility
The blob download approach works in:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

### 5. Loading States
Always show a loading indicator during download to improve UX:
```typescript
const [isDownloading, setIsDownloading] = useState(false);

// In your download function:
setIsDownloading(true);
try {
  await downloadPDF();
} finally {
  setIsDownloading(false);
}
```

### 6. Memory Management
Always revoke blob URLs after download to prevent memory leaks:
```typescript
window.URL.revokeObjectURL(url);
```

### 7. Stocktake Status
PDFs can be downloaded for stocktakes in **any status**:
- **DRAFT** - Can download while still editing
- **IN_PROGRESS** - Can download during counting
- **APPROVED** - Can download finalized stocktakes

No restrictions or permissions required based on status. The PDF will display the current status in the header.

---

## Testing Checklist

- [ ] Test stocktake PDF download
- [ ] Test period PDF download  
- [ ] Test combined report download
- [ ] Test with `include_cocktails=true` parameter
- [ ] Test Excel format downloads
- [ ] Test error handling (404, 403, 500)
- [ ] Test with expired token (401)
- [ ] Test loading states
- [ ] Test on different browsers
- [ ] Test on mobile devices
- [ ] Verify correct filenames
- [ ] Verify file content is accurate

---

## Common Issues & Solutions

### Issue: Download starts but file is corrupted
**Solution:** Ensure `responseType: 'blob'` is set (if using Axios) or blob is created properly from fetch response.

### Issue: Nothing happens when clicking download
**Solution:** Check browser console for errors. Verify authentication token is valid.

### Issue: PDF opens in browser instead of downloading
**Solution:** This is browser default behavior. Users can save from browser PDF viewer, or ensure `Content-Disposition: attachment` is set in backend response.

### Issue: Large files fail to download
**Solution:** Implement progress tracking and consider streaming for very large files.

---

## Support

For backend API issues or questions, contact the backend team or refer to:
- `docs/EXPORT_API_DOCUMENTATION.md`
- `docs/COMBINED_REPORT_IMPLEMENTATION.md`
