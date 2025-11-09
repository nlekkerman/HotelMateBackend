"""
Django Test: Simulate Frontend Movement Entry

This test uses Django's test framework to simulate the complete flow
WITHOUT needing a running server.

Run with: python manage.py test stock_tracker.test_movement_api
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from decimal import Decimal
import json

from stock_tracker.models import (
    StocktakeLine, Stocktake, StockMovement
)
from hotel.models import Hotel

User = get_user_model()


class MovementAPITest(TestCase):
    """Test the movement API endpoints"""

    def setUp(self):
        """Set up test data"""
        # Get or create hotel
        self.hotel = Hotel.objects.first()
        if not self.hotel:
            print("No hotel found in database!")
            return

        # Get a draft stocktake
        self.stocktake = Stocktake.objects.filter(
            status='DRAFT',
            hotel=self.hotel
        ).first()

        if not self.stocktake:
            print("No DRAFT stocktake found!")
            return

        # Get a line from this stocktake
        self.line = StocktakeLine.objects.filter(
            stocktake=self.stocktake
        ).select_related('item').first()

        if not self.line:
            print("No stocktake lines found!")
            return

        # Set up API client
        self.client = APIClient()

        print("\n" + "="*70)
        print("TEST SETUP")
        print("="*70)
        print(f"Hotel: {self.hotel.name} (ID: {self.hotel.id})")
        print(f"Stocktake: {self.stocktake.id} ({self.stocktake.status})")
        print(f"Test Line: {self.line.id}")
        print(f"Item: {self.line.item.sku} - {self.line.item.name}")
        print("="*70 + "\n")

    def test_add_purchase_movement(self):
        """Test adding a PURCHASE movement to a line"""
        
        if not hasattr(self, 'line'):
            self.skipTest("No test data available")

        print("\n" + "="*70)
        print("TEST: Add PURCHASE Movement")
        print("="*70)

        # Get initial state
        initial_purchases = self.line.purchases
        initial_expected = self.line.expected_qty
        initial_variance = self.line.variance_qty

        print(f"\n📊 BEFORE:")
        print(f"   Purchases: {initial_purchases}")
        print(f"   Expected:  {initial_expected}")
        print(f"   Variance:  {initial_variance}")

        # Simulate frontend payload
        payload = {
            "movement_type": "PURCHASE",
            "quantity": 24,
            "reference": "TEST-INV-123",
            "notes": "Test purchase from unit test"
        }

        print(f"\n📤 Sending Payload:")
        print(json.dumps(payload, indent=2))

        # Make request
        url = f'/api/stock_tracker/{self.hotel.id}/stocktake-lines/{self.line.id}/add-movement/'
        print(f"\nPOST {url}")

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        print(f"\n📥 Response Status: {response.status_code}")

        # Check response
        self.assertEqual(response.status_code, 201)

        data = response.json()
        
        print(f"\n✅ Movement Created:")
        print(f"   ID: {data['movement']['id']}")
        print(f"   Type: {data['movement']['movement_type']}")
        print(f"   Quantity: {data['movement']['quantity']}")

        # Check the line data was updated
        updated_line = data['line']
        
        print(f"\n📊 AFTER:")
        print(f"   Purchases: {updated_line['purchases']}")
        print(f"   Expected:  {updated_line['expected_qty']}")
        print(f"   Variance:  {updated_line['variance_qty']}")

        # Verify changes
        new_purchases = Decimal(updated_line['purchases'])
        new_expected = Decimal(updated_line['expected_qty'])
        
        purchases_change = new_purchases - initial_purchases
        expected_change = new_expected - initial_expected

        print(f"\n📈 CHANGES:")
        print(f"   Purchases: +{purchases_change}")
        print(f"   Expected:  +{expected_change}")

        # Assert the movement was added
        self.assertEqual(purchases_change, Decimal('24'))
        self.assertEqual(expected_change, Decimal('24'))

        # Verify the movement exists in database
        movement = StockMovement.objects.get(
            id=data['movement']['id']
        )
        self.assertEqual(movement.quantity, Decimal('24'))
        self.assertEqual(movement.movement_type, 'PURCHASE')
        
        print(f"\n✅ All assertions passed!")

    def test_add_sale_movement(self):
        """Test adding a SALE movement"""
        
        if not hasattr(self, 'line'):
            self.skipTest("No test data available")

        print("\n" + "="*70)
        print("TEST: Add SALE Movement")
        print("="*70)

        initial_sales = self.line.sales
        initial_expected = self.line.expected_qty

        print(f"\n📊 BEFORE:")
        print(f"   Sales:    {initial_sales}")
        print(f"   Expected: {initial_expected}")

        payload = {
            "movement_type": "SALE",
            "quantity": 15,
            "reference": "TEST-SALE-001"
        }

        url = f'/api/stock_tracker/{self.hotel.id}/stocktake-lines/{self.line.id}/add-movement/'
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        updated_line = data['line']

        print(f"\n📊 AFTER:")
        print(f"   Sales:    {updated_line['sales']}")
        print(f"   Expected: {updated_line['expected_qty']}")

        new_sales = Decimal(updated_line['sales'])
        new_expected = Decimal(updated_line['expected_qty'])

        sales_change = new_sales - initial_sales
        expected_change = new_expected - initial_expected

        print(f"\n📈 CHANGES:")
        print(f"   Sales:    +{sales_change}")
        print(f"   Expected: {expected_change}")

        # Sales should increase by 15, expected should decrease by 15
        self.assertEqual(sales_change, Decimal('15'))
        self.assertEqual(expected_change, Decimal('-15'))

        print(f"\n✅ All assertions passed!")

    def test_get_movements_for_line(self):
        """Test fetching all movements for a line"""
        
        if not hasattr(self, 'line'):
            self.skipTest("No test data available")

        print("\n" + "="*70)
        print("TEST: Get All Movements for Line")
        print("="*70)

        # Add a couple movements first
        for i, movement_type in enumerate(['PURCHASE', 'WASTE']):
            StockMovement.objects.create(
                hotel=self.hotel,
                item=self.line.item,
                period=self.stocktake.period,
                movement_type=movement_type,
                quantity=Decimal('10'),
                reference=f'TEST-{i}'
            )

        # Get movements
        url = f'/api/stock_tracker/{self.hotel.id}/stocktake-lines/{self.line.id}/movements/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        print(f"\n📋 Movement Summary:")
        print(f"   Total Movements: {data['summary']['movement_count']}")
        print(f"   Total Purchases: {data['summary']['total_purchases']}")
        print(f"   Total Sales:     {data['summary']['total_sales']}")
        print(f"   Total Waste:     {data['summary']['total_waste']}")

        print(f"\n📝 Individual Movements:")
        for m in data['movements'][:5]:
            print(f"   #{m['id']}: {m['movement_type']:<12} "
                  f"Qty: {m['quantity']:<10} Ref: {m['reference']}")

        self.assertGreaterEqual(
            data['summary']['movement_count'], 
            2
        )

        print(f"\n✅ All assertions passed!")

    def test_formula_verification(self):
        """Test that the expected_qty formula is correct"""
        
        if not hasattr(self, 'line'):
            self.skipTest("No test data available")

        print("\n" + "="*70)
        print("TEST: Formula Verification")
        print("="*70)

        # Refresh line from database
        self.line.refresh_from_db()

        opening = self.line.opening_qty
        purchases = self.line.purchases
        sales = self.line.sales
        waste = self.line.waste
        transfers_in = self.line.transfers_in
        transfers_out = self.line.transfers_out
        adjustments = self.line.adjustments

        calculated = (opening + purchases - sales - waste + 
                     transfers_in - transfers_out + adjustments)
        
        actual = self.line.expected_qty

        print(f"\n📐 Formula Test:")
        print(f"   Opening:      {opening}")
        print(f"   + Purchases:  {purchases}")
        print(f"   - Sales:      {sales}")
        print(f"   - Waste:      {waste}")
        print(f"   + TransferIn: {transfers_in}")
        print(f"   - TransferOut:{transfers_out}")
        print(f"   + Adjustments:{adjustments}")
        print(f"   ───────────────────────")
        print(f"   Calculated:   {calculated}")
        print(f"   Actual:       {actual}")

        self.assertEqual(calculated, actual)

        print(f"\n✅ Formula is correct!")


def run_tests():
    """Helper function to run these tests"""
    import sys
    from django.core.management import call_command
    
    print("\n" + "="*70)
    print("RUNNING MOVEMENT API TESTS")
    print("="*70)
    
    call_command('test', 'stock_tracker.test_movement_api', verbosity=2)


if __name__ == '__main__':
    run_tests()
