"""
Create StockSnapshots with EXACT Excel values for October 2024
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel


# ========== EXCEL DATA WITH EXACT VALUES ==========

EXCEL_DRAUGHT = [
    {'sku': 'D0044', 'full': Decimal('4.00'), 'partial': Decimal('29.75'), 'value': Decimal('522.64')},
    {'sku': 'D0040', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('530.40')},
    {'sku': 'D0085', 'full': Decimal('4.00'), 'partial': Decimal('31.00'), 'value': Decimal('565.68')},
    {'sku': 'D0003', 'full': Decimal('5.00'), 'partial': Decimal('53.00'), 'value': Decimal('687.73')},
    {'sku': 'D5', 'full': Decimal('3.00'), 'partial': Decimal('46.00'), 'value': Decimal('421.37')},
    {'sku': 'D0075', 'full': Decimal('7.00'), 'partial': Decimal('18.00'), 'value': Decimal('860.23')},
    {'sku': 'D0201', 'full': Decimal('3.00'), 'partial': Decimal('68.75'), 'value': Decimal('472.45')},
    {'sku': 'D6', 'full': Decimal('1.00'), 'partial': Decimal('17.00'), 'value': Decimal('111.20')},
    {'sku': 'D5098', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('280.24')},
    {'sku': 'D0120', 'full': Decimal('2.00'), 'partial': Decimal('12.00'), 'value': Decimal('164.96')},
    {'sku': 'D0310', 'full': Decimal('1.00'), 'partial': Decimal('27.00'), 'value': Decimal('179.78')},
    {'sku': 'D0151', 'full': Decimal('3.00'), 'partial': Decimal('52.00'), 'value': Decimal('439.94')},
    {'sku': 'D0011', 'full': Decimal('1.00'), 'partial': Decimal('4.00'), 'value': Decimal('61.00')},
    {'sku': 'D666', 'full': Decimal('0.00'), 'partial': Decimal('14.00'), 'value': Decimal('14.00')},
]

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
    {'sku': 'S005', 'full': Decimal('2.00'), 'partial': Decimal('0.10'), 'value': Decimal('41.47')},
    {'sku': 'S0028', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('24.22')},
    {'sku': 'S0096', 'full': Decimal('2.00'), 'partial': Decimal('0.25'), 'value': Decimal('40.18')},
    {'sku': 'S0108', 'full': Decimal('0.00'), 'partial': Decimal('0.70'), 'value': Decimal('23.93')},
    {'sku': 'S0110', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('43.48')},
    {'sku': 'S0410', 'full': Decimal('1.00'), 'partial': Decimal('0.80'), 'value': Decimal('42.78')},
    {'sku': 'S0420', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('17.80')},
    {'sku': 'S0510', 'full': Decimal('2.00'), 'partial': Decimal('0.00'), 'value': Decimal('36.84')},
    {'sku': 'S0610', 'full': Decimal('0.00'), 'partial': Decimal('0.80'), 'value': Decimal('15.62')},
    {'sku': 'S0615', 'full': Decimal('0.00'), 'partial': Decimal('0.70'), 'value': Decimal('13.50')},
    {'sku': 'S09', 'full': Decimal('3.00'), 'partial': Decimal('0.20'), 'value': Decimal('47.76')},
    {'sku': 'S0011', 'full': Decimal('4.00'), 'partial': Decimal('0.25'), 'value': Decimal('88.99')},
    {'sku': 'S1030', 'full': Decimal('1.00'), 'partial': Decimal('0.50'), 'value': Decimal('29.46')},
    {'sku': 'S1050', 'full': Decimal('0.00'), 'partial': Decimal('0.80'), 'value': Decimal('35.63')},
    {'sku': 'S0015', 'full': Decimal('0.00'), 'partial': Decimal('0.70'), 'value': Decimal('15.96')},
    {'sku': 'S1015', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('25.67')},
    {'sku': 'S1075', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S1100', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S3098', 'full': Decimal('6.00'), 'partial': Decimal('0.50'), 'value': Decimal('148.14')},
    {'sku': 'S0022', 'full': Decimal('1.00'), 'partial': Decimal('0.70'), 'value': Decimal('35.90')},
    {'sku': 'S0004', 'full': Decimal('8.00'), 'partial': Decimal('0.50'), 'value': Decimal('227.59')},
    {'sku': 'S0024', 'full': Decimal('5.00'), 'partial': Decimal('0.30'), 'value': Decimal('120.93')},
    {'sku': 'S2256', 'full': Decimal('5.00'), 'partial': Decimal('0.40'), 'value': Decimal('170.03')},
    {'sku': 'S2014', 'full': Decimal('1.00'), 'partial': Decimal('0.40'), 'value': Decimal('40.42')},
    {'sku': 'S2265', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0038', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('9.58')},
    {'sku': 'S2258', 'full': Decimal('2.00'), 'partial': Decimal('0.45'), 'value': Decimal('76.66')},
    {'sku': 'S2301', 'full': Decimal('7.00'), 'partial': Decimal('0.90'), 'value': Decimal('136.98')},
    {'sku': 'S1200', 'full': Decimal('0.00'), 'partial': Decimal('0.60'), 'value': Decimal('9.10')},
    {'sku': 'S0165', 'full': Decimal('1.00'), 'partial': Decimal('0.35'), 'value': Decimal('42.42')},
    {'sku': 'S0270', 'full': Decimal('2.00'), 'partial': Decimal('0.80'), 'value': Decimal('93.98')},
    {'sku': 'S0280', 'full': Decimal('5.00'), 'partial': Decimal('0.40'), 'value': Decimal('156.66')},
    {'sku': 'S0290', 'full': Decimal('3.00'), 'partial': Decimal('0.60'), 'value': Decimal('77.30')},
    {'sku': 'S0305', 'full': Decimal('3.00'), 'partial': Decimal('0.40'), 'value': Decimal('60.05')},
    {'sku': 'S0315', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('20.03')},
    {'sku': 'S0318', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('17.80')},
    {'sku': 'S0410B', 'full': Decimal('0.00'), 'partial': Decimal('0.35'), 'value': Decimal('11.43')},
    {'sku': 'S3033', 'full': Decimal('0.00'), 'partial': Decimal('0.50'), 'value': Decimal('17.36')},
    {'sku': 'S3034', 'full': Decimal('3.00'), 'partial': Decimal('0.60'), 'value': Decimal('67.91')},
    {'sku': 'S3036', 'full': Decimal('2.00'), 'partial': Decimal('0.90'), 'value': Decimal('55.20')},
    {'sku': 'S3048', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S3066', 'full': Decimal('0.00'), 'partial': Decimal('0.65'), 'value': Decimal('9.85')},
    {'sku': 'S3325', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0330', 'full': Decimal('3.00'), 'partial': Decimal('0.70'), 'value': Decimal('61.11')},
    {'sku': 'S0001', 'full': Decimal('4.00'), 'partial': Decimal('0.10'), 'value': Decimal('118.92')},
    {'sku': 'S0125', 'full': Decimal('0.00'), 'partial': Decimal('0.40'), 'value': Decimal('9.41')},
    {'sku': 'S3099', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('13.50')},
    {'sku': 'S3158', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('16.36')},
    {'sku': 'S0048', 'full': Decimal('6.00'), 'partial': Decimal('0.10'), 'value': Decimal('138.01')},
    {'sku': 'S0060', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0040', 'full': Decimal('0.00'), 'partial': Decimal('0.90'), 'value': Decimal('28.35')},
    {'sku': 'S0044', 'full': Decimal('1.50'), 'partial': Decimal('0.00'), 'value': Decimal('85.11')},
    {'sku': 'S3147', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('13.19')},
    {'sku': 'S3159', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S3164', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S3174', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('73.20')},
    {'sku': 'S0620', 'full': Decimal('1.00'), 'partial': Decimal('0.55'), 'value': Decimal('36.88')},
    {'sku': 'S1004', 'full': Decimal('6.00'), 'partial': Decimal('0.55'), 'value': Decimal('128.34')},
    {'sku': 'S1010', 'full': Decimal('0.00'), 'partial': Decimal('0.20'), 'value': Decimal('5.53')},
    {'sku': 'S1104', 'full': Decimal('2.00'), 'partial': Decimal('0.40'), 'value': Decimal('110.56')},
    {'sku': 'S3141', 'full': Decimal('1.00'), 'partial': Decimal('0.60'), 'value': Decimal('42.92')},
    {'sku': 'S0210', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S1303', 'full': Decimal('2.00'), 'partial': Decimal('0.80'), 'value': Decimal('102.97')},
    {'sku': 'S0222', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0240', 'full': Decimal('6.00'), 'partial': Decimal('0.40'), 'value': Decimal('160.06')},
    {'sku': 'S0250', 'full': Decimal('0.50'), 'partial': Decimal('0.00'), 'value': Decimal('21.33')},
    {'sku': 'S0260', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('158.40')},
    {'sku': 'S0268', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S0300', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'S_SEADOG', 'full': Decimal('1.00'), 'partial': Decimal('0.70'), 'value': Decimal('66.81')},
    {'sku': 'S_DINGLE_WHISKEY', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('150.00')},
    {'sku': 'S0638_00', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
]

EXCEL_WINES = [
    {'sku': 'W0036', 'full': Decimal('3.00'), 'partial': Decimal('0.60'), 'value': Decimal('36.21')},
    {'sku': 'W0203', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('76.56')},
    {'sku': 'W0051', 'full': Decimal('9.00'), 'partial': Decimal('0.30'), 'value': Decimal('116.46')},
    {'sku': 'W0080', 'full': Decimal('12.00'), 'partial': Decimal('0.60'), 'value': Decimal('131.64')},
    {'sku': 'W0095', 'full': Decimal('12.00'), 'partial': Decimal('0.50'), 'value': Decimal('162.45')},
    {'sku': 'W0108', 'full': Decimal('8.00'), 'partial': Decimal('0.90'), 'value': Decimal('158.42')},
    {'sku': 'W0115', 'full': Decimal('7.00'), 'partial': Decimal('0.60'), 'value': Decimal('66.49')},
    {'sku': 'W0128', 'full': Decimal('5.00'), 'partial': Decimal('0.90'), 'value': Decimal('66.36')},
    {'sku': 'W0133', 'full': Decimal('14.00'), 'partial': Decimal('0.10'), 'value': Decimal('184.00')},
    {'sku': 'W0146', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W0152', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('64.00')},
    {'sku': 'W0170', 'full': Decimal('6.00'), 'partial': Decimal('0.30'), 'value': Decimal('65.35')},
    {'sku': 'W0220', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W0350', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W006', 'full': Decimal('2.00'), 'partial': Decimal('0.30'), 'value': Decimal('27.57')},
    {'sku': 'W0059', 'full': Decimal('10.00'), 'partial': Decimal('0.80'), 'value': Decimal('154.52')},
    {'sku': 'W0018', 'full': Decimal('19.00'), 'partial': Decimal('0.00'), 'value': Decimal('281.70')},
    {'sku': 'W008', 'full': Decimal('6.00'), 'partial': Decimal('0.90'), 'value': Decimal('84.63')},
    {'sku': 'W0090', 'full': Decimal('8.00'), 'partial': Decimal('0.90'), 'value': Decimal('135.51')},
    {'sku': 'W0067', 'full': Decimal('20.00'), 'partial': Decimal('0.00'), 'value': Decimal('193.60')},
    {'sku': 'W0195', 'full': Decimal('4.00'), 'partial': Decimal('0.40'), 'value': Decimal('75.04')},
    {'sku': 'W0190', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('18.00')},
    {'sku': 'W0099', 'full': Decimal('3.00'), 'partial': Decimal('0.60'), 'value': Decimal('39.96')},
    {'sku': 'W0107', 'full': Decimal('21.00'), 'partial': Decimal('0.20'), 'value': Decimal('233.28')},
    {'sku': 'W0133A', 'full': Decimal('13.00'), 'partial': Decimal('0.40'), 'value': Decimal('233.31')},
    {'sku': 'W0133B', 'full': Decimal('11.00'), 'partial': Decimal('0.20'), 'value': Decimal('196.13')},
    {'sku': 'W0217', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('76.56')},
    {'sku': 'W0260', 'full': Decimal('1.00'), 'partial': Decimal('0.10'), 'value': Decimal('12.37')},
    {'sku': 'W0147', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W3064', 'full': Decimal('4.00'), 'partial': Decimal('0.00'), 'value': Decimal('72.32')},
    {'sku': 'W0009', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W0038', 'full': Decimal('43.00'), 'partial': Decimal('0.00'), 'value': Decimal('388.50')},
    {'sku': 'W5006', 'full': Decimal('13.00'), 'partial': Decimal('0.00'), 'value': Decimal('221.00')},
    {'sku': 'W3084', 'full': Decimal('18.00'), 'partial': Decimal('0.00'), 'value': Decimal('316.62')},
    {'sku': 'W3085', 'full': Decimal('8.00'), 'partial': Decimal('0.00'), 'value': Decimal('131.12')},
    {'sku': 'W0135', 'full': Decimal('7.00'), 'partial': Decimal('0.70'), 'value': Decimal('144.93')},
    {'sku': 'W4031', 'full': Decimal('12.00'), 'partial': Decimal('0.00'), 'value': Decimal('342.36')},
    {'sku': 'W_MDC_PROSECCO', 'full': Decimal('6.00'), 'partial': Decimal('0.00'), 'value': Decimal('319.77')},
    {'sku': 'W_OG_SHIRAZ_75', 'full': Decimal('3.00'), 'partial': Decimal('0.00'), 'value': Decimal('51.00')},
    {'sku': 'W_OG_SHIRAZ_187', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W_OG_SAUV_187', 'full': Decimal('1.00'), 'partial': Decimal('0.00'), 'value': Decimal('36.00')},
    {'sku': 'W_PACSAUD', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W_PINOT_SNIPES', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'W_PROSECCO_NA', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
]

EXCEL_MINERALS = [
    {'sku': 'M3314', 'full': Decimal('0.00'), 'partial': Decimal('42.00'), 'value': Decimal('22.68')},
    {'sku': 'M0044', 'full': Decimal('0.00'), 'partial': Decimal('193.00'), 'value': Decimal('104.22')},
    {'sku': 'M0003', 'full': Decimal('0.00'), 'partial': Decimal('133.00'), 'value': Decimal('71.82')},
    {'sku': 'M0085', 'full': Decimal('0.00'), 'partial': Decimal('126.00'), 'value': Decimal('68.04')},
    {'sku': 'M0040', 'full': Decimal('0.00'), 'partial': Decimal('115.00'), 'value': Decimal('62.10')},
    {'sku': 'M0075', 'full': Decimal('0.00'), 'partial': Decimal('149.00'), 'value': Decimal('80.46')},
    {'sku': 'M0012', 'full': Decimal('0.00'), 'partial': Decimal('57.00'), 'value': Decimal('30.78')},
    {'sku': 'M01', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M0030', 'full': Decimal('0.00'), 'partial': Decimal('132.00'), 'value': Decimal('71.28')},
    {'sku': 'M0201', 'full': Decimal('0.00'), 'partial': Decimal('65.00'), 'value': Decimal('35.10')},
    {'sku': 'M0151', 'full': Decimal('0.00'), 'partial': Decimal('98.00'), 'value': Decimal('52.92')},
    {'sku': 'M0206', 'full': Decimal('0.00'), 'partial': Decimal('67.00'), 'value': Decimal('36.18')},
    {'sku': 'M0071', 'full': Decimal('0.00'), 'partial': Decimal('85.00'), 'value': Decimal('45.90')},
    {'sku': 'M1065', 'full': Decimal('0.00'), 'partial': Decimal('40.00'), 'value': Decimal('30.80')},
    {'sku': 'M1066', 'full': Decimal('0.00'), 'partial': Decimal('28.00'), 'value': Decimal('33.04')},
    {'sku': 'M1094', 'full': Decimal('0.00'), 'partial': Decimal('44.00'), 'value': Decimal('51.92')},
    {'sku': 'M1116', 'full': Decimal('0.00'), 'partial': Decimal('31.00'), 'value': Decimal('36.58')},
    {'sku': 'M1075', 'full': Decimal('0.00'), 'partial': Decimal('48.00'), 'value': Decimal('34.56')},
    {'sku': 'M1081', 'full': Decimal('0.00'), 'partial': Decimal('85.00'), 'value': Decimal('61.20')},
    {'sku': 'M1089', 'full': Decimal('0.00'), 'partial': Decimal('29.00'), 'value': Decimal('20.88')},
    {'sku': 'M1085', 'full': Decimal('0.00'), 'partial': Decimal('20.00'), 'value': Decimal('14.40')},
    {'sku': 'M1086', 'full': Decimal('0.00'), 'partial': Decimal('90.00'), 'value': Decimal('64.80')},
    {'sku': 'M2051', 'full': Decimal('0.00'), 'partial': Decimal('38.00'), 'value': Decimal('38.00')},
    {'sku': 'M3032', 'full': Decimal('0.00'), 'partial': Decimal('30.00'), 'value': Decimal('30.00')},
    {'sku': 'M1098', 'full': Decimal('0.00'), 'partial': Decimal('123.00'), 'value': Decimal('148.83')},
    {'sku': 'M1099', 'full': Decimal('0.00'), 'partial': Decimal('22.00'), 'value': Decimal('26.62')},
    {'sku': 'M1101', 'full': Decimal('0.00'), 'partial': Decimal('58.00'), 'value': Decimal('70.18')},
    {'sku': 'M1112', 'full': Decimal('0.00'), 'partial': Decimal('23.00'), 'value': Decimal('27.83')},
    {'sku': 'M6020', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M6014', 'full': Decimal('0.00'), 'partial': Decimal('57.00'), 'value': Decimal('62.70')},
    {'sku': 'M6002', 'full': Decimal('0.00'), 'partial': Decimal('65.00'), 'value': Decimal('94.25')},
    {'sku': 'M6005', 'full': Decimal('0.00'), 'partial': Decimal('85.00'), 'value': Decimal('123.25')},
    {'sku': 'M6003', 'full': Decimal('0.00'), 'partial': Decimal('88.00'), 'value': Decimal('127.60')},
    {'sku': 'M6001', 'full': Decimal('0.00'), 'partial': Decimal('99.00'), 'value': Decimal('143.55')},
    {'sku': 'M6013', 'full': Decimal('0.00'), 'partial': Decimal('45.00'), 'value': Decimal('65.25')},
    {'sku': 'M6011', 'full': Decimal('0.00'), 'partial': Decimal('120.00'), 'value': Decimal('192.00')},
    {'sku': 'M6006', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'M4024', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('155.00')},
    {'sku': 'M4027', 'full': Decimal('5.00'), 'partial': Decimal('0.00'), 'value': Decimal('165.00')},
    {'sku': 'M4069', 'full': Decimal('11.00'), 'partial': Decimal('0.00'), 'value': Decimal('429.00')},
    {'sku': 'M1103', 'full': Decimal('0.00'), 'partial': Decimal('41.00'), 'value': Decimal('56.78')},
    {'sku': 'M1108', 'full': Decimal('0.00'), 'partial': Decimal('48.00'), 'value': Decimal('66.48')},
    {'sku': 'M1110', 'full': Decimal('0.00'), 'partial': Decimal('35.00'), 'value': Decimal('48.48')},
    {'sku': 'M1115', 'full': Decimal('0.00'), 'partial': Decimal('35.00'), 'value': Decimal('48.48')},
    {'sku': 'M1160', 'full': Decimal('0.00'), 'partial': Decimal('36.00'), 'value': Decimal('49.86')},
    {'sku': 'M1091', 'full': Decimal('0.00'), 'partial': Decimal('25.00'), 'value': Decimal('34.63')},
    {'sku': 'M1102', 'full': Decimal('0.00'), 'partial': Decimal('0.00'), 'value': Decimal('0.00')},
]


def create_excel_snapshots():
    """Create snapshots with exact Excel values"""
    
    print("=" * 70)
    print("CREATE OCTOBER 2024 SNAPSHOTS WITH EXACT EXCEL VALUES")
    print("=" * 70)
    
    hotel = Hotel.objects.first()
    print(f"\n🏨 Hotel: {hotel.name}")
    
    # Get or open the October 2024 period
    try:
        period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
        # Open the period if it's closed
        if period.is_closed:
            print(f"📅 Reopening period: {period.period_name}")
            period.is_closed = False
            period.save()
    except StockPeriod.DoesNotExist:
        print(f"\n❌ October 2024 period not found!")
        return
    
    print(f"📅 Period: {period.period_name}")
    
    # Delete existing snapshots
    existing = StockSnapshot.objects.filter(hotel=hotel, period=period)
    if existing.exists():
        print(f"\n🗑️  Deleting {existing.count()} existing snapshots...")
        existing.delete()
    
    # Create snapshots with exact Excel values
    print(f"\n📸 Creating snapshots with exact Excel values...\n")
    
    all_excel_data = [
        ('D', EXCEL_DRAUGHT),
        ('B', EXCEL_BOTTLED),
        ('S', EXCEL_SPIRITS),
        ('W', EXCEL_WINES),
        ('M', EXCEL_MINERALS),
    ]
    
    created_count = 0
    total_value = Decimal('0.00')
    category_summary = {}
    
    for cat_code, excel_items in all_excel_data:
        print(f"  {cat_code} Category:")
        cat_count = 0
        cat_value = Decimal('0.00')
        
        for row in excel_items:
            try:
                item = StockItem.objects.get(hotel=hotel, sku=row['sku'])
                
                snapshot = StockSnapshot.objects.create(
                    hotel=hotel,
                    period=period,
                    item=item,
                    closing_full_units=row['full'],
                    closing_partial_units=row['partial'],
                    unit_cost=item.unit_cost,
                    cost_per_serving=item.cost_per_serving,
                    closing_stock_value=row['value'],  # EXACT Excel value
                    menu_price=item.menu_price
                )
                
                created_count += 1
                cat_count += 1
                cat_value += row['value']
                total_value += row['value']
                
            except StockItem.DoesNotExist:
                print(f"    ⚠️  SKU not found: {row['sku']}")
        
        category_summary[cat_code] = {'count': cat_count, 'value': cat_value}
        print(f"    Created: {cat_count} items, Value: €{cat_value:,.2f}\n")
    
    # Display summary
    print(f"📊 STOCKTAKE SUMMARY:")
    print(f"=" * 70)
    
    for cat_code in ['D', 'B', 'S', 'W', 'M']:
        if cat_code in category_summary:
            cat = category_summary[cat_code]
            print(f"  {cat_code}: {cat['count']:>3} items = €{cat['value']:>10,.2f}")
    
    print(f"  {'-' * 68}")
    print(f"  TOTAL: {created_count:>3} items = €{total_value:>10,.2f}")
    print(f"=" * 70)
    
    # Verify against Excel
    excel_total = Decimal('27306.51')
    difference = total_value - excel_total
    
    print(f"\n✅ VERIFICATION:")
    print(f"  Database Total: €{total_value:,.2f}")
    print(f"  Excel Total:    €{excel_total:,.2f}")
    print(f"  Difference:     €{difference:,.2f}")
    
    if abs(difference) < Decimal('0.10'):
        print(f"  Status: ✅ PERFECT MATCH!")
    elif abs(difference) < Decimal('1.00'):
        print(f"  Status: ✅ VERIFIED (within €1)")
    else:
        print(f"  Status: ⚠️  WARNING - Check values")
    
    # Close the period
    print(f"\n🔒 Closing October 2024 Period...")
    period.is_closed = True
    period.save()
    print(f"  ✅ Period closed successfully!")
    
    print(f"\n" + "=" * 70)
    print(f"🎉 October 2024 Stocktake Complete!")
    print(f"   Period ID: {period.id}")
    print(f"   Status: CLOSED")
    print(f"   Total Items: {created_count}")
    print(f"   Total Value: €{total_value:,.2f}")
    print(f"=" * 70)


if __name__ == '__main__':
    create_excel_snapshots()
