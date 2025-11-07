"""
Update ALL Categories with CORRECT SKUs from Excel - October 2025

This uses the actual SKUs that exist in the database.
"""

import os
import sys
import django
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod, StockSnapshot
from hotel.models import Hotel


# ========== BOTTLED BEERS (Correct SKUs) ==========
EXCEL_BOTTLED = [
    {'sku': 'B0070', 'full': Decimal('0.00'), 'partial': Decimal('113.00'), 'value': Decimal('110.65')},
    {'sku': 'B0075', 'full': Decimal('0.00'), 'partial': Decimal('121.00'), 'value': Decimal('209.63')},
    {'sku': 'B0085', 'full': Decimal('0.00'), 'partial': Decimal('181.00'), 'value': Decimal('416.30')},
    {'sku': 'B0095', 'full': Decimal('0.00'), 'partial': Decimal('74.00'), 'value': Decimal('87.44')},
    {'sku': 'B0101', 'full': Decimal('0.00'), 'partial': Decimal('85.00'), 'value': Decimal('97.40')},
    {'sku': 'B0012', 'full': Decimal('0.00'), 'partial': Decimal('69.00'), 'value': Decimal('81.65')},
    {'sku': 'B1036', 'full': Decimal('0.00'), 'partial': Decimal('37.00'), 'value': Decimal('93.98')},
    {'sku': 'B1022', 'full': Decimal('0.00'), 'partial': Decimal('26.00'), 'value': Decimal('30.33')},
    {'sku': 'B2055', 'full': Decimal('0.00'), 'partial': Decimal('54.00'), 'value': Decimal('45.00')},
    {'sku': 'B0140', 'full': Decimal('0.00'), 'partial': Decimal('125.00'), 'value': Decimal('143.23')},
    {'sku': 'B11', 'full': Decimal('0.00'), 'partial': Decimal('16.00'), 'value': Decimal('41.23')},
    {'sku': 'B14', 'full': Decimal('0.00'), 'partial': Decimal('26.00'), 'value': Decimal('66.99')},
    {'sku': 'B1006', 'full': Decimal('0.00'), 'partial': Decimal('190.00'), 'value': Decimal('418.00')},
    {'sku': 'B2308', 'full': Decimal('0.00'), 'partial': Decimal('41.00'), 'value': Decimal('82.96')},
    {'sku': 'B0205', 'full': Decimal('0.00'), 'partial': Decimal('76.00'), 'value': Decimal('95.00')},
    {'sku': 'B12', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'B2588', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'B2036', 'full': Decimal('0.00'), 'partial': Decimal('62.00'), 'value': Decimal('105.92')},
    {'sku': 'B0235', 'full': Decimal('0.00'), 'partial': Decimal('65.00'), 'value': Decimal('111.04')},
    {'sku': 'B10', 'full': Decimal('0.00'), 'partial': Decimal('29.00'), 'value': Decimal('51.72')},
    {'sku': 'B0254', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
]

# ========== SPIRITS (Correct SKUs) ==========
EXCEL_SPIRITS = [
    {'sku': 'S0008', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('25.00')},
    {'sku': 'S0006', 'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('52.30')},
    {'sku': 'S3214', 'full': Decimal('2.00'), 'partial': Decimal('0.80'), 'value': Decimal('51.32')},
    {'sku': 'S1019', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('15.60')},
    {'sku': 'S0002', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('79.56')},
    {'sku': 'S1401', 'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('39.80')},
    {'sku': 'S0045', 'full': Decimal('5.00'), 'partial': Decimal('0.85'), 'value': Decimal('145.20')},
    {'sku': 'S29', 'full': Decimal('1.00'), 'partial': Decimal('0.60'), 'value': Decimal('40.70')},
    {'sku': 'S0074', 'full': Decimal('7.00'), 'partial': Decimal('0.20'), 'value': Decimal('120.60')},
    {'sku': 'S2058', 'full': Decimal('1.00'), 'partial': Decimal('0.80'), 'value': Decimal('53.53')},
    {'sku': 'S2033', 'full': Decimal('1.00'), 'partial': Decimal('0.45'), 'value': Decimal('25.85')},
    {'sku': 'S2055', 'full': Decimal('2.00'), 'partial': Decimal('0.50'), 'value': Decimal('95.80')},
    {'sku': 'S0065', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('49.20')},
    {'sku': 'S2148', 'full': Decimal('2.00'), 'partial': Decimal('0.55'), 'value': Decimal('78.62')},
    {'sku': 'S1400', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('17.51')},
    {'sku': 'S0080', 'full': Decimal('3.00'), 'partial': Decimal('0.45'), 'value': Decimal('80.25')},
    {'sku': 'S100', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('104.00')},
    {'sku': 'S0215', 'full': Decimal('2.00'), 'partial': Decimal('0.40'), 'value': Decimal('40.82')},
    {'sku': 'S0162', 'full': Decimal('1.50'), 'partial': Decimal('0.00'), 'value': Decimal('19.61')},
    {'sku': 'S1024', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('14.48')},
    {'sku': 'S0180', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('26.14')},
    {'sku': 'S0190', 'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('25.12')},
    {'sku': 'S0195', 'full': Decimal('1.00'), 'partial': Decimal('0.90'), 'value': Decimal('31.52')},
    {'sku': 'S5555', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('28.50')},
    {'sku': 'S0009', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('8.59')},
    {'sku': 'S0147', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0100', 'full': Decimal('1.00'), 'partial': Decimal('0.45'), 'value': Decimal('32.38')},
    {'sku': 'S2314', 'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('42.94')},
    {'sku': 'S2065', 'full': Decimal('1.00'), 'partial': Decimal('0.25'), 'value': Decimal('37.93')},
    {'sku': 'S0105', 'full': Decimal('3.00'), 'partial': Decimal('0.55'), 'value': Decimal('116.33')},
    {'sku': 'S0027', 'full': Decimal('0.00'), 'partial': Decimal('0.75'), 'value': Decimal('18.59')},
    {'sku': 'S0120', 'full': Decimal('3.00'), 'partial': Decimal('0.90'), 'value': Decimal('69.54')},
    {'sku': 'S0130', 'full': Decimal('2.00'), 'partial': Decimal('0.85'), 'value': Decimal('51.78')},
    {'sku': 'S0135', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('91.68')},
    {'sku': 'S0140', 'full': Decimal('4.00'), 'partial': Decimal('0.60'), 'value': Decimal('108.10')},
    {'sku': 'S0150', 'full': Decimal('7.00'), 'partial': Decimal('0.35'), 'value': Decimal('173.09')},
    {'sku': 'S1203', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('33.50')},
    {'sku': 'S0170', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('20.85')},
    {'sku': 'S0007', 'full': Decimal('6.00'), 'partial': Decimal('0.20'), 'value': Decimal('205.65')},
    {'sku': 'S0205', 'full': Decimal('2.00'), 'partial': Decimal('0.55'), 'value': Decimal('84.61')},
    {'sku': 'S0220', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S3145', 'full': Decimal('20.00'), 'partial': Decimal('0.10'), 'value': Decimal('490.84')},
    {'sku': 'S2369', 'full': Decimal('3.00'), 'partial': Decimal('0.35'), 'value': Decimal('125.63')},
    {'sku': 'S2034', 'full': Decimal('13.00'), 'partial': Decimal('0.50'), 'value': Decimal('276.75')},
    {'sku': 'S1587', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('39.16')},
    {'sku': 'S0230', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('28.35')},
    {'sku': 'S0026', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('79.98')},
    {'sku': 'S0245', 'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('54.86')},
    {'sku': 'S0265', 'full': Decimal('0.00'), 'partial': Decimal('0.30'), 'value': Decimal('7.36')},
    {'sku': 'S0014', 'full': Decimal('1.00'), 'partial': Decimal('0.30'), 'value': Decimal('40.42')},
    {'sku': 'S0271', 'full': Decimal('1.00'), 'partial': Decimal('0.85'), 'value': Decimal('71.00')},
    {'sku': 'S0327', 'full': Decimal('3.00'), 'partial': Decimal('0.20'), 'value': Decimal('122.66')},
    {'sku': 'S002', 'full': Decimal('7.00'), 'partial': Decimal('0.60'), 'value': Decimal('196.31')},
    {'sku': 'S0019', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0306', 'full': Decimal('8.00'), 'partial': Decimal('0.75'), 'value': Decimal('217.70')},
    {'sku': 'S0310', 'full': Decimal('3.00'), 'partial': Decimal('0.95'), 'value': Decimal('125.53')},
    {'sku': 'S1412', 'full': Decimal('15.00'), 'partial': Decimal('0.25'), 'value': Decimal('681.52')},
    {'sku': 'S1258', 'full': Decimal('2.00'), 'partial': Decimal('0.85'), 'value': Decimal('103.08')},
    {'sku': 'S0325', 'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('33.05')},
    {'sku': 'S0029', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('18.50')},
    {'sku': 'S2156', 'full': Decimal('2.00'), 'partial': Decimal('0.95'), 'value': Decimal('62.98')},
    {'sku': 'S2354', 'full': Decimal('1.00'), 'partial': Decimal('0.10'), 'value': Decimal('35.19')},
    {'sku': 'S1302', 'full': Decimal('1.00'), 'partial': Decimal('0.80'), 'value': Decimal('58.81')},
    {'sku': 'S0335', 'full': Decimal('5.00'), 'partial': Decimal('0.90'), 'value': Decimal('259.95')},
    {'sku': 'S0365', 'full': Decimal('2.00'), 'partial': Decimal('0.20'), 'value': Decimal('49.87')},
    {'sku': 'S0380', 'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('50.78')},
    {'sku': 'S0385', 'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('45.68')},
    {'sku': 'S2186', 'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('72.17')},
    {'sku': 'S0405', 'full': Decimal('17.00'), 'partial': Decimal('0.80'), 'value': Decimal('520.29')},
    {'sku': 'S0255', 'full': Decimal('6.00'), 'partial': Decimal('0.85'), 'value': Decimal('287.77')},
    {'sku': 'S2189', 'full': Decimal('3.00'), 'partial': Decimal('0.70'), 'value': Decimal('116.11')},
    {'sku': 'S0370', 'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('101.22')},
    {'sku': 'S1002', 'full': Decimal('3.00'), 'partial': Decimal('0.50'), 'value': Decimal('73.68')},
    {'sku': 'S0420', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('40.74')},
    {'sku': 'S1299', 'full': Decimal('3.00'), 'partial': Decimal('0.40'), 'value': Decimal('74.80')},
    {'sku': 'S0021', 'full': Decimal('1.00'), 'partial': Decimal('0.20'), 'value': Decimal('36.60')},
    {'sku': 'S9987', 'full': Decimal('7.00'), 'partial': Decimal('0.25'), 'value': Decimal('165.52')},
    {'sku': 'S1101', 'full': Decimal('1.00'), 'partial': Decimal('0.15'), 'value': Decimal('55.20')},
    {'sku': 'S1205', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0455', 'full': Decimal('3.00'), 'partial': Decimal('0.10'), 'value': Decimal('40.83')},
    {'sku': 'S2155', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('31.69')},
    {'sku': 'S0699', 'full': Decimal('6.00'), 'partial': Decimal('0.50'), 'value': Decimal('63.18')},
    {'sku': 'S0485', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('29.16')},
    {'sku': 'S2365', 'full': Decimal('1.00'), 'partial': Decimal('0.35'), 'value': Decimal('35.78')},
    {'sku': 'S2349', 'full': Decimal('0.00'), 'partial': Decimal('0.40'), 'value': Decimal('13.17')},
    {'sku': 'S1047', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('23.22')},
    {'sku': 'S0064', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('56.66')},
    {'sku': 'S0530', 'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('54.44')},
    {'sku': 'S0041', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('15.00')},
    {'sku': 'S24', 'full': Decimal('1.00'), 'partial': Decimal('0.40'), 'value': Decimal('69.96')},
    {'sku': 'S0543', 'full': Decimal('9.00'), 'partial': Decimal('0.40'), 'value': Decimal('119.47')},
    {'sku': 'S0545', 'full': Decimal('1.00'), 'partial': Decimal('0.90'), 'value': Decimal('39.05')},
    {'sku': 'S0550', 'full': Decimal('0.00'), 'partial': Decimal('0.05'), 'value': Decimal('0.88')},
    {'sku': 'S0555', 'full': Decimal('4.00'), 'partial': Decimal('0.90'), 'value': Decimal('159.94')},
    {'sku': 'S2359', 'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('83.41')},
    {'sku': 'S2241', 'full': Decimal('1.00'), 'partial': Decimal('0.75'), 'value': Decimal('100.33')},
    {'sku': 'S0575', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('93.34')},
    {'sku': 'S1210', 'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('238.30')},
    {'sku': 'S0585', 'full': Decimal('2.00'), 'partial': Decimal('0.40'), 'value': Decimal('103.34')},
    {'sku': 'S0022', 'full': Decimal('4.00'), 'partial': Decimal('0.90'), 'value': Decimal('147.00')},
    {'sku': 'S2302', 'full': Decimal('1.00'), 'partial': Decimal('0.30'), 'value': Decimal('41.17')},
    {'sku': 'S0605', 'full': Decimal('1.00'), 'partial': Decimal('0.85'), 'value': Decimal('26.44')},
    {'sku': 'S0018', 'full': Decimal('1.00'), 'partial': Decimal('0.65'), 'value': Decimal('27.19')},
    {'sku': 'S2217', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('30.01')},
    {'sku': 'S0001', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('101.49')},
    {'sku': 'S0610', 'full': Decimal('41.00'), 'partial': Decimal('0.30'), 'value': Decimal('901.58')},
    {'sku': 'S0625', 'full': Decimal('2.00'), 'partial': Decimal('0.55'), 'value': Decimal('35.06')},
    {'sku': 'S0010', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('106.06')},
    {'sku': 'S0638', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('45.66')},
    {'sku': 'S0630', 'full': Decimal('0.00'), 'partial': Decimal('0.05'), 'value': Decimal('0.86')},
    {'sku': 'S2159', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0012', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('18.17')},
    {'sku': 'S0635', 'full': Decimal('6.00'), 'partial': Decimal('0.60'), 'value': Decimal('133.32')},
    {'sku': 'S1022', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0640', 'full': Decimal('6.00'), 'partial': Decimal('0.30'), 'value': Decimal('96.58')},
    {'sku': 'S0653', 'full': Decimal('2.00'), 'partial': Decimal('0.95'), 'value': Decimal('40.74')},
    {'sku': 'S3147', 'full': Decimal('7.00'), 'partial': Decimal('0.15'), 'value': Decimal('160.88')},
    {'sku': 'S0647', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('67.71')},
    {'sku': 'S0023', 'full': Decimal('1.00'), 'partial': Decimal('0.90'), 'value': Decimal('24.55')},
    {'sku': 'S0028', 'full': Decimal('1.00'), 'partial': Decimal('0.85'), 'value': Decimal('33.10')},
    {'sku': 'S0017', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0005', 'full': Decimal('4.00'), 'partial': Decimal('0.90'), 'value': Decimal('65.66')},
    {'sku': 'S2378', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0071', 'full': Decimal('2.00'), 'partial': Decimal('0.50'), 'value': Decimal('31.05')},
    {'sku': 'S1411', 'full': Decimal('2.00'), 'partial': Decimal('0.70'), 'value': Decimal('164.81')},
]

# ========== WINES (Correct SKUs) ==========
EXCEL_WINES = [
    {'sku': 'W0040', 'full': Decimal('36.00'), 'partial': Decimal('0.00'), 'value': Decimal('124.92')},
    {'sku': 'W31', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W0039', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W0019', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('186.70')},
    {'sku': 'W0025', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('97.98')},
    {'sku': 'W0044', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('36.18')},
    {'sku': 'W0018', 'full': Decimal('11.00'), 'partial': Decimal('0.00'), 'value': Decimal('112.75')},
    {'sku': 'W2108', 'full': Decimal('24.00'), 'partial': Decimal('0.00'), 'value': Decimal('163.92')},
    {'sku': 'W0038', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('49.15')},
    {'sku': 'W0032', 'full': Decimal('3.80'), 'partial': Decimal('0.00'), 'value': Decimal('41.15')},
    {'sku': 'W0036', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('63.32')},
    {'sku': 'W0028', 'full': Decimal('11.00'), 'partial': Decimal('0.00'), 'value': Decimal('170.50')},
    {'sku': 'W0023', 'full': Decimal('23.00'), 'partial': Decimal('0.00'), 'value': Decimal('187.22')},
    {'sku': 'W0027', 'full': Decimal('32.00'), 'partial': Decimal('0.00'), 'value': Decimal('240.00')},
    {'sku': 'W0043', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('10.38')},
    {'sku': 'W0031', 'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('110.50')},
    {'sku': 'W0033', 'full': Decimal('15.60'), 'partial': Decimal('0.00'), 'value': Decimal('132.60')},
    {'sku': 'W2102', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('61.12')},
    {'sku': 'W1020', 'full': Decimal('32.00'), 'partial': Decimal('0.00'), 'value': Decimal('224.00')},
    {'sku': 'W2589', 'full': Decimal('50.60'), 'partial': Decimal('0.00'), 'value': Decimal('312.20')},
    {'sku': 'W1004', 'full': Decimal('76.10'), 'partial': Decimal('0.00'), 'value': Decimal('469.54')},
    {'sku': 'W0024', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('124.00')},
    {'sku': 'W1013', 'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('371.88')},
    {'sku': 'W0021', 'full': Decimal('20.00'), 'partial': Decimal('0.00'), 'value': Decimal('197.60')},
    {'sku': 'W0037', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('175.00')},
    {'sku': 'W45', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('92.00')},
    {'sku': 'W1019', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W2110', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W111', 'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('54.21')},
    {'sku': 'W1', 'full': Decimal('16.00'), 'partial': Decimal('0.00'), 'value': Decimal('142.88')},
    {'sku': 'W0034', 'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('90.00')},
    {'sku': 'W0041', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('62.58')},
    {'sku': 'W0042', 'full': Decimal('16.00'), 'partial': Decimal('0.00'), 'value': Decimal('103.68')},
    {'sku': 'W2104', 'full': Decimal('59.60'), 'partial': Decimal('0.00'), 'value': Decimal('412.43')},
    {'sku': 'W0029', 'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('127.79')},
    {'sku': 'W0022', 'full': Decimal('49.40'), 'partial': Decimal('0.00'), 'value': Decimal('338.39')},
    {'sku': 'W0030', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('87.00')},
]

# ========== MINERALS & SYRUPS (Correct SKUs) ==========
EXCEL_MINERALS = [
    {'sku': 'M2236', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M0195', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M0140', 'full': Decimal('0.00'), 'partial': Decimal('137.00'), 'value': Decimal('194.08')},
    {'sku': 'M2107', 'full': Decimal('0.00'), 'partial': Decimal('42.00'), 'value': Decimal('43.82')},
    {'sku': 'M0320', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('18.48')},
    {'sku': 'M11', 'full': Decimal('0.00'), 'partial': Decimal('117.00'), 'value': Decimal('117.00')},
    {'sku': 'M0042', 'full': Decimal('0.00'), 'partial': Decimal('40.00'), 'value': Decimal('40.50')},
    {'sku': 'M0210', 'full': Decimal('0.00'), 'partial': Decimal('48.00'), 'value': Decimal('52.20')},
    {'sku': 'M0008', 'full': Decimal('18.00'), 'partial': Decimal('0.00'), 'value': Decimal('105.84')},
    {'sku': 'M0009', 'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('70.56')},
    {'sku': 'M3', 'full': Decimal('2.70'), 'partial': Decimal('0.00'), 'value': Decimal('26.95')},
    {'sku': 'M0006', 'full': Decimal('2.20'), 'partial': Decimal('0.00'), 'value': Decimal('20.53')},
    {'sku': 'M13', 'full': Decimal('15.70'), 'partial': Decimal('0.00'), 'value': Decimal('143.66')},
    {'sku': 'M04', 'full': Decimal('4.50'), 'partial': Decimal('0.00'), 'value': Decimal('46.71')},
    {'sku': 'M0014', 'full': Decimal('8.40'), 'partial': Decimal('0.00'), 'value': Decimal('86.10')},
    {'sku': 'M2', 'full': Decimal('6.50'), 'partial': Decimal('0.00'), 'value': Decimal('99.91')},
    {'sku': 'M03', 'full': Decimal('13.40'), 'partial': Decimal('0.00'), 'value': Decimal('122.61')},
    {'sku': 'M05', 'full': Decimal('5.40'), 'partial': Decimal('0.00'), 'value': Decimal('55.35')},
    {'sku': 'M06', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M1', 'full': Decimal('10.00'), 'partial': Decimal('0.00'), 'value': Decimal('121.30')},
    {'sku': 'M01', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('61.86')},
    {'sku': 'M5', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M9', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('26.49')},
    {'sku': 'M02', 'full': Decimal('5.10'), 'partial': Decimal('0.00'), 'value': Decimal('45.65')},
    {'sku': 'M0170', 'full': Decimal('0.00'), 'partial': Decimal('64.00'), 'value': Decimal('59.36')},
    {'sku': 'M0123', 'full': Decimal('0.00'), 'partial': Decimal('35.00'), 'value': Decimal('56.44')},
    {'sku': 'M0180', 'full': Decimal('0.00'), 'partial': Decimal('388.00'), 'value': Decimal('167.49')},
    {'sku': 'M25', 'full': Decimal('1.00'), 'partial': Decimal('1.00'), 'value': Decimal('171.50')},
    {'sku': 'M24', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M23', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('173.06')},
    {'sku': 'M0050', 'full': Decimal('0.00'), 'partial': Decimal('288.00'), 'value': Decimal('152.40')},
    {'sku': 'M0003', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M0040', 'full': Decimal('0.00'), 'partial': Decimal('10.00'), 'value': Decimal('5.83')},
    {'sku': 'M0013', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M2105', 'full': Decimal('0.00'), 'partial': Decimal('191.00'), 'value': Decimal('105.05')},
    {'sku': 'M0004', 'full': Decimal('0.00'), 'partial': Decimal('116.00'), 'value': Decimal('55.58')},
    {'sku': 'M0034', 'full': Decimal('0.00'), 'partial': Decimal('85.00'), 'value': Decimal('40.73')},
    {'sku': 'M0070', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M0135', 'full': Decimal('0.00'), 'partial': Decimal('38.00'), 'value': Decimal('27.87')},
    {'sku': 'M0315', 'full': Decimal('0.00'), 'partial': Decimal('89.00'), 'value': Decimal('37.83')},
    {'sku': 'M0016', 'full': Decimal('0.00'), 'partial': Decimal('30.00'), 'value': Decimal('25.60')},
    {'sku': 'M0255', 'full': Decimal('0.00'), 'partial': Decimal('475.00'), 'value': Decimal('272.33')},
    {'sku': 'M0122', 'full': Decimal('0.00'), 'partial': Decimal('1.00'), 'value': Decimal('0.54')},
    {'sku': 'M0200', 'full': Decimal('0.00'), 'partial': Decimal('177.00'), 'value': Decimal('82.60')},
    {'sku': 'M0312', 'full': Decimal('0.00'), 'partial': Decimal('159.00'), 'value': Decimal('111.30')},
    {'sku': 'M0012', 'full': Decimal('0.00'), 'partial': Decimal('2.00'), 'value': Decimal('17.34')},
    {'sku': 'M0011', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
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
            print(f"  ✅ {sku} = €{item_data['value']}")
            
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
        print(f"  ⚠️  Discrepancy: €{abs(difference):.2f}")
    
    if not_found:
        print(f"\n  ⚠️  Items not found: {', '.join(not_found)}")
    
    print(f"\n  ✅ Updated {updated_count}/{len(data_list)} items")
    
    return total_value


def main():
    print("=" * 60)
    print("UPDATE ALL CATEGORIES - CORRECT SKUs")
    print("=" * 60)
    
    try:
        hotel = Hotel.objects.first()
        period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
        print(f"\n🏨 Hotel: {hotel.name}")
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
    
    # Get draught total
    draught_snapshots = StockSnapshot.objects.filter(
        hotel=hotel, period=period, item__category__code='D'
    )
    totals['D'] = sum(s.closing_stock_value for s in draught_snapshots)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY - ALL CATEGORIES")
    print("=" * 60)
    
    categories = [
        ('D', 'Draught Beers', Decimal('5311.62')),
        ('B', 'Bottled Beers', Decimal('2288.46')),
        ('S', 'Spirits', Decimal('11063.66')),
        ('W', 'Wines', Decimal('5580.35')),
        ('M', 'Minerals & Syrups', Decimal('3062.43')),
    ]
    
    for code, name, expected in categories:
        diff = totals[code] - expected
        match = "✅" if abs(diff) < Decimal('1.00') else "⚠️"
        print(f"\n{name}:")
        print(f"  Database: €{totals[code]:,.2f}")
        print(f"  Excel:    €{expected:,.2f}")
        print(f"  Diff:     €{diff:,.2f} {match}")
    
    grand_total = sum(totals.values())
    excel_grand_total = Decimal('27306.51')
    
    print(f"\n{'='*60}")
    print(f"GRAND TOTAL: €{grand_total:,.2f}")
    print(f"Excel Total: €{excel_grand_total:,.2f}")
    print(f"Difference:  €{grand_total - excel_grand_total:,.2f}")
    print(f"{'='*60}")
    
    if abs(grand_total - excel_grand_total) < Decimal('0.01'):
        print("\n🎉 SUCCESS! Database matches Excel perfectly!")
    elif abs(grand_total - excel_grand_total) < Decimal('1.00'):
        print("\n✅ SUCCESS! Database matches Excel (within €1)")
    else:
        diff = abs(grand_total - excel_grand_total)
        print(f"\n⚠️  Remaining difference: €{diff:.2f}")


if __name__ == '__main__':
    main()
