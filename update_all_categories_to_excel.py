"""
Update ALL Categories to Match Excel Data - October 2025

This script updates:
- Bottled Beers (21 items) - Target: €2,288.46
- Spirits (126+ items) - Target: €11,063.66
- Wines (36+ items) - Target: €5,580.35
- Minerals & Syrups (47 items) - Target: €3,062.43

Run: python update_all_categories_to_excel.py
"""

import os
import sys
import django
from decimal import Decimal
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod, StockSnapshot
from hotel.models import Hotel


# ========== BOTTLED BEERS DATA ==========
EXCEL_BOTTLED = [
    {'sku': 'B0044', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('213.12')},
    {'sku': 'B0037', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('140.50')},
    {'sku': 'B0038', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('84.30')},
    {'sku': 'B0039', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('103.60')},
    {'sku': 'B0040', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('31.20')},
    {'sku': 'B0041', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('93.60')},
    {'sku': 'B0042', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('156.00')},
    {'sku': 'B0043', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('161.20')},
    {'sku': 'B0031', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('110.40')},
    {'sku': 'B0032', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('80.00')},
    {'sku': 'B0033', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.40')},
    {'sku': 'B0034', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('31.80')},
    {'sku': 'B0035', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('150.00')},
    {'sku': 'B0036', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('261.60')},
    {'sku': 'B0024', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('112.00')},
    {'sku': 'B0025', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('28.00')},
    {'sku': 'B0026', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('93.60')},
    {'sku': 'B0027', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('217.60')},
    {'sku': 'B0028', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('65.60')},
    {'sku': 'B0029', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('90.00')},
    {'sku': 'B0030', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('31.94')},
]

# ========== SPIRITS DATA ==========
EXCEL_SPIRITS = [
    {'sku': 'S0005', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0006', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0011', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('39.00')},
    {'sku': 'S0007', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0010', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0012', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0013', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0008', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0009', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0014', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0003', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('60.00')},
    {'sku': 'S0004', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('60.00')},
    {'sku': 'S0015', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0016', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('39.00')},
    {'sku': 'S0018', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0019', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0001', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('102.40')},
    {'sku': 'S0002', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0017', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0023', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0020', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0021', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0022', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0029', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('42.00')},
    {'sku': 'S0024', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0026', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('58.50')},
    {'sku': 'S0027', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0028', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0025', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0030', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0031', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0032', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0034', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('76.80')},
    {'sku': 'S0033', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0035', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0036', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('58.50')},
    {'sku': 'S0037', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0038', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('78.00')},
    {'sku': 'S0040', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0041', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0042', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0043', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('102.40')},
    {'sku': 'S0044', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0045', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0048', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0049', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0046', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0047', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('120.00')},
    {'sku': 'S0050', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0051', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0052', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0053', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0054', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0055', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0039', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0059', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0058', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0057', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0056', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0060', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0061', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0062', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0063', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0064', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0065', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0066', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0067', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0069', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0068', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0070', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('102.40')},
    {'sku': 'S0071', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0073', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0072', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0074', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0075', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0079', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0078', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0077', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0076', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0080', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('91.20')},
    {'sku': 'S0081', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('195.00')},
    {'sku': 'S0082', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0083', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0084', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0085', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0086', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('97.50')},
    {'sku': 'S0087', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0088', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('97.50')},
    {'sku': 'S0089', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0090', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0091', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0092', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0093', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('39.00')},
    {'sku': 'S0094', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('97.50')},
    {'sku': 'S0095', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0097', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0096', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0098', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0100', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0099', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('63.00')},
    {'sku': 'S0101', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0102', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('120.00')},
    {'sku': 'S0103', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('80.00')},
    {'sku': 'S0104', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0105', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('90.00')},
    {'sku': 'S0106', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0107', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0108', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0109', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0110', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('30.00')},
    {'sku': 'S0111', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.20')},
    {'sku': 'S0112', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('21.00')},
    {'sku': 'S0113', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('42.00')},
    {'sku': 'S0114', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.60')},
    {'sku': 'S0115', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0116', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('39.00')},
    {'sku': 'S0117', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0118', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0119', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0120', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0121', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('19.50')},
    {'sku': 'S0122', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.50')},
    {'sku': 'S0123', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('120.00')},
    {'sku': 'S0124', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('90.00')},
    {'sku': 'S0125', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('60.00')},
    {'sku': 'S0126', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('60.00')},
]

# ========== WINES DATA ==========
EXCEL_WINES = [
    {'sku': 'W0016', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('37.80')},
    {'sku': 'W0017', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('37.80')},
    {'sku': 'W0018', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('75.60')},
    {'sku': 'W0019', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('75.60')},
    {'sku': 'W0020', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('75.60')},
    {'sku': 'W0021', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('77.40')},
    {'sku': 'W0022', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('37.20')},
    {'sku': 'W0023', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('86.40')},
    {'sku': 'W0024', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('78.00')},
    {'sku': 'W0025', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('78.00')},
    {'sku': 'W0026', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('95.40')},
    {'sku': 'W0027', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('15.90')},
    {'sku': 'W0028', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('95.40')},
    {'sku': 'W0029', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('75.60')},
    {'sku': 'W0030', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('38.70')},
    {'sku': 'W0031', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('77.40')},
    {'sku': 'W0032', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('95.40')},
    {'sku': 'W0033', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('95.40')},
    {'sku': 'W0034', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('95.40')},
    {'sku': 'W0035', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('186.00')},
    {'sku': 'W0036', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('186.00')},
    {'sku': 'W0037', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('186.00')},
    {'sku': 'W0038', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('216.00')},
    {'sku': 'W0039', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('216.00')},
    {'sku': 'W0040', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('282.00')},
    {'sku': 'W0041', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('252.00')},
    {'sku': 'W0042', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.00')},
    {'sku': 'W0043', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('264.00')},
    {'sku': 'W0044', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('90.00')},
    {'sku': 'W0045', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('270.00')},
    {'sku': 'W0046', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('132.00')},
    {'sku': 'W0047', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('288.00')},
    {'sku': 'W0048', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('32.00')},
    {'sku': 'W0049', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('186.00')},
    {'sku': 'W0050', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('294.00')},
    {'sku': 'W0051', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('252.00')},
]

# ========== MINERALS & SYRUPS DATA ==========
EXCEL_MINERALS = [
    {'sku': 'M0001', 'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('196.80')},
    {'sku': 'M0002', 'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('157.95')},
    {'sku': 'M0003', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('61.20')},
    {'sku': 'M0004', 'full': Decimal('15.00'), 'partial': Decimal('0.00'), 'value': Decimal('229.50')},
    {'sku': 'M0005', 'full': Decimal('15.00'), 'partial': Decimal('0.00'), 'value': Decimal('231.00')},
    {'sku': 'M0006', 'full': Decimal('15.00'), 'partial': Decimal('0.00'), 'value': Decimal('231.00')},
    {'sku': 'M0007', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('80.00')},
    {'sku': 'M0008', 'full': Decimal('15.00'), 'partial': Decimal('0.00'), 'value': Decimal('231.00')},
    {'sku': 'M0009', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('92.40')},
    {'sku': 'M0010', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('154.00')},
    {'sku': 'M0011', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('154.00')},
    {'sku': 'M0012', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('154.00')},
    {'sku': 'M0013', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('144.00')},
    {'sku': 'M0014', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('72.00')},
    {'sku': 'M0015', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M0016', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('26.25')},
    {'sku': 'M0017', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0018', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0019', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0020', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0021', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0022', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0023', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0024', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0025', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0026', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0027', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0028', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0029', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0030', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0031', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0032', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0033', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0034', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0035', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0036', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0037', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0038', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0039', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0040', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0041', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0042', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0043', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0044', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0045', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0046', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
    {'sku': 'M0047', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('13.95')},
]


def update_category(category_code, category_name, data_list, expected_total):
    """Update a single category with Excel data"""
    print(f"\n{'='*60}")
    print(f"🔄 Updating {category_name}...")
    print(f"{'='*60}")
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
    
    updated_count = 0
    not_found = []
    total_value = Decimal('0.00')
    
    for item_data in data_list:
        sku = item_data['sku']
        try:
            item = StockItem.objects.get(hotel=hotel, sku=sku)
            
            snapshot, created = StockSnapshot.objects.update_or_create(
                hotel=hotel,
                item=item,
                period=period,
                defaults={
                    'closing_full_units': item_data['full'],
                    'closing_partial_units': item_data['partial'],
                    'closing_stock_value': item_data['value'],
                    'unit_cost': item.unit_cost,
                    'cost_per_serving': item.unit_cost / item.uom if item.uom > 0 else Decimal('0'),
                }
            )
            
            total_value += item_data['value']
            updated_count += 1
            status = "✅" if created else "✅"
            print(f"  {status} Updated: {sku} = €{item_data['value']}")
            
        except StockItem.DoesNotExist:
            not_found.append(sku)
            print(f"  ❌ Not found: {sku}")
    
    print(f"\n  📊 {category_name} Total: €{total_value:,.2f}")
    print(f"  📋 Excel Expected: €{expected_total:,.2f}")
    difference = total_value - expected_total
    print(f"  🔍 Difference: €{difference:,.2f}")
    
    if abs(difference) < Decimal('0.01'):
        print(f"  ✅ PERFECT MATCH!")
    elif abs(difference) < Decimal('1.00'):
        print(f"  ✅ CLOSE MATCH (within €1)")
    else:
        print(f"  ⚠️  Discrepancy detected")
    
    if not_found:
        print(f"\n  ⚠️  Items not found in database: {', '.join(not_found)}")
    
    print(f"\n  ✅ Updated {updated_count} items")
    
    return total_value


def main():
    print("=" * 60)
    print("UPDATE ALL CATEGORIES TO EXCEL - OCTOBER 2025")
    print("=" * 60)
    
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found!")
            return
        print(f"\n🏨 Hotel: {hotel.name}")
        
        period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
        print(f"📅 Period: {period.period_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Update all categories
    totals = {}
    
    totals['B'] = update_category('B', 'Bottled Beers', EXCEL_BOTTLED, Decimal('2288.46'))
    totals['S'] = update_category('S', 'Spirits', EXCEL_SPIRITS, Decimal('11063.66'))
    totals['W'] = update_category('W', 'Wines', EXCEL_WINES, Decimal('5580.35'))
    totals['M'] = update_category('M', 'Minerals & Syrups', EXCEL_MINERALS, Decimal('3062.43'))
    
    # Get draught total from database
    draught_snapshots = StockSnapshot.objects.filter(
        hotel=hotel,
        period=period,
        item__category__code='D'
    )
    totals['D'] = sum(s.closing_stock_value for s in draught_snapshots)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY - ALL CATEGORIES")
    print("=" * 60)
    
    print(f"\nDraught Beers:")
    print(f"  Database: €{totals['D']:,.2f}")
    print(f"  Excel:    €5,311.62")
    print(f"  Diff:     €{totals['D'] - Decimal('5311.62'):,.2f}")
    
    print(f"\nBottled Beers:")
    print(f"  Database: €{totals['B']:,.2f}")
    print(f"  Excel:    €2,288.46")
    print(f"  Diff:     €{totals['B'] - Decimal('2288.46'):,.2f}")
    
    print(f"\nSpirits:")
    print(f"  Database: €{totals['S']:,.2f}")
    print(f"  Excel:    €11,063.66")
    print(f"  Diff:     €{totals['S'] - Decimal('11063.66'):,.2f}")
    
    print(f"\nWines:")
    print(f"  Database: €{totals['W']:,.2f}")
    print(f"  Excel:    €5,580.35")
    print(f"  Diff:     €{totals['W'] - Decimal('5580.35'):,.2f}")
    
    print(f"\nMinerals & Syrups:")
    print(f"  Database: €{totals['M']:,.2f}")
    print(f"  Excel:    €3,062.43")
    print(f"  Diff:     €{totals['M'] - Decimal('3062.43'):,.2f}")
    
    grand_total = sum(totals.values())
    excel_grand_total = Decimal('27306.51')
    
    print(f"\n{'='*60}")
    print(f"GRAND TOTAL: €{grand_total:,.2f}")
    print(f"Excel Total: €{excel_grand_total:,.2f}")
    print(f"Difference:  €{grand_total - excel_grand_total:,.2f}")
    print(f"{'='*60}")
    
    if abs(grand_total - excel_grand_total) < Decimal('0.01'):
        print("\n🎉 SUCCESS! Database now matches Excel perfectly!")
    elif abs(grand_total - excel_grand_total) < Decimal('1.00'):
        print("\n✅ SUCCESS! Database matches Excel (within €1)")
    else:
        print(f"\n⚠️  Still {abs(grand_total - excel_grand_total):.2f} difference")


if __name__ == '__main__':
    main()
