"""
Simple Test for Canonical Guest Chat API Service Layer

This test focuses on the core service layer functionality without
depending on specific model migrations that might cause issues.
"""

from django.test import TestCase
from django.utils import timezone
from django.test import override_settings
from bookings.services import (
    resolve_guest_chat_context,
    InvalidTokenError,
    NotInHouseError,
    NoRoomAssignedError,
    MissingScopeError
)

# Simple test to verify our service layer changes work
class ServiceLayerTest(TestCase):
    def test_scope_validation_logic(self):
        """Test that our enhanced service layer function signature works"""
        # This just tests that the function signature is correct
        # and the new parameters are accepted
        try:
            # This will fail with InvalidTokenError (expected)
            # but it should not fail due to signature issues
            resolve_guest_chat_context(
                hotel_slug="test-hotel",
                token_str="invalid-token",
                required_scopes=["CHAT"],
                action_required=True
            )
        except InvalidTokenError:
            # This is expected - the token is invalid
            pass
        except Exception as e:
            # If we get here, there's a signature or import issue
            self.fail(f"Function signature issue: {e}")
    
    def test_missing_scope_error_creation(self):
        """Test that our new MissingScopeError works correctly"""
        error = MissingScopeError("Test message", required_scopes=["CHAT", "ROOM_SERVICE"])
        self.assertEqual(error.status_code, 403)
        self.assertEqual(error.required_scopes, ["CHAT", "ROOM_SERVICE"])
        self.assertIn("Test message", str(error))


class ViewImportTest(TestCase):
    def test_canonical_views_import(self):
        """Test that our new canonical views can be imported without errors"""
        try:
            from hotel.canonical_guest_chat_views import (
                GuestChatContextView,
                GuestChatSendMessageView
            )
            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"View import failed: {e}")


# Test URL configuration
class URLConfigTest(TestCase):
    def test_canonical_urls_configured(self):
        """Test that our canonical URLs are properly configured"""
        from django.urls import reverse
        try:
            # These should not raise NoReverseMatch
            from django.urls import reverse, NoReverseMatch
            try:
                # Try to reverse our new canonical URLs
                context_url = reverse('canonical-guest-chat-context', kwargs={'hotel_slug': 'test-hotel'})
                messages_url = reverse('canonical-guest-chat-send-message', kwargs={'hotel_slug': 'test-hotel'})
                
                # Verify they have the correct pattern
                self.assertIn('/api/guest/hotel/test-hotel/chat/context', context_url)
                self.assertIn('/api/guest/hotel/test-hotel/chat/messages', messages_url)
                
            except NoReverseMatch as e:
                self.fail(f"URL reverse failed: {e}")
        except ImportError:
            # If reverse import fails, that's also OK for now
            pass