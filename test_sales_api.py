"""
Test script to verify Sales API endpoints are working correctly.

This script tests all sales-related endpoints to ensure the backend
is properly configured for frontend integration.

Run with: python test_sales_api.py
"""

import requests
import json
from datetime import date, timedelta


class SalesAPITester:
    def __init__(self, base_url, hotel_identifier, auth_token=None):
        self.base_url = base_url.rstrip('/')
        self.hotel_identifier = hotel_identifier
        self.auth_token = auth_token
        self.headers = {'Content-Type': 'application/json'}
        
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
    
    def get_url(self, endpoint):
        """Build full URL for endpoint"""
        return f"{self.base_url}/api/stock-tracker/{self.hotel_identifier}/{endpoint}"
    
    def test_list_sales(self, stocktake_id=None):
        """Test: GET /sales/"""
        print("\n=== TEST: List Sales ===")
        
        url = self.get_url("sales/")
        if stocktake_id:
            url += f"?stocktake={stocktake_id}"
        
        response = requests.get(url, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} sales")
            if data:
                print(f"Sample: {json.dumps(data[0], indent=2)}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_create_sale(self, stocktake_id, item_id, quantity, unit_cost, unit_price):
        """Test: POST /sales/"""
        print("\n=== TEST: Create Sale ===")
        
        url = self.get_url("sales/")
        payload = {
            "stocktake": stocktake_id,
            "item": item_id,
            "quantity": str(quantity),
            "unit_cost": str(unit_cost),
            "unit_price": str(unit_price),
            "sale_date": date.today().isoformat(),
            "notes": "Test sale from API tester"
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ Success! Sale created:")
            print(f"  ID: {data['id']}")
            print(f"  Quantity: {data['quantity']}")
            print(f"  Revenue: €{data['total_revenue']}")
            print(f"  GP%: {data['gross_profit_percentage']}%")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_update_sale(self, sale_id, quantity=None, unit_price=None):
        """Test: PATCH /sales/{id}/"""
        print("\n=== TEST: Update Sale ===")
        
        url = self.get_url(f"sales/{sale_id}/")
        payload = {}
        if quantity:
            payload['quantity'] = str(quantity)
        if unit_price:
            payload['unit_price'] = str(unit_price)
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.patch(url, json=payload, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Sale updated:")
            print(f"  Quantity: {data['quantity']}")
            print(f"  Revenue: €{data['total_revenue']}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_delete_sale(self, sale_id):
        """Test: DELETE /sales/{id}/"""
        print("\n=== TEST: Delete Sale ===")
        
        url = self.get_url(f"sales/{sale_id}/")
        
        response = requests.delete(url, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 204:
            print("✅ Success! Sale deleted")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    
    def test_sales_summary(self, stocktake_id):
        """Test: GET /sales/summary/"""
        print("\n=== TEST: Sales Summary ===")
        
        url = self.get_url(f"sales/summary/?stocktake={stocktake_id}")
        
        response = requests.get(url, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Summary retrieved:")
            print(f"  Overall Revenue: €{data['overall'].get('total_revenue', 0)}")
            print(f"  Overall GP%: {data['overall'].get('gross_profit_percentage', 0)}%")
            print(f"  Categories: {len(data['by_category'])}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_line_sales(self, line_id):
        """Test: GET /stocktake-lines/{id}/sales/"""
        print("\n=== TEST: Line Item Sales ===")
        
        url = self.get_url(f"stocktake-lines/{line_id}/sales/")
        
        response = requests.get(url, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Line sales retrieved:")
            print(f"  Item: {data['item']['name']}")
            print(f"  Sales Count: {data['summary']['sale_count']}")
            print(f"  Total Quantity: {data['summary']['total_quantity']}")
            print(f"  Total Revenue: €{data['summary']['total_revenue']}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def test_bulk_create(self, stocktake_id, sales_data):
        """Test: POST /sales/bulk_create/"""
        print("\n=== TEST: Bulk Create Sales ===")
        
        url = self.get_url("sales/bulk_create/")
        payload = {"sales": sales_data}
        
        print(f"Creating {len(sales_data)} sales...")
        
        response = requests.post(url, json=payload, headers=self.headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [201, 207]:
            data = response.json()
            print(f"✅ {data['message']}")
            print(f"  Created: {data['created_count']}")
            if 'errors' in data:
                print(f"  Errors: {len(data['errors'])}")
            return data
        else:
            print(f"❌ Error: {response.text}")
            return None
    
    def run_full_test_suite(self, stocktake_id, item_id, line_id=None):
        """Run complete test suite"""
        print("\n" + "="*60)
        print("SALES API TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Hotel: {self.hotel_identifier}")
        print(f"Stocktake ID: {stocktake_id}")
        print(f"Item ID: {item_id}")
        print("="*60)
        
        # Test 1: List existing sales
        existing_sales = self.test_list_sales(stocktake_id)
        
        # Test 2: Create a new sale
        new_sale = self.test_create_sale(
            stocktake_id=stocktake_id,
            item_id=item_id,
            quantity=100,
            unit_cost=0.50,
            unit_price=5.00
        )
        
        if new_sale:
            sale_id = new_sale['id']
            
            # Test 3: Update the sale
            self.test_update_sale(sale_id, quantity=150)
            
            # Test 4: Get sales summary
            self.test_sales_summary(stocktake_id)
            
            # Test 5: Get line item sales (if line_id provided)
            if line_id:
                self.test_line_sales(line_id)
            
            # Test 6: Delete the sale
            self.test_delete_sale(sale_id)
        
        # Test 7: Bulk create
        bulk_data = [
            {
                "stocktake": stocktake_id,
                "item": item_id,
                "quantity": "50.0000",
                "unit_cost": "0.50",
                "unit_price": "5.00",
                "sale_date": date.today().isoformat()
            },
            {
                "stocktake": stocktake_id,
                "item": item_id,
                "quantity": "75.0000",
                "unit_cost": "0.50",
                "unit_price": "5.00",
                "sale_date": (date.today() - timedelta(days=1)).isoformat()
            }
        ]
        bulk_result = self.test_bulk_create(stocktake_id, bulk_data)
        
        # Clean up bulk sales if created
        if bulk_result and bulk_result.get('created_count', 0) > 0:
            print("\n=== CLEANUP: Deleting test sales ===")
            cleanup_sales = self.test_list_sales(stocktake_id)
            if cleanup_sales:
                for sale in cleanup_sales:
                    if 'Test sale' in sale.get('notes', ''):
                        self.test_delete_sale(sale['id'])
        
        print("\n" + "="*60)
        print("TEST SUITE COMPLETE")
        print("="*60)


def main():
    """
    Main test runner
    
    USAGE:
    1. Update the configuration below with your details
    2. Run: python test_sales_api.py
    """
    
    # ====== CONFIGURATION ======
    BASE_URL = "http://localhost:8000"  # Your backend URL
    HOTEL_IDENTIFIER = "myhotel"         # Your hotel slug/subdomain
    AUTH_TOKEN = None                     # Your JWT token (if required)
    
    # Test data
    STOCKTAKE_ID = 1                      # Existing stocktake ID
    ITEM_ID = 1                           # Existing item ID
    LINE_ID = 1                           # Existing stocktake line ID (optional)
    # ===========================
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                   SALES API TEST SCRIPT                        ║
║                                                                ║
║  This script will test all sales endpoints to verify that     ║
║  the backend is ready for frontend integration.               ║
║                                                                ║
║  IMPORTANT: Update the configuration above before running!    ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Create tester instance
    tester = SalesAPITester(BASE_URL, HOTEL_IDENTIFIER, AUTH_TOKEN)
    
    # Run tests
    try:
        tester.run_full_test_suite(STOCKTAKE_ID, ITEM_ID, LINE_ID)
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
