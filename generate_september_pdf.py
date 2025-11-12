"""
Generate updated September PDF with Wine data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from stock_tracker.utils.pdf_generator import generate_stocktake_pdf
from hotel.models import Hotel

hotel = Hotel.objects.first()

# Get September stocktake
stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
)

print("=" * 80)
print("GENERATING SEPTEMBER PDF WITH UPDATED WINE DATA")
print("=" * 80)
print()
print(f"Stocktake #{stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print()

# Generate PDF
pdf_buffer = generate_stocktake_pdf(stocktake)

# Save to file
output_path = 'september_stocktake_with_wine.pdf'
with open(output_path, 'wb') as f:
    f.write(pdf_buffer.getvalue())

print(f"✅ PDF saved to: {output_path}")
print()
print("Check the Wine category - it should now show €4,466.14")
print("instead of €0.00")
print()
print("=" * 80)
