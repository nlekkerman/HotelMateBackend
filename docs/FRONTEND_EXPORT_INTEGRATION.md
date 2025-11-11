# Frontend Integration Guide - PDF/Excel Exports

## 🎯 Overview

The backend now supports PDF and Excel exports for **stocktakes** and **periods**. All endpoints are ready to integrate with your frontend.

---

## 📍 API Endpoints (All Include hotel_identifier)

### Stocktake Downloads

```
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-pdf/
GET /api/stock-tracker/{hotel_identifier}/stocktakes/{id}/download-excel/
```

### Period Downloads

```
GET /api/stock-tracker/{hotel_identifier}/periods/{id}/download-pdf/?include_cocktails=true
GET /api/stock-tracker/{hotel_identifier}/periods/{id}/download-excel/?include_cocktails=true
```

**Note:** `include_cocktails` parameter is optional (default: `true`)

---

## 🚀 Quick Start Example

```javascript
// Download stocktake PDF
const downloadStocktakePDF = async (hotelId, stocktakeId) => {
  const url = `/api/stock-tracker/${hotelId}/stocktakes/${stocktakeId}/download-pdf/`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  const blob = await response.blob();
  const filename = response.headers
    .get('Content-Disposition')
    .split('filename=')[1]
    .replace(/"/g, '');
  
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
};
```

---

## 📦 What's Included in Exports

### Stocktake Reports (PDF & Excel)
- ✅ Period information (dates, status, approval details)
- ✅ Summary totals (expected, counted, variance)
- ✅ Profitability metrics (COGS, Revenue, GP%, Pour Cost%)
- ✅ Category breakdown (D, B, S, W, M)
- ✅ All line items with full details
- ✅ Variance report (Excel only - separate sheet)

### Period Reports (PDF & Excel)
- ✅ Period overview (name, dates, type, status)
- ✅ Stock snapshots with closing values
- ✅ Category analysis with percentages
- ✅ Cocktail sales data (optional)
- ✅ Stock value breakdown by category

---

## 🎨 UI Integration Suggestions

### 1. Download Buttons in Stocktake Detail View

```jsx
<div className="flex gap-2">
  <Button onClick={() => downloadPDF('stocktake', id)}>
    <FileDown className="mr-2" />
    Download PDF
  </Button>
  <Button onClick={() => downloadExcel('stocktake', id)}>
    <FileSpreadsheet className="mr-2" />
    Download Excel
  </Button>
</div>
```

### 2. Download Options in Period List

```jsx
<DropdownMenu>
  <DropdownMenuTrigger>
    <Download /> Export
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem onClick={() => downloadPDF('period', id)}>
      PDF Report
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => downloadExcel('period', id)}>
      Excel Workbook
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### 3. Bulk Export Option

```jsx
// In period list with checkboxes
<Button 
  onClick={() => downloadMultiplePeriods(selectedIds)}
  disabled={selectedIds.length === 0}
>
  Export Selected ({selectedIds.length})
</Button>
```

---

## 🔧 Recommended Features to Add

### Loading States
```jsx
const [downloading, setDownloading] = useState(false);

// Show spinner while downloading
{downloading && <Spinner />}
```

### Success/Error Notifications
```jsx
try {
  await downloadFile();
  toast.success('File downloaded successfully');
} catch (error) {
  toast.error('Failed to download file');
}
```

### Download History Tracking
```jsx
// Store in localStorage or state
const downloadHistory = [
  { type: 'stocktake', id: 42, date: '2024-11-11', format: 'pdf' },
  // ...
];
```

---

## 📱 Mobile Considerations

- Files download to device's download folder
- Consider showing "File downloaded" message
- Add option to share/open file directly
- Test on iOS Safari and Android Chrome

---

## 🐛 Error Handling

### Common Errors

```javascript
if (response.status === 404) {
  // Stocktake/Period not found
  toast.error('Resource not found');
}

if (response.status === 403) {
  // Permission denied
  toast.error('You do not have permission to download this file');
}

if (response.status === 500) {
  // Server error
  toast.error('Failed to generate report. Please try again.');
}
```

---

## ✅ Testing Checklist

- [ ] Download stocktake PDF
- [ ] Download stocktake Excel
- [ ] Download period PDF (with cocktails)
- [ ] Download period PDF (without cocktails)
- [ ] Download period Excel (with cocktails)
- [ ] Download period Excel (without cocktails)
- [ ] Test on mobile devices
- [ ] Test error handling (404, 403, 500)
- [ ] Verify filenames are correct
- [ ] Check file opens correctly

---

## 📚 Full Documentation

See `docs/EXPORT_API_DOCUMENTATION.md` for:
- Complete API reference
- Response format details
- Advanced examples
- React component templates

---

## 🎉 Ready to Use!

All backend endpoints are **LIVE** and ready for integration. The URLs follow the standard pattern with `hotel_identifier` included.

**Example URLs:**
- `/api/stock-tracker/my-hotel/stocktakes/42/download-pdf/`
- `/api/stock-tracker/my-hotel/periods/15/download-excel/`

Just add download buttons to your UI and start testing! 🚀
