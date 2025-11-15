"""
Compare Excel spirits data with system stocktake data
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

print("=" * 120)
print("SPIRITS COMPARISON: EXCEL vs SYSTEM (October 2025)")
print("=" * 120)

# Excel data from your sheet
excel_data = {
    'S0008': {'name': '1827 Osborne Port', 'size': '75cl', 'uom': 10.6, 'cost': 12.50, 'full': 2.00, 'partial': 0.00, 'value': 25.00},
    'S0006': {'name': 'Absolut Raspberry', 'size': '70cl', 'uom': 19.7, 'cost': 22.74, 'full': 2.00, 'partial': 0.30, 'value': 52.30},
    'S3214': {'name': 'Absolut Vanilla', 'size': '70cl', 'uom': 19.7, 'cost': 18.33, 'full': 2.00, 'partial': 0.80, 'value': 51.32},
    'S1019': {'name': 'Antica Sambuca Classic', 'size': '70cl', 'uom': 19.7, 'cost': 17.33, 'full': 0.00, 'partial': 0.90, 'value': 15.60},
    'S0002': {'name': 'Aperol', 'size': '70cl', 'uom': 19.7, 'cost': 13.26, 'full': 6.00, 'partial': 0.00, 'value': 79.56},
    'S1401': {'name': 'Apple Souz', 'size': '70cl', 'uom': 19.7, 'cost': 12.84, 'full': 3.00, 'partial': 0.10, 'value': 39.80},
    'S0045': {'name': 'Bacardi 1ltr', 'size': '1 Lt', 'uom': 28.2, 'cost': 24.82, 'full': 5.00, 'partial': 0.85, 'value': 145.20},
    'S29': {'name': 'Bacardi Oro Gold', 'size': '70cl', 'uom': 19.7, 'cost': 25.44, 'full': 1.00, 'partial': 0.60, 'value': 40.70},
    'S0074': {'name': 'Baileys 1 litre', 'size': '1 Lt', 'uom': 20.0, 'cost': 16.75, 'full': 7.00, 'partial': 0.20, 'value': 120.60},
    'S2058': {'name': 'Beefeater 24 Gin', 'size': '70cl', 'uom': 19.7, 'cost': 29.74, 'full': 1.00, 'partial': 0.80, 'value': 53.53},
    'S2033': {'name': 'Beefeeter Gin', 'size': '70cl', 'uom': 19.7, 'cost': 17.83, 'full': 1.00, 'partial': 0.45, 'value': 25.85},
    'S2055': {'name': 'Belvedere Vodka', 'size': '70cl', 'uom': 19.7, 'cost': 38.32, 'full': 2.00, 'partial': 0.50, 'value': 95.80},
    'S0065': {'name': 'Benedictine', 'size': '70cl', 'uom': 19.7, 'cost': 24.60, 'full': 2.00, 'partial': 0.00, 'value': 49.20},
    'S2148': {'name': 'Berthas Revenge Gin', 'size': '70cl', 'uom': 19.7, 'cost': 30.83, 'full': 2.00, 'partial': 0.55, 'value': 78.62},
    'S1400': {'name': 'Black & White 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 19.45, 'full': 0.00, 'partial': 0.90, 'value': 17.51},
    'S0080': {'name': 'Black Bush', 'size': '70cl', 'uom': 19.7, 'cost': 23.26, 'full': 3.00, 'partial': 0.45, 'value': 80.25},
    'S100': {'name': 'Boatyard Sloe Gin', 'size': '70cl', 'uom': 19.7, 'cost': 26.00, 'full': 4.00, 'partial': 0.00, 'value': 104.00},
    'S0215': {'name': 'Bols Blue Curacao', 'size': '70cl', 'uom': 19.7, 'cost': 17.01, 'full': 2.00, 'partial': 0.40, 'value': 40.82},
    'S0162': {'name': 'Bols Cherry Liquer', 'size': '50cl', 'uom': 14.1, 'cost': 13.07, 'full': 1.50, 'partial': 0.00, 'value': 19.61},
    'S1024': {'name': 'Bols Coconut', 'size': '70cl', 'uom': 19.7, 'cost': 16.09, 'full': 0.00, 'partial': 0.90, 'value': 14.48},
    'S0180': {'name': 'Bols Creme De Cacao B', 'size': '70cl', 'uom': 19.7, 'cost': 13.07, 'full': 2.00, 'partial': 0.00, 'value': 26.14},
    'S0190': {'name': 'Bols Creme De Cassis', 'size': '70cl', 'uom': 19.7, 'cost': 11.96, 'full': 2.00, 'partial': 0.10, 'value': 25.12},
    'S0195': {'name': 'Bols Creme Menthe G', 'size': '70cl', 'uom': 19.7, 'cost': 16.59, 'full': 1.00, 'partial': 0.90, 'value': 31.52},
    'S5555': {'name': 'Bols Peppermint White', 'size': '70cl', 'uom': 19.7, 'cost': 14.25, 'full': 2.00, 'partial': 0.00, 'value': 28.50},
    'S0009': {'name': 'Bols Strawberry', 'size': '70cl', 'uom': 19.7, 'cost': 17.17, 'full': 0.50, 'partial': 0.00, 'value': 8.59},
    'S0147': {'name': 'Bombay LTR', 'size': '1 Lt', 'uom': 28.2, 'cost': 29.75, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0100': {'name': 'Bombay Saphire 700 ML', 'size': '70cl', 'uom': 19.7, 'cost': 22.33, 'full': 1.00, 'partial': 0.45, 'value': 32.38},
    'S2314': {'name': 'Buffalo Trace 700ml', 'size': '70cl', 'uom': 19.7, 'cost': 18.67, 'full': 2.00, 'partial': 0.30, 'value': 42.94},
    'S2065': {'name': 'Bullet Bourbon', 'size': '70cl', 'uom': 19.7, 'cost': 30.34, 'full': 1.00, 'partial': 0.25, 'value': 37.93},
    'S0105': {'name': 'Bushmills 10 YO', 'size': '70cl', 'uom': 19.7, 'cost': 32.77, 'full': 3.00, 'partial': 0.55, 'value': 116.33},
    'S0027': {'name': 'Bushmills Caribben Rum', 'size': '70cl', 'uom': 19.7, 'cost': 24.78, 'full': 0.00, 'partial': 0.75, 'value': 18.59},
    'S0120': {'name': 'Bushmills Red 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 17.83, 'full': 3.00, 'partial': 0.90, 'value': 69.54},
    'S0130': {'name': 'Campari 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 18.17, 'full': 2.00, 'partial': 0.85, 'value': 51.78},
    'S0135': {'name': 'Canadian Club', 'size': '70cl', 'uom': 19.7, 'cost': 22.92, 'full': 4.00, 'partial': 0.00, 'value': 91.68},
    'S0140': {'name': 'Captain Morgans LTR', 'size': '1 Lt', 'uom': 28.2, 'cost': 23.50, 'full': 4.00, 'partial': 0.60, 'value': 108.10},
    'S0150': {'name': 'CDC LTR', 'size': '1 Lt', 'uom': 28.2, 'cost': 23.55, 'full': 7.00, 'partial': 0.35, 'value': 173.09},
    'S1203': {'name': 'Chambord', 'size': '50cl', 'uom': 14.1, 'cost': 16.75, 'full': 2.00, 'partial': 0.00, 'value': 33.50},
    'S0170': {'name': 'Cointreau', 'size': '70cl', 'uom': 19.7, 'cost': 23.17, 'full': 0.00, 'partial': 0.90, 'value': 20.85},
    'S0007': {'name': 'Corazon Tequila Anejo', 'size': '70cl', 'uom': 19.7, 'cost': 33.17, 'full': 6.00, 'partial': 0.20, 'value': 205.65},
    'S0205': {'name': 'Crested 10', 'size': '70cl', 'uom': 19.7, 'cost': 33.18, 'full': 2.00, 'partial': 0.55, 'value': 84.61},
    'S0220': {'name': 'Dark Rum', 'size': '70cl', 'uom': 19.7, 'cost': 17.13, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S3145': {'name': 'Dingle Gin 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 24.42, 'full': 20.00, 'partial': 0.10, 'value': 490.84},
    'S2369': {'name': 'Dingle Single Malt', 'size': '70cl', 'uom': 19.7, 'cost': 37.50, 'full': 3.00, 'partial': 0.35, 'value': 125.63},
    'S2034': {'name': 'Dingle Vodka 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 20.50, 'full': 13.00, 'partial': 0.50, 'value': 276.75},
    'S1587': {'name': 'Disaronno Amaretto', 'size': '70cl', 'uom': 19.7, 'cost': 19.58, 'full': 2.00, 'partial': 0.00, 'value': 39.16},
    'S0230': {'name': 'Drambuie', 'size': '70cl', 'uom': 19.7, 'cost': 31.50, 'full': 0.00, 'partial': 0.90, 'value': 28.35},
    'S0026': {'name': 'El Jimador Blanco', 'size': '70cl', 'uom': 19.7, 'cost': 26.66, 'full': 3.00, 'partial': 0.00, 'value': 79.98},
    'S0245': {'name': 'Famous Grouse 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 20.32, 'full': 2.00, 'partial': 0.70, 'value': 54.86},
    'S0265': {'name': 'Galliano', 'size': '50cl', 'uom': 14.1, 'cost': 24.53, 'full': 0.00, 'partial': 0.30, 'value': 7.36},
    'S0014': {'name': 'Ghost Spicy Tequila', 'size': '70cl', 'uom': 19.7, 'cost': 31.09, 'full': 1.00, 'partial': 0.30, 'value': 40.42},
    'S0271': {'name': 'Glenfiddich 12 YO', 'size': '70cl', 'uom': 19.7, 'cost': 38.38, 'full': 1.00, 'partial': 0.85, 'value': 71.00},
    'S0327': {'name': 'Glenmorangie', 'size': '70cl', 'uom': 19.7, 'cost': 38.33, 'full': 3.00, 'partial': 0.20, 'value': 122.66},
    'S002': {'name': 'Gordans Pink Litre', 'size': '1 Lt', 'uom': 28.2, 'cost': 25.83, 'full': 7.00, 'partial': 0.60, 'value': 196.31},
    'S0019': {'name': 'Gordons 0.0% 700ML', 'size': '70cl', 'uom': 19.7, 'cost': 14.64, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0306': {'name': 'Gordons Gin LTR', 'size': '1 Lt', 'uom': 28.2, 'cost': 24.88, 'full': 8.00, 'partial': 0.75, 'value': 217.70},
    'S0310': {'name': 'Grand Marnier 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 31.78, 'full': 3.00, 'partial': 0.95, 'value': 125.53},
    'S1412': {'name': 'Green Spot', 'size': '70cl', 'uom': 19.7, 'cost': 44.69, 'full': 15.00, 'partial': 0.25, 'value': 681.52},
    'S1258': {'name': 'Grey Goose', 'size': '70cl', 'uom': 19.7, 'cost': 36.17, 'full': 2.00, 'partial': 0.85, 'value': 103.08},
    'S0325': {'name': 'Harveys Bristol Cream', 'size': '75cl', 'uom': 10.6, 'cost': 10.66, 'full': 3.00, 'partial': 0.10, 'value': 33.05},
    'S0029': {'name': 'Havana 3YR', 'size': '70cl', 'uom': 19.7, 'cost': 18.50, 'full': 1.00, 'partial': 0.00, 'value': 18.50},
    'S2156': {'name': 'Havana Anejo', 'size': '70cl', 'uom': 19.7, 'cost': 21.35, 'full': 2.00, 'partial': 0.95, 'value': 62.98},
    'S2354': {'name': 'Havana Club 7 YO', 'size': '70cl', 'uom': 19.7, 'cost': 31.99, 'full': 1.00, 'partial': 0.10, 'value': 35.19},
    'S1302': {'name': 'Hendricks Gin', 'size': '70cl', 'uom': 19.7, 'cost': 32.67, 'full': 1.00, 'partial': 0.80, 'value': 58.81},
    'S0335': {'name': 'Hennessy 1Ltr', 'size': '1 Lt', 'uom': 28.2, 'cost': 44.06, 'full': 5.00, 'partial': 0.90, 'value': 259.95},
    'S0365': {'name': 'Irish Mist 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 22.67, 'full': 2.00, 'partial': 0.20, 'value': 49.87},
    'S0380': {'name': 'Jack Daniels', 'size': '70cl', 'uom': 19.7, 'cost': 24.18, 'full': 2.00, 'partial': 0.10, 'value': 50.78},
    'S0385': {'name': 'Jagermeister 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 16.92, 'full': 2.00, 'partial': 0.70, 'value': 45.68},
    'S2186': {'name': 'Jamesom Caskmate Stout', 'size': '70cl', 'uom': 19.7, 'cost': 31.38, 'full': 2.00, 'partial': 0.30, 'value': 72.17},
    'S0405': {'name': 'Jameson 1Ltr', 'size': '1 Lt', 'uom': 28.2, 'cost': 29.23, 'full': 17.00, 'partial': 0.80, 'value': 520.29},
    'S0255': {'name': 'Jameson Black Barrel', 'size': '70cl', 'uom': 19.7, 'cost': 42.01, 'full': 6.00, 'partial': 0.85, 'value': 287.77},
    'S2189': {'name': 'Jameson Caskmate IPA', 'size': '70cl', 'uom': 19.7, 'cost': 31.38, 'full': 3.00, 'partial': 0.70, 'value': 116.11},
    'S0370': {'name': 'Johnnie Walker Black', 'size': '70cl', 'uom': 19.7, 'cost': 32.65, 'full': 3.00, 'partial': 0.10, 'value': 101.22},
    'S1002': {'name': 'Johnny Walker Red', 'size': '70cl', 'uom': 19.7, 'cost': 21.05, 'full': 3.00, 'partial': 0.50, 'value': 73.68},
    'S0420': {'name': 'Kahlua', 'size': '70cl', 'uom': 19.7, 'cost': 13.58, 'full': 3.00, 'partial': 0.00, 'value': 40.74},
    'S1299': {'name': 'Kettle One', 'size': '70cl', 'uom': 19.7, 'cost': 22.00, 'full': 3.00, 'partial': 0.40, 'value': 74.80},
    'S0021': {'name': 'Killarney Whiskey', 'size': '70cl', 'uom': 19.7, 'cost': 30.50, 'full': 1.00, 'partial': 0.20, 'value': 36.60},
    'S9987': {'name': 'Krackan', 'size': '70cl', 'uom': 19.7, 'cost': 22.83, 'full': 7.00, 'partial': 0.25, 'value': 165.52},
    'S1101': {'name': 'Laphroaig 10 Year Old', 'size': '70cl', 'uom': 19.7, 'cost': 48.00, 'full': 1.00, 'partial': 0.15, 'value': 55.20},
    'S1205': {'name': 'Luxardo Limoncello', 'size': '70cl', 'uom': 19.7, 'cost': 18.95, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0455': {'name': 'Malibu', 'size': '70cl', 'uom': 19.7, 'cost': 13.17, 'full': 3.00, 'partial': 0.10, 'value': 40.83},
    'S2155': {'name': 'Martel VS', 'size': '70cl', 'uom': 19.7, 'cost': 31.69, 'full': 1.00, 'partial': 0.00, 'value': 31.69},
    'S0699': {'name': 'Martini Dry', 'size': '75cl', 'uom': 10.6, 'cost': 9.72, 'full': 6.00, 'partial': 0.50, 'value': 63.18},
    'S0485': {'name': 'Martini Rosso 75Cl', 'size': '75cl', 'uom': 10.6, 'cost': 9.72, 'full': 3.00, 'partial': 0.00, 'value': 29.16},
    'S2365': {'name': 'Matusalem Solera 7YO', 'size': '70cl', 'uom': 19.7, 'cost': 26.50, 'full': 1.00, 'partial': 0.35, 'value': 35.78},
    'S2349': {'name': 'Method & Madness Gin', 'size': '70cl', 'uom': 19.7, 'cost': 32.92, 'full': 0.00, 'partial': 0.40, 'value': 13.17},
    'S1047': {'name': 'Midori Green', 'size': '70cl', 'uom': 19.7, 'cost': 25.80, 'full': 0.00, 'partial': 0.90, 'value': 23.22},
    'S0064': {'name': 'Muckross Wild Gin', 'size': '70cl', 'uom': 19.7, 'cost': 28.33, 'full': 2.00, 'partial': 0.00, 'value': 56.66},
    'S0530': {'name': 'Paddy', 'size': '1 Lt', 'uom': 28.2, 'cost': 23.67, 'full': 2.00, 'partial': 0.30, 'value': 54.44},
    'S0041': {'name': 'Passoa Passionfruit Liqueur', 'size': '70cl', 'uom': 19.7, 'cost': 15.00, 'full': 1.00, 'partial': 0.00, 'value': 15.00},
    'S24': {'name': 'Patron Tequila Silver', 'size': '70cl', 'uom': 19.7, 'cost': 49.97, 'full': 1.00, 'partial': 0.40, 'value': 69.96},
    'S0543': {'name': 'Peach Schnapps 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 12.71, 'full': 9.00, 'partial': 0.40, 'value': 119.47},
    'S0545': {'name': 'Pernod 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 20.55, 'full': 1.00, 'partial': 0.90, 'value': 39.05},
    'S0550': {'name': 'Pimms No.1', 'size': '70cl', 'uom': 19.7, 'cost': 17.50, 'full': 0.00, 'partial': 0.05, 'value': 0.88},
    'S0555': {'name': 'Powers 1ltr', 'size': '1 Lt', 'uom': 28.2, 'cost': 32.64, 'full': 4.00, 'partial': 0.90, 'value': 159.94},
    'S2359': {'name': 'Powers 3 Swallows', 'size': '70cl', 'uom': 19.7, 'cost': 39.72, 'full': 2.00, 'partial': 0.10, 'value': 83.41},
    'S2241': {'name': 'Powers John Lane', 'size': '70cl', 'uom': 19.7, 'cost': 57.33, 'full': 1.00, 'partial': 0.75, 'value': 100.33},
    'S0575': {'name': 'Redbreast 12Yr', 'size': '70cl', 'uom': 19.7, 'cost': 46.67, 'full': 2.00, 'partial': 0.00, 'value': 93.34},
    'S1210': {'name': 'Redbreast 15 Years Old', 'size': '70cl', 'uom': 19.7, 'cost': 88.26, 'full': 2.00, 'partial': 0.70, 'value': 238.30},
    'S0585': {'name': 'Remy Martin Vsop', 'size': '70cl', 'uom': 19.7, 'cost': 43.06, 'full': 2.00, 'partial': 0.40, 'value': 103.34},
    'S0022': {'name': 'Ring Of Kerry Gin', 'size': '70cl', 'uom': 19.7, 'cost': 30.00, 'full': 4.00, 'partial': 0.90, 'value': 147.00},
    'S2302': {'name': 'Roe & Coe', 'size': '70cl', 'uom': 19.7, 'cost': 31.67, 'full': 1.00, 'partial': 0.30, 'value': 41.17},
    'S0605': {'name': 'Sandeman Port', 'size': '75cl', 'uom': 10.6, 'cost': 14.29, 'full': 1.00, 'partial': 0.85, 'value': 26.44},
    'S0018': {'name': 'Sarti Rosa Spritz', 'size': '70cl', 'uom': 9.9, 'cost': 16.48, 'full': 1.00, 'partial': 0.65, 'value': 27.19},
    'S2217': {'name': 'Silver Spear Gin', 'size': '70cl', 'uom': 19.7, 'cost': 33.34, 'full': 0.00, 'partial': 0.90, 'value': 30.01},
    'S0001': {'name': 'Skellig Six18Pot Still', 'size': '70cl', 'uom': 19.7, 'cost': 33.83, 'full': 3.00, 'partial': 0.00, 'value': 101.49},
    'S0610': {'name': 'Smirnoff 1Ltr', 'size': '1 Lt', 'uom': 28.2, 'cost': 21.83, 'full': 41.00, 'partial': 0.30, 'value': 901.58},
    'S0625': {'name': 'Southern Comfort', 'size': '70cl', 'uom': 19.7, 'cost': 13.75, 'full': 2.00, 'partial': 0.55, 'value': 35.06},
    'S0010': {'name': 'Talisker 10 YR', 'size': '70cl', 'uom': 19.7, 'cost': 53.03, 'full': 2.00, 'partial': 0.00, 'value': 106.06},
    'S0638': {'name': 'Tanquery 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 22.83, 'full': 2.00, 'partial': 0.00, 'value': 45.66},
    'S0630': {'name': 'Teachers 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 17.17, 'full': 0.00, 'partial': 0.05, 'value': 0.86},
    'S2159': {'name': 'Tequila Bianca', 'size': '70cl', 'uom': 19.7, 'cost': 17.67, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0012': {'name': 'Tequila J.C Gold', 'size': '70cl', 'uom': 19.7, 'cost': 18.17, 'full': 1.00, 'partial': 0.00, 'value': 18.17},
    'S0635': {'name': 'Tequila Olmeca Gold', 'size': '70cl', 'uom': 19.7, 'cost': 20.20, 'full': 6.00, 'partial': 0.60, 'value': 133.32},
    'S1022': {'name': 'Tequila Rose', 'size': '70cl', 'uom': 19.7, 'cost': 15.75, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0640': {'name': 'Tia Maria 70Cl', 'size': '70cl', 'uom': 19.7, 'cost': 15.33, 'full': 6.00, 'partial': 0.30, 'value': 96.58},
    'S0653': {'name': 'Tio Pepe', 'size': '70cl', 'uom': 9.9, 'cost': 13.81, 'full': 2.00, 'partial': 0.95, 'value': 40.74},
    'S3147': {'name': 'Tito s Vodka', 'size': '70cl', 'uom': 19.7, 'cost': 22.50, 'full': 7.00, 'partial': 0.15, 'value': 160.88},
    'S0647': {'name': 'Tullamore Dew 70cl', 'size': '70cl', 'uom': 19.7, 'cost': 22.57, 'full': 3.00, 'partial': 0.00, 'value': 67.71},
    'S0023': {'name': 'Volare Butterscotch', 'size': '70cl', 'uom': 19.7, 'cost': 12.92, 'full': 1.00, 'partial': 0.90, 'value': 24.55},
    'S0028': {'name': 'Volare Limoncello 700ML', 'size': '70cl', 'uom': 19.7, 'cost': 17.89, 'full': 1.00, 'partial': 0.85, 'value': 33.10},
    'S0017': {'name': 'Volare Passionfruit 700ML', 'size': 'Ind', 'uom': 1.0, 'cost': 13.89, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0005': {'name': 'Volare Triple sec', 'size': '70cl', 'uom': 19.7, 'cost': 13.40, 'full': 4.00, 'partial': 0.90, 'value': 65.66},
    'S2378': {'name': 'West Cork Irish Whiskey', 'size': '70cl', 'uom': 19.7, 'cost': 24.58, 'full': 0.00, 'partial': 0.00, 'value': 0.00},
    'S0071': {'name': 'Winters Tale 75cl', 'size': '75cl', 'uom': 10.7, 'cost': 12.42, 'full': 2.00, 'partial': 0.50, 'value': 31.05},
    'S1411': {'name': 'Yellow Spot', 'size': '70cl', 'uom': 19.7, 'cost': 61.04, 'full': 2.00, 'partial': 0.70, 'value': 164.81},
}

# Additional items from your list without SKU
additional_items = [
    {'name': 'Sea Dog Rum', 'cost': 17.13, 'full': 3.00, 'partial': 0.90, 'value': 66.81},
    {'name': 'Dingle Whiskey', 'cost': 37.50, 'full': 4.00, 'partial': 0.00, 'value': 150.00},
    {'name': 'Tanquery 70cl 0.0%', 'cost': 15.00, 'full': 5.00, 'partial': 0.30, 'value': 0.00},  # Value missing in Excel
]

# Calculate Excel total
excel_total = sum(item['value'] for item in excel_data.values())
excel_total += sum(item['value'] for item in additional_items)

print(f'\nEXCEL TOTAL: €{excel_total:,.2f}')
print(f'Expected Total: €11,063.66')
print()

# Get October 2025 stocktake
stocktake = Stocktake.objects.get(id=18)
spirits_lines = stocktake.lines.filter(
    item__category__code='S'
).select_related('item').order_by('item__sku')

print(f'SYSTEM TOTAL: {spirits_lines.count()} spirits items')
print()

# Compare each item
system_total = Decimal('0.00')
discrepancies = []
matched_count = 0
missing_in_system = []
missing_in_excel = []

print(f"{'SKU':<10} {'Name':<35} {'Excel €':<12} {'System €':<12} {'Diff €':<12} {'Status':<15}")
print("=" * 120)

# Check Excel items against system
for sku, excel_item in excel_data.items():
    system_line = spirits_lines.filter(item__sku=sku).first()
    
    if system_line:
        system_value = system_line.counted_value
        excel_value = Decimal(str(excel_item['value']))
        diff = system_value - excel_value
        
        system_total += system_value
        
        status = '✓ MATCH' if abs(diff) < Decimal('0.01') else '✗ DIFF'
        
        if abs(diff) >= Decimal('0.01'):
            discrepancies.append({
                'sku': sku,
                'name': excel_item['name'],
                'excel_value': excel_value,
                'system_value': system_value,
                'diff': diff,
                'excel_full': excel_item['full'],
                'excel_partial': excel_item['partial'],
                'system_full': system_line.counted_full_units,
                'system_partial': system_line.counted_partial_units,
            })
            print(f"{sku:<10} {excel_item['name']:<35} {excel_value:>11.2f} {system_value:>11.2f} {diff:>11.2f} {status:<15}")
        else:
            matched_count += 1
    else:
        missing_in_system.append({'sku': sku, 'name': excel_item['name'], 'value': excel_item['value']})
        print(f"{sku:<10} {excel_item['name']:<35} {excel_item['value']:>11.2f} {'MISSING':>11} {'---':>11} {'✗ NOT IN SYS':<15}")

# Check for items in system but not in Excel
for line in spirits_lines:
    if line.item.sku not in excel_data:
        missing_in_excel.append({
            'sku': line.item.sku,
            'name': line.item.name,
            'value': line.counted_value
        })
        system_total += line.counted_value
        print(f"{line.item.sku:<10} {line.item.name:<35} {'MISSING':>11} {line.counted_value:>11.2f} {'---':>11} {'✗ NOT IN EXCEL':<15}")

print("=" * 120)
print(f"\nSUMMARY:")
print(f"{'Excel Total:':<40} €{excel_total:>11,.2f}")
print(f"{'System Total:':<40} €{system_total:>11,.2f}")
print(f"{'Difference:':<40} €{(system_total - Decimal(str(excel_total))):>11,.2f}")
print()
print(f"Matched Items: {matched_count}")
print(f"Items with Discrepancies: {len(discrepancies)}")
print(f"Missing in System: {len(missing_in_system)}")
print(f"Missing in Excel: {len(missing_in_excel)}")

if discrepancies:
    print("\n" + "=" * 120)
    print("DETAILED DISCREPANCIES:")
    print("=" * 120)
    
    for disc in discrepancies:
        print(f"\n{disc['sku']} - {disc['name']}")
        print(f"  Excel:  {disc['excel_full']:.2f} bottles + {disc['excel_partial']:.2f} = €{disc['excel_value']:.2f}")
        print(f"  System: {disc['system_full']:.2f} bottles + {disc['system_partial']:.2f} = €{disc['system_value']:.2f}")
        print(f"  Difference: €{disc['diff']:.2f}")

if missing_in_system:
    print("\n" + "=" * 120)
    print("ITEMS IN EXCEL BUT NOT IN SYSTEM:")
    print("=" * 120)
    for item in missing_in_system:
        print(f"  {item['sku']} - {item['name']}: €{item['value']:.2f}")

if missing_in_excel:
    print("\n" + "=" * 120)
    print("ITEMS IN SYSTEM BUT NOT IN EXCEL:")
    print("=" * 120)
    for item in missing_in_excel:
        print(f"  {item['sku']} - {item['name']}: €{item['value']:.2f}")

print("\n" + "=" * 120)
