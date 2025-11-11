"""
Tests for stocktake and period export functionality (PDF and Excel).

Tests both access methods:
1. ID-based: /stocktakes/{id}/download-pdf/
2. Date-based: /stocktakes/download-pdf/?start_date=X&end_date=Y
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from decimal import Decimal

from hotel.models import Hotel
from .models import (
    Stocktake,
    StockPeriod,
    StockItem,
    StockCategory,
    Location
)

User = get_user_model()


class StocktakeExportTests(TestCase):
    """Test PDF and Excel exports for stocktakes."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            subdomain='test'
        )
        
        # Create stock category
        self.category = StockCategory.objects.create(
            hotel=self.hotel,
            code='D',
            name='Drinks'
        )
        
        # Create location
        self.location = Location.objects.create(
            hotel=self.hotel,
            name='Main Bar'
        )
        
        # Create stock items
        self.item1 = StockItem.objects.create(
            hotel=self.hotel,
            category=self.category,
            location=self.location,
            sku='ITEM001',
            name='Test Item 1',
            cost_price=Decimal('10.00'),
            selling_price=Decimal('20.00'),
            current_qty=Decimal('100'),
            reorder_level=Decimal('20')
        )
        
        self.item2 = StockItem.objects.create(
            hotel=self.hotel,
            category=self.category,
            location=self.location,
            sku='ITEM002',
            name='Test Item 2',
            cost_price=Decimal('15.00'),
            selling_price=Decimal('30.00'),
            current_qty=Decimal('50'),
            reorder_level=Decimal('10')
        )
        
        # Create test stocktake
        self.period_start = date(2024, 11, 1)
        self.period_end = date(2024, 11, 30)
        
        self.stocktake = Stocktake.objects.create(
            hotel=self.hotel,
            period_start=self.period_start,
            period_end=self.period_end,
            status=Stocktake.DRAFT
        )
        
        # Create stocktake lines
        from .models import StocktakeLine
        StocktakeLine.objects.create(
            stocktake=self.stocktake,
            item=self.item1,
            opening_qty=Decimal('100'),
            purchases=Decimal('50'),
            sales=Decimal('30'),
            waste=Decimal('5'),
            counted_qty=Decimal('115')
        )
        
        StocktakeLine.objects.create(
            stocktake=self.stocktake,
            item=self.item2,
            opening_qty=Decimal('50'),
            purchases=Decimal('20'),
            sales=Decimal('15'),
            waste=Decimal('2'),
            counted_qty=Decimal('53')
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Base URL
        self.base_url = f'/api/stock-tracker/{self.hotel.slug}'

    def test_download_stocktake_pdf_by_id(self):
        """Test downloading stocktake PDF using ID."""
        url = f'{self.base_url}/stocktakes/{self.stocktake.id}/download-pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertIn(
            '.pdf',
            response['Content-Disposition']
        )
        # Verify PDF content is not empty
        self.assertGreater(len(response.content), 0)

    def test_download_stocktake_pdf_by_date(self):
        """Test downloading stocktake PDF using date range."""
        url = (
            f'{self.base_url}/stocktakes/download-pdf/'
            f'?start_date={self.period_start}&end_date={self.period_end}'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_stocktake_pdf_by_date_missing_params(self):
        """Test date-based PDF download with missing parameters."""
        # Missing end_date
        url = (
            f'{self.base_url}/stocktakes/download-pdf/'
            f'?start_date={self.period_start}'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('required', response.data['error'].lower())

    def test_download_stocktake_pdf_by_date_invalid_format(self):
        """Test date-based PDF download with invalid date format."""
        url = (
            f'{self.base_url}/stocktakes/download-pdf/'
            f'?start_date=2024/11/01&end_date=2024/11/30'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('format', response.data['error'].lower())

    def test_download_stocktake_pdf_by_date_not_found(self):
        """Test date-based PDF download for non-existent stocktake."""
        url = (
            f'{self.base_url}/stocktakes/download-pdf/'
            f'?start_date=2025-01-01&end_date=2025-01-31'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_download_stocktake_excel_by_id(self):
        """Test downloading stocktake Excel using ID."""
        url = (
            f'{self.base_url}/stocktakes/{self.stocktake.id}/'
            f'download-excel/'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'spreadsheetml',
            response['Content-Type']
        )
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertIn(
            '.xlsx',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_stocktake_excel_by_date(self):
        """Test downloading stocktake Excel using date range."""
        url = (
            f'{self.base_url}/stocktakes/download-excel/'
            f'?start_date={self.period_start}&end_date={self.period_end}'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'spreadsheetml',
            response['Content-Type']
        )
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_stocktake_excel_by_date_not_found(self):
        """Test date-based Excel download for non-existent stocktake."""
        url = (
            f'{self.base_url}/stocktakes/download-excel/'
            f'?start_date=2025-01-01&end_date=2025-01-31'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_download_stocktake_pdf_unauthenticated(self):
        """Test that unauthenticated users cannot download."""
        self.client.force_authenticate(user=None)
        url = f'{self.base_url}/stocktakes/{self.stocktake.id}/download-pdf/'
        response = self.client.get(url)
        
        # Should be 401 or 403
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )


class StockPeriodExportTests(TestCase):
    """Test PDF and Excel exports for stock periods."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            subdomain='test'
        )
        
        # Create stock category
        self.category = StockCategory.objects.create(
            hotel=self.hotel,
            code='D',
            name='Drinks'
        )
        
        # Create location
        self.location = Location.objects.create(
            hotel=self.hotel,
            name='Main Bar'
        )
        
        # Create stock items
        self.item1 = StockItem.objects.create(
            hotel=self.hotel,
            category=self.category,
            location=self.location,
            sku='ITEM001',
            name='Test Item 1',
            cost_price=Decimal('10.00'),
            selling_price=Decimal('20.00'),
            current_qty=Decimal('100'),
            reorder_level=Decimal('20')
        )
        
        # Create test period
        self.period_start = date(2024, 11, 1)
        self.period_end = date(2024, 11, 30)
        
        self.period = StockPeriod.objects.create(
            hotel=self.hotel,
            start_date=self.period_start,
            end_date=self.period_end,
            period_name='November 2024',
            status=StockPeriod.OPEN
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Base URL
        self.base_url = f'/api/stock-tracker/{self.hotel.slug}'

    def test_download_period_pdf_by_id(self):
        """Test downloading period PDF using ID."""
        url = f'{self.base_url}/periods/{self.period.id}/download-pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertIn(
            '.pdf',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_period_pdf_by_id_with_cocktails_param(self):
        """Test PDF download with include_cocktails parameter."""
        url = (
            f'{self.base_url}/periods/{self.period.id}/download-pdf/'
            f'?include_cocktails=false'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.content), 0)

    def test_download_period_pdf_by_date(self):
        """Test downloading period PDF using date range."""
        url = (
            f'{self.base_url}/periods/download-pdf/'
            f'?start_date={self.period_start}&end_date={self.period_end}'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_period_pdf_by_date_with_cocktails(self):
        """Test date-based PDF with include_cocktails parameter."""
        url = (
            f'{self.base_url}/periods/download-pdf/'
            f'?start_date={self.period_start}&end_date={self.period_end}'
            f'&include_cocktails=false'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.content), 0)

    def test_download_period_pdf_by_date_missing_params(self):
        """Test date-based PDF download with missing parameters."""
        url = (
            f'{self.base_url}/periods/download-pdf/'
            f'?start_date={self.period_start}'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_download_period_pdf_by_date_not_found(self):
        """Test date-based PDF download for non-existent period."""
        url = (
            f'{self.base_url}/periods/download-pdf/'
            f'?start_date=2025-01-01&end_date=2025-01-31'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_download_period_excel_by_id(self):
        """Test downloading period Excel using ID."""
        url = f'{self.base_url}/periods/{self.period.id}/download-excel/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'spreadsheetml',
            response['Content-Type']
        )
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertIn(
            '.xlsx',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_period_excel_by_date(self):
        """Test downloading period Excel using date range."""
        url = (
            f'{self.base_url}/periods/download-excel/'
            f'?start_date={self.period_start}&end_date={self.period_end}'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            'spreadsheetml',
            response['Content-Type']
        )
        self.assertIn(
            'attachment',
            response['Content-Disposition']
        )
        self.assertGreater(len(response.content), 0)

    def test_download_period_excel_by_date_not_found(self):
        """Test date-based Excel download for non-existent period."""
        url = (
            f'{self.base_url}/periods/download-excel/'
            f'?start_date=2025-01-01&end_date=2025-01-31'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_download_period_excel_unauthenticated(self):
        """Test that unauthenticated users cannot download."""
        self.client.force_authenticate(user=None)
        url = f'{self.base_url}/periods/{self.period.id}/download-excel/'
        response = self.client.get(url)
        
        # Should be 401 or 403
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )


class MultipleStocktakesPerMonthTests(TestCase):
    """
    Test that date-based access works correctly when multiple
    stocktakes/periods exist for the same month.
    """

    def setUp(self):
        """Set up test data with multiple stocktakes per month."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            subdomain='test'
        )
        
        # Create stock category
        self.category = StockCategory.objects.create(
            hotel=self.hotel,
            code='D',
            name='Drinks'
        )
        
        # Create location
        self.location = Location.objects.create(
            hotel=self.hotel,
            name='Main Bar'
        )
        
        # Create stock item
        self.item = StockItem.objects.create(
            hotel=self.hotel,
            category=self.category,
            location=self.location,
            sku='ITEM001',
            name='Test Item 1',
            cost_price=Decimal('10.00'),
            selling_price=Decimal('20.00'),
            current_qty=Decimal('100'),
            reorder_level=Decimal('20')
        )
        
        # Create multiple stocktakes for November 2024 with different periods
        self.stocktake1 = Stocktake.objects.create(
            hotel=self.hotel,
            period_start=date(2024, 11, 1),
            period_end=date(2024, 11, 15),
            status=Stocktake.DRAFT
        )
        
        self.stocktake2 = Stocktake.objects.create(
            hotel=self.hotel,
            period_start=date(2024, 11, 16),
            period_end=date(2024, 11, 30),
            status=Stocktake.DRAFT
        )
        
        # Create multiple periods with different date ranges
        self.period1 = StockPeriod.objects.create(
            hotel=self.hotel,
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 15),
            period_name='November 1-15, 2024',
            status=StockPeriod.OPEN
        )
        
        self.period2 = StockPeriod.objects.create(
            hotel=self.hotel,
            start_date=date(2024, 11, 16),
            end_date=date(2024, 11, 30),
            period_name='November 16-30, 2024',
            status=StockPeriod.OPEN
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Base URL
        self.base_url = f'/api/stock-tracker/{self.hotel.slug}'

    def test_download_correct_stocktake_by_date_first_half(self):
        """Test that first half stocktake is returned for first half dates."""
        url = (
            f'{self.base_url}/stocktakes/download-pdf/'
            f'?start_date=2024-11-01&end_date=2024-11-15'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filename contains first half dates
        self.assertIn('2024-11-01', response['Content-Disposition'])
        self.assertIn('2024-11-15', response['Content-Disposition'])

    def test_download_correct_stocktake_by_date_second_half(self):
        """Test that second half stocktake is returned for second half dates."""
        url = (
            f'{self.base_url}/stocktakes/download-pdf/'
            f'?start_date=2024-11-16&end_date=2024-11-30'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify filename contains second half dates
        self.assertIn('2024-11-16', response['Content-Disposition'])
        self.assertIn('2024-11-30', response['Content-Disposition'])

    def test_download_correct_period_by_date_first_half(self):
        """Test that first half period is returned for first half dates."""
        url = (
            f'{self.base_url}/periods/download-pdf/'
            f'?start_date=2024-11-01&end_date=2024-11-15'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify correct period is used
        self.assertIn('November_1-15', response['Content-Disposition'])

    def test_download_correct_period_by_date_second_half(self):
        """Test that second half period is returned for second half dates."""
        url = (
            f'{self.base_url}/periods/download-pdf/'
            f'?start_date=2024-11-16&end_date=2024-11-30'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify correct period is used
        self.assertIn('November_16-30', response['Content-Disposition'])

    def test_download_by_id_still_works_with_multiple_periods(self):
        """Test that ID-based access still works with multiple periods."""
        # First stocktake by ID
        url = (
            f'{self.base_url}/stocktakes/{self.stocktake1.id}/'
            f'download-pdf/'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Second stocktake by ID
        url = (
            f'{self.base_url}/stocktakes/{self.stocktake2.id}/'
            f'download-pdf/'
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
