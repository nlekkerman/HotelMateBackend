"""
Comprehensive tests for Stripe payment integration.
Tests payment session creation, webhook handling, idempotency, and caching.
"""
from django.test import TestCase, override_settings
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from hotel.payment_cache import (
    generate_idempotency_key,
    store_payment_session,
    get_payment_session,
    is_webhook_processed,
    mark_webhook_processed,
    get_idempotency_session,
    store_idempotency_session,
)


class PaymentCacheTests(TestCase):
    """Test payment cache utility functions."""
    
    def setUp(self):
        """Clear cache before each test."""
        cache.clear()
    
    def test_generate_idempotency_key(self):
        """Test idempotency key generation."""
        key1 = generate_idempotency_key('BK-2025-TEST01', 'test@example.com')
        key2 = generate_idempotency_key('BK-2025-TEST01', 'test@example.com')
        key3 = generate_idempotency_key('BK-2025-TEST02', 'test@example.com')
        
        # Same input should generate same key
        self.assertEqual(key1, key2)
        # Different booking_id should generate different key
        self.assertNotEqual(key1, key3)
        # Key should start with idem_
        self.assertTrue(key1.startswith('idem_'))
    
    def test_store_and_get_payment_session(self):
        """Test storing and retrieving payment sessions."""
        booking_id = 'BK-2025-TEST01'
        session_data = {
            'session_id': 'cs_test_123',
            'booking_id': booking_id,
            'amount': '100.00',
            'currency': 'eur',
        }
        
        # Store session
        result = store_payment_session(booking_id, session_data)
        self.assertTrue(result)
        
        # Retrieve session
        retrieved = get_payment_session(booking_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['session_id'], 'cs_test_123')
        self.assertEqual(retrieved['booking_id'], booking_id)
    
    def test_webhook_deduplication(self):
        """Test webhook event deduplication."""
        event_id = 'evt_test_123'
        
        # First check - should not be processed
        self.assertFalse(is_webhook_processed(event_id))
        
        # Mark as processed
        mark_webhook_processed(event_id)
        
        # Second check - should be processed
        self.assertTrue(is_webhook_processed(event_id))
    
    def test_idempotency_session_storage(self):
        """Test storing and retrieving idempotency sessions."""
        idempotency_key = 'idem_test123'
        session_id = 'cs_test_456'
        
        # Store
        store_idempotency_session(idempotency_key, session_id)
        
        # Retrieve
        retrieved = get_idempotency_session(idempotency_key)
        self.assertEqual(retrieved, session_id)


@override_settings(
    STRIPE_SECRET_KEY='sk_test_fake',
    STRIPE_PUBLISHABLE_KEY='pk_test_fake',
    STRIPE_WEBHOOK_SECRET='whsec_fake'
)
class CreatePaymentSessionViewTests(TestCase):
    """Test payment session creation endpoint."""
    
    def setUp(self):
        """Set up test client and clear cache."""
        self.client = APIClient()
        cache.clear()
        
        self.booking_data = {
            'booking': {
                'hotel': {
                    'name': 'Test Hotel',
                    'slug': 'test-hotel'
                },
                'room': {
                    'type': 'Deluxe Room',
                    'photo': 'https://example.com/room.jpg'
                },
                'dates': {
                    'check_in': '2025-12-01',
                    'check_out': '2025-12-05',
                    'nights': 4
                },
                'guest': {
                    'name': 'John Doe',
                    'email': 'john@example.com'
                },
                'pricing': {
                    'total': '400.00',
                    'currency': 'EUR'
                }
            }
        }
    
    @patch('stripe.checkout.Session.create')
    def test_create_payment_session_success(self, mock_stripe_create):
        """Test successful payment session creation."""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_session.status = 'open'
        mock_stripe_create.return_value = mock_session
        
        response = self.client.post(
            '/api/hotel/bookings/BK-2025-TEST01/payment/session/',
            data=self.booking_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], 'cs_test_123')
        self.assertEqual(response.data['status'], 'created')
        self.assertEqual(response.data['amount'], '400.00')
    
    def test_create_payment_session_missing_booking_data(self):
        """Test error when booking data is missing."""
        response = self.client.post(
            '/api/hotel/bookings/BK-2025-TEST01/payment/session/',
            data={},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_create_payment_session_missing_email(self):
        """Test error when guest email is missing."""
        booking_data = self.booking_data.copy()
        booking_data['booking']['guest'] = {'name': 'John Doe'}
        
        response = self.client.post(
            '/api/hotel/bookings/BK-2025-TEST01/payment/session/',
            data=booking_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['detail'].lower())
    
    @patch('stripe.checkout.Session.retrieve')
    @patch('stripe.checkout.Session.create')
    def test_idempotency_returns_existing_session(
        self,
        mock_stripe_create,
        mock_stripe_retrieve
    ):
        """Test that duplicate requests return existing session."""
        # Mock first session creation
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_session.status = 'open'
        mock_session.amount_total = 40000
        mock_session.currency = 'eur'
        mock_stripe_create.return_value = mock_session
        mock_stripe_retrieve.return_value = mock_session
        
        # First request
        response1 = self.client.post(
            '/api/hotel/bookings/BK-2025-TEST01/payment/session/',
            data=self.booking_data,
            format='json'
        )
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['status'], 'created')
        
        # Second request with same data
        response2 = self.client.post(
            '/api/hotel/bookings/BK-2025-TEST01/payment/session/',
            data=self.booking_data,
            format='json'
        )
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['status'], 'existing')
        self.assertEqual(response2.data['session_id'], 'cs_test_123')
        
        # Stripe create should only be called once
        self.assertEqual(mock_stripe_create.call_count, 1)
    
    @patch('stripe.checkout.Session.create')
    def test_stripe_error_handling(self, mock_stripe_create):
        """Test error handling when Stripe API fails."""
        import stripe
        mock_stripe_create.side_effect = stripe.error.StripeError(
            'Test error'
        )
        
        response = self.client.post(
            '/api/hotel/bookings/BK-2025-TEST01/payment/session/',
            data=self.booking_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)


@override_settings(
    STRIPE_SECRET_KEY='sk_test_fake',
    STRIPE_WEBHOOK_SECRET='whsec_fake',
    EMAIL_HOST_USER='test@example.com'
)
class StripeWebhookViewTests(TestCase):
    """Test Stripe webhook handling."""
    
    def setUp(self):
        """Set up test client and clear cache."""
        self.client = APIClient()
        cache.clear()
    
    @patch('stripe.Webhook.construct_event')
    @patch('django.core.mail.send_mail')
    def test_webhook_checkout_completed(
        self,
        mock_send_mail,
        mock_construct_event
    ):
        """Test webhook handling for successful checkout."""
        # Mock Stripe event
        mock_event = {
            'id': 'evt_test_123',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer_email': 'customer@example.com',
                    'amount_total': 40000,
                    'currency': 'eur',
                    'metadata': {
                        'booking_id': 'BK-2025-TEST01',
                        'hotel_slug': 'test-hotel',
                        'guest_name': 'John Doe',
                        'check_in': '2025-12-01',
                        'check_out': '2025-12-05',
                    }
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        response = self.client.post(
            '/api/hotel/bookings/stripe-webhook/',
            data={},
            format='json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify email was sent
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertIn('BK-2025-TEST01', call_args[1]['subject'])
        self.assertIn('customer@example.com', call_args[1]['recipient_list'])
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_deduplication(self, mock_construct_event):
        """Test that duplicate webhooks are ignored."""
        mock_event = {
            'id': 'evt_test_duplicate',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer_email': 'test@example.com',
                    'amount_total': 10000,
                    'currency': 'eur',
                    'metadata': {
                        'booking_id': 'BK-2025-TEST01',
                        'hotel_slug': 'test-hotel',
                        'guest_name': 'Test',
                        'check_in': '2025-12-01',
                        'check_out': '2025-12-02',
                    }
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        # First webhook
        response1 = self.client.post(
            '/api/hotel/bookings/stripe-webhook/',
            data={},
            format='json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Duplicate webhook
        response2 = self.client.post(
            '/api/hotel/bookings/stripe-webhook/',
            data={},
            format='json',
            HTTP_STRIPE_SIGNATURE='test_signature'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('already processed', response2.data['message'].lower())
    
    @patch('stripe.Webhook.construct_event')
    def test_webhook_invalid_signature(self, mock_construct_event):
        """Test webhook with invalid signature."""
        import stripe
        mock_construct_event.side_effect = (
            stripe.error.SignatureVerificationError('Invalid', 'sig')
        )
        
        response = self.client.post(
            '/api/hotel/bookings/stripe-webhook/',
            data={},
            format='json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('signature', response.data['detail'].lower())


@override_settings(
    STRIPE_SECRET_KEY='sk_test_fake'
)
class VerifyPaymentViewTests(TestCase):
    """Test payment verification endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    @patch('stripe.checkout.Session.retrieve')
    def test_verify_payment_success(self, mock_stripe_retrieve):
        """Test successful payment verification."""
        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_session.amount_total = 40000
        mock_session.currency = 'eur'
        mock_session.customer_email = 'test@example.com'
        mock_session.metadata = {'booking_id': 'BK-2025-TEST01'}
        mock_stripe_retrieve.return_value = mock_session
        
        response = self.client.get(
            '/api/hotel/bookings/BK-2025-TEST01/payment/verify/',
            {'session_id': 'cs_test_123'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment_status'], 'paid')
        self.assertEqual(response.data['amount_total'], 400.00)
    
    def test_verify_payment_missing_session_id(self):
        """Test error when session_id is missing."""
        response = self.client.get(
            '/api/hotel/bookings/BK-2025-TEST01/payment/verify/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('session_id', response.data['detail'].lower())
    
    @patch('stripe.checkout.Session.retrieve')
    def test_verify_payment_stripe_error(self, mock_stripe_retrieve):
        """Test error handling when Stripe API fails."""
        import stripe
        mock_stripe_retrieve.side_effect = stripe.error.StripeError(
            'Session not found'
        )
        
        response = self.client.get(
            '/api/hotel/bookings/BK-2025-TEST01/payment/verify/',
            {'session_id': 'cs_invalid'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
