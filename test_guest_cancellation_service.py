"""
Tests for Guest Cancellation Service

Tests the Stripe-safe guest cancellation functionality with proper
authorization void/refund integration and idempotency protection.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from hotel.models import Hotel, RoomBooking, BookingManagementToken
from hotel.services.guest_cancellation import (
    cancel_booking_with_token,
    GuestCancellationError,
    StripeOperationError,
)
from rooms.models import RoomType


class GuestCancellationServiceTests(TestCase):
    """Test suite for guest cancellation service."""

    def setUp(self):
        """Set up test data."""
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            email="test@hotel.com"
        )
        
        # Create test room type
        self.room_type = RoomType.objects.create(
            name="Standard Room",
            hotel=self.hotel,
            base_price=Decimal("100.00"),
            max_occupancy=2
        )
        
        # Create base booking data
        self.booking_data = {
            'hotel': self.hotel,
            'room_type': self.room_type,
            'check_in': timezone.now().date(),
            'check_out': (timezone.now() + timezone.timedelta(days=2)).date(),
            'adults': 2,
            'children': 0,
            'total_amount': Decimal('200.00'),
            'primary_first_name': 'John',
            'primary_last_name': 'Doe',
            'primary_email': 'john@example.com',
            'payment_provider': 'stripe',
            'payment_intent_id': 'pi_test123456789'
        }

    def _create_booking_with_token(self, status='CONFIRMED', paid_at=None, **kwargs):
        """Helper to create booking with management token."""
        booking_data = {**self.booking_data, 'status': status, **kwargs}
        if paid_at:
            booking_data['paid_at'] = paid_at
            
        booking = RoomBooking.objects.create(**booking_data)
        
        # Create management token
        token = BookingManagementToken.objects.create(
            booking=booking,
            token_hash='test_hash_123',
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        return booking, token

    @patch('hotel.services.guest_cancellation.stripe.Refund.create')
    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_confirmed_stripe_booking_cancellation(self, mock_calculator_class, mock_refund_create):
        """Test CONFIRMED Stripe booking cancellation with refund."""
        # Setup
        booking, token = self._create_booking_with_token(
            status='CONFIRMED', 
            paid_at=timezone.now()
        )
        
        # Mock cancellation calculator
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('20.00'),
            'refund_amount': Decimal('180.00'),
            'description': 'Cancellation with fee'
        }
        
        # Mock Stripe refund
        mock_refund = MagicMock()
        mock_refund.id = 're_test123456789'
        mock_refund_create.return_value = mock_refund
        
        # Execute cancellation
        result = cancel_booking_with_token(
            booking=booking,
            token_obj=token,
            reason="Test cancellation"
        )
        
        # Verify Stripe refund called with correct parameters
        mock_refund_create.assert_called_once_with(
            payment_intent='pi_test123456789',
            amount=18000,  # 180.00 * 100 cents
            idempotency_key='guest_cancel_refund:' + booking.booking_id
        )
        
        # Verify booking updated correctly
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(booking.cancellation_fee, Decimal('20.00'))
        self.assertEqual(booking.refund_amount, Decimal('180.00'))
        self.assertEqual(booking.refund_reference, 're_test123456789')
        self.assertIsNotNone(booking.cancelled_at)
        self.assertIsNotNone(booking.refund_processed_at)
        
        # Verify token marked as used
        token.refresh_from_db()
        self.assertIsNotNone(token.used_at)
        
        # Verify response structure
        self.assertEqual(result['fee_amount'], Decimal('20.00'))
        self.assertEqual(result['refund_amount'], Decimal('180.00'))
        self.assertEqual(result['refund_reference'], 're_test123456789')
        self.assertIn('cancelled_at', result)

    @patch('hotel.services.guest_cancellation.stripe.PaymentIntent.cancel')
    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_pending_approval_stripe_booking_void(self, mock_calculator_class, mock_payment_cancel):
        """Test PENDING_APPROVAL Stripe booking void authorization."""
        # Setup
        booking, token = self._create_booking_with_token(
            status='PENDING_APPROVAL',
            paid_at=None  # Not captured yet
        )
        
        # Mock cancellation calculator
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('0.00'),
            'refund_amount': Decimal('200.00'),
            'description': 'Full refund - authorization void'
        }
        
        # Execute cancellation
        result = cancel_booking_with_token(
            booking=booking,
            token_obj=token,
            reason="Test void"
        )
        
        # Verify Stripe PaymentIntent.cancel called
        mock_payment_cancel.assert_called_once_with(
            'pi_test123456789',
            cancellation_reason='requested_by_customer'
        )
        
        # Verify booking updated correctly
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(booking.cancellation_fee, Decimal('0.00'))
        self.assertEqual(booking.refund_amount, Decimal('200.00'))
        self.assertEqual(booking.refund_reference, '')  # No refund object for voids
        self.assertIsNone(booking.refund_processed_at)  # No refund processed
        
        # Verify response
        self.assertEqual(result['refund_reference'], '')

    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_non_stripe_booking_cancellation(self, mock_calculator_class):
        """Test non-Stripe booking cancellation (DB-only)."""
        # Setup
        booking, token = self._create_booking_with_token(
            status='CONFIRMED',
            payment_provider='paypal',  # Non-Stripe
            payment_intent_id=None
        )
        
        # Mock cancellation calculator
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('10.00'),
            'refund_amount': Decimal('190.00'),
            'description': 'PayPal booking cancellation'
        }
        
        # Execute cancellation - should not call Stripe
        with patch('hotel.services.guest_cancellation.stripe') as mock_stripe:
            result = cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason="Test non-Stripe"
            )
            
            # Verify no Stripe calls
            mock_stripe.PaymentIntent.cancel.assert_not_called()
            mock_stripe.Refund.create.assert_not_called()
        
        # Verify booking updated
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(booking.refund_reference, '')

    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_already_cancelled_booking_idempotency(self, mock_calculator_class):
        """Test idempotent behavior for already cancelled bookings."""
        # Setup - pre-cancelled booking
        booking, token = self._create_booking_with_token(
            status='CANCELLED',
            cancelled_at=timezone.now(),
            cancellation_fee=Decimal('25.00'),
            refund_amount=Decimal('175.00')
        )
        
        # Execute cancellation - should return idempotent response
        result = cancel_booking_with_token(
            booking=booking,
            token_obj=token,
            reason="Retry cancellation"
        )
        
        # Verify calculator not called (no recalculation)
        mock_calculator_class.assert_not_called()
        
        # Verify idempotent response
        self.assertEqual(result['fee_amount'], Decimal('25.00'))
        self.assertEqual(result['refund_amount'], Decimal('175.00'))
        self.assertEqual(result['applied_rule'], 'ALREADY_CANCELLED')

    @patch('hotel.services.guest_cancellation.stripe.Refund.create')
    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_refund_idempotency_guard(self, mock_calculator_class, mock_refund_create):
        """Test refund idempotency guard prevents double refunds."""
        # Setup - booking with refund already processed
        booking, token = self._create_booking_with_token(
            status='CONFIRMED',
            paid_at=timezone.now(),
            refund_processed_at=timezone.now(),  # Already processed
            refund_reference='re_existing123'
        )
        
        # Mock calculator
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('20.00'),
            'refund_amount': Decimal('180.00'),
            'description': 'Cancellation with fee'
        }
        
        # Execute cancellation
        result = cancel_booking_with_token(
            booking=booking,
            token_obj=token,
            reason="Retry cancellation"
        )
        
        # Verify Stripe refund NOT called again
        mock_refund_create.assert_not_called()
        
        # Verify existing refund reference preserved
        self.assertEqual(result['refund_reference'], 're_existing123')

    def test_invalid_booking_status_error(self):
        """Test error for bookings that cannot be cancelled."""
        # Setup - completed booking
        booking, token = self._create_booking_with_token(status='COMPLETED')
        
        # Execute and expect error
        with self.assertRaises(GuestCancellationError) as cm:
            cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason="Invalid attempt"
            )
        
        self.assertIn('cannot be cancelled', str(cm.exception))

    @patch('hotel.services.guest_cancellation.stripe.Refund.create')
    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_stripe_error_handling(self, mock_calculator_class, mock_refund_create):
        """Test Stripe error handling and transaction rollback."""
        import stripe
        
        # Setup
        booking, token = self._create_booking_with_token(
            status='CONFIRMED',
            paid_at=timezone.now()
        )
        
        # Mock calculator
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('20.00'),
            'refund_amount': Decimal('180.00'),
            'description': 'Test cancellation'
        }
        
        # Mock Stripe error
        mock_refund_create.side_effect = stripe.error.CardError(
            message='Your card was declined.',
            param='card',
            code='card_declined'
        )
        
        # Execute and expect StripeOperationError
        with self.assertRaises(StripeOperationError):
            cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason="Stripe error test"
            )
        
        # Verify booking NOT marked as cancelled due to transaction rollback
        booking.refresh_from_db()
        self.assertNotEqual(booking.status, 'CANCELLED')
        self.assertIsNone(booking.cancelled_at)
        
        # Verify token NOT marked as used
        token.refresh_from_db()
        self.assertIsNone(token.used_at)

    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_zero_refund_amount_no_stripe_call(self, mock_calculator_class):
        """Test that zero refund amount doesn't call Stripe refund."""
        # Setup
        booking, token = self._create_booking_with_token(
            status='CONFIRMED',
            paid_at=timezone.now()
        )
        
        # Mock calculator with zero refund
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('200.00'),  # Full fee
            'refund_amount': Decimal('0.00'),  # No refund
            'description': 'Late cancellation - no refund'
        }
        
        # Execute cancellation - should not call Stripe
        with patch('hotel.services.guest_cancellation.stripe.Refund.create') as mock_refund:
            result = cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason="Late cancellation"
            )
            
            # Verify no Stripe refund call
            mock_refund.assert_not_called()
        
        # Verify booking still cancelled
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(result['refund_reference'], '')

    @patch('hotel.services.guest_cancellation.CancellationCalculator')
    def test_missing_payment_intent_id_fallback(self, mock_calculator_class):
        """Test safe fallback when payment_intent_id is missing."""
        # Setup - Stripe booking but missing payment_intent_id
        booking, token = self._create_booking_with_token(
            status='CONFIRMED',
            payment_provider='stripe',
            payment_intent_id='',  # Empty string
            paid_at=timezone.now()
        )
        
        # Mock calculator
        mock_calculator = mock_calculator_class.return_value
        mock_calculator.calculate.return_value = {
            'fee_amount': Decimal('20.00'),
            'refund_amount': Decimal('180.00'),
            'description': 'Cancellation fallback'
        }
        
        # Execute cancellation - should not call Stripe but still cancel
        with patch('hotel.services.guest_cancellation.stripe') as mock_stripe:
            result = cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason="Missing payment ID"
            )
            
            # Verify no Stripe calls
            mock_stripe.Refund.create.assert_not_called()
            mock_stripe.PaymentIntent.cancel.assert_not_called()
        
        # Verify booking still cancelled (safe fallback)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertEqual(result['refund_reference'], '')