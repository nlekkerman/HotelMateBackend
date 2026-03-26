"""
Tests for the canonical guest access resolver (common.guest_access).

Ensures both GuestBookingToken and BookingManagementToken resolve
through the same canonical path and that chat/booking-status/portal
endpoints use consistent validation.
"""

import hashlib
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from hotel.models import Hotel, GuestBookingToken, BookingManagementToken, RoomBooking
from rooms.models import Room, RoomType
from chat.models import Conversation

from common.guest_access import (
    resolve_guest_access,
    GuestAccessContext,
    GuestAccessError,
    TokenRequiredError,
    InvalidTokenError,
    MissingScopeError,
    NotInHouseError,
    NotCheckedInError,
    AlreadyCheckedOutError,
    NoRoomAssignedError,
)
from bookings.services import (
    resolve_guest_chat_context,
    # Backward-compat re-exports
    InvalidTokenError as SvcInvalidTokenError,
    NotInHouseError as SvcNotInHouseError,
    NoRoomAssignedError as SvcNoRoomAssignedError,
    MissingScopeError as SvcMissingScopeError,
    hash_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Base test case
# ---------------------------------------------------------------------------

class GuestAccessBaseTestCase(TestCase):
    """Shared setup: hotel, room_type, room, booking, both token types."""

    def setUp(self):
        self.hotel = Hotel.objects.create(name="Test Hotel", slug="test-hotel")

        self.room_type = RoomType.objects.create(
            name="Standard Room", hotel=self.hotel
        )
        self.room = Room.objects.create(
            room_number="101", room_type=self.room_type, hotel=self.hotel
        )

        self.booking = RoomBooking.objects.create(
            booking_id="BK-TESTHTL-2026-0001",
            confirmation_number="CONF-001",
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timedelta(days=3)).date(),
            primary_first_name="Jane",
            primary_last_name="Doe",
            primary_email="jane@example.com",
            adults=2,
            total_amount=300,
            status="CONFIRMED",
            assigned_room=self.room,
            checked_in_at=timezone.now(),
        )

        # --- GuestBookingToken ---
        self.guest_token_raw = "guest-token-abc123"
        self.guest_token = GuestBookingToken.objects.create(
            token_hash=_hash(self.guest_token_raw),
            booking=self.booking,
            hotel=self.hotel,
            status="ACTIVE",
            scopes=["STATUS_READ", "CHAT", "ROOM_SERVICE"],
            expires_at=timezone.now() + timedelta(days=30),
        )

        # --- BookingManagementToken ---
        self.mgmt_token_raw = "mgmt-token-xyz789"
        self.mgmt_token = BookingManagementToken.objects.create(
            token_hash=_hash(self.mgmt_token_raw),
            booking=self.booking,
            expires_at=timezone.now() + timedelta(days=90),
        )


# ===================================================================
# Phase 1: Canonical resolver unit tests
# ===================================================================

class ResolveGuestAccessGuestTokenTest(GuestAccessBaseTestCase):
    """Tests using GuestBookingToken."""

    def test_valid_guest_token(self):
        ctx = resolve_guest_access(self.guest_token_raw, "test-hotel")
        self.assertEqual(ctx.booking.id, self.booking.id)
        self.assertEqual(ctx.token_type, "guest_booking")
        self.assertIn("CHAT", ctx.scopes)

    def test_valid_guest_token_with_scopes(self):
        ctx = resolve_guest_access(
            self.guest_token_raw, "test-hotel", required_scopes=["CHAT"]
        )
        self.assertIn("CHAT", ctx.scopes)

    def test_missing_scope(self):
        self.guest_token.scopes = ["STATUS_READ"]
        self.guest_token.save()
        with self.assertRaises(MissingScopeError) as cm:
            resolve_guest_access(
                self.guest_token_raw, "test-hotel", required_scopes=["CHAT"]
            )
        self.assertIn("CHAT", cm.exception.missing_scopes)

    def test_expired_guest_token(self):
        self.guest_token.expires_at = timezone.now() - timedelta(hours=1)
        self.guest_token.save()
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.guest_token_raw, "test-hotel")

    def test_revoked_guest_token(self):
        self.guest_token.status = "REVOKED"
        self.guest_token.save()
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.guest_token_raw, "test-hotel")

    def test_hotel_slug_mismatch(self):
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.guest_token_raw, "wrong-hotel")

    def test_cancelled_booking(self):
        self.booking.status = "CANCELLED"
        self.booking.save()
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.guest_token_raw, "test-hotel")


class ResolveGuestAccessManagementTokenTest(GuestAccessBaseTestCase):
    """Tests using BookingManagementToken (the token from email links)."""

    def test_valid_management_token(self):
        ctx = resolve_guest_access(self.mgmt_token_raw, "test-hotel")
        self.assertEqual(ctx.booking.id, self.booking.id)
        self.assertEqual(ctx.token_type, "booking_management")
        self.assertIn("CHAT", ctx.scopes)
        self.assertIn("STATUS_READ", ctx.scopes)

    def test_management_token_with_chat_scope(self):
        """Management tokens imply CHAT scope — the core fix."""
        ctx = resolve_guest_access(
            self.mgmt_token_raw, "test-hotel", required_scopes=["CHAT"]
        )
        self.assertIn("CHAT", ctx.scopes)

    def test_management_token_hotel_mismatch(self):
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.mgmt_token_raw, "wrong-hotel")

    def test_management_token_revoked(self):
        self.mgmt_token.revoked_at = timezone.now()
        self.mgmt_token.save()
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.mgmt_token_raw, "test-hotel")

    def test_management_token_cancelled_booking(self):
        self.booking.status = "CANCELLED"
        self.booking.cancelled_at = timezone.now()
        self.booking.save()
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access(self.mgmt_token_raw, "test-hotel")

    def test_guest_token_preferred_over_management(self):
        """When both tokens exist, GuestBookingToken is tried first."""
        # Create a GuestBookingToken with the same raw value as mgmt
        # (unlikely in production but verifies priority)
        GuestBookingToken.objects.create(
            token_hash=_hash(self.mgmt_token_raw),
            booking=self.booking,
            hotel=self.hotel,
            status="ACTIVE",
            scopes=["STATUS_READ"],
            expires_at=timezone.now() + timedelta(days=30),
        )
        ctx = resolve_guest_access(self.mgmt_token_raw, "test-hotel")
        self.assertEqual(ctx.token_type, "guest_booking")


class ResolveGuestAccessEdgeCasesTest(GuestAccessBaseTestCase):
    """Edge cases and error handling."""

    def test_empty_token(self):
        with self.assertRaises(TokenRequiredError):
            resolve_guest_access("", "test-hotel")

    def test_whitespace_token(self):
        with self.assertRaises(TokenRequiredError):
            resolve_guest_access("   ", "test-hotel")

    def test_completely_unknown_token(self):
        with self.assertRaises(InvalidTokenError):
            resolve_guest_access("does-not-exist", "test-hotel")


# ===================================================================
# Phase 2: In-house requirement tests
# ===================================================================

class InHouseRequirementTest(GuestAccessBaseTestCase):

    def test_in_house_succeeds(self):
        ctx = resolve_guest_access(
            self.guest_token_raw, "test-hotel", require_in_house=True
        )
        self.assertTrue(ctx.is_in_house)

    def test_not_checked_in_raises(self):
        self.booking.checked_in_at = None
        self.booking.save()
        with self.assertRaises(NotCheckedInError):
            resolve_guest_access(
                self.guest_token_raw, "test-hotel", require_in_house=True
            )

    def test_already_checked_out_raises(self):
        self.booking.checked_out_at = timezone.now()
        self.booking.save()
        with self.assertRaises(AlreadyCheckedOutError):
            resolve_guest_access(
                self.guest_token_raw, "test-hotel", require_in_house=True
            )

    def test_no_room_assigned_raises(self):
        self.booking.assigned_room = None
        self.booking.save()
        with self.assertRaises(NoRoomAssignedError):
            resolve_guest_access(
                self.guest_token_raw, "test-hotel", require_in_house=True
            )

    def test_not_in_house_error_is_catchable_as_base(self):
        """NotCheckedInError and AlreadyCheckedOutError are subclasses of NotInHouseError."""
        self.booking.checked_in_at = None
        self.booking.save()
        with self.assertRaises(NotInHouseError):
            resolve_guest_access(
                self.guest_token_raw, "test-hotel", require_in_house=True
            )

    def test_management_token_in_house(self):
        """Management token works for in-house check too."""
        ctx = resolve_guest_access(
            self.mgmt_token_raw, "test-hotel", require_in_house=True
        )
        self.assertTrue(ctx.is_in_house)

    def test_management_token_not_checked_in(self):
        self.booking.checked_in_at = None
        self.booking.save()
        with self.assertRaises(NotCheckedInError):
            resolve_guest_access(
                self.mgmt_token_raw, "test-hotel", require_in_house=True
            )


# ===================================================================
# Phase 3: Chat context integration tests
# ===================================================================

class ResolveChatContextGuestTokenTest(GuestAccessBaseTestCase):
    """resolve_guest_chat_context with GuestBookingToken."""

    def test_chat_context_in_house(self):
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug="test-hotel",
            token_str=self.guest_token_raw,
            required_scopes=["CHAT"],
            action_required=True,
        )
        self.assertEqual(booking.id, self.booking.id)
        self.assertEqual(room.id, self.room.id)
        self.assertIsNotNone(conversation)
        self.assertTrue(actions["can_chat"])
        self.assertIsNone(reason)

    def test_chat_context_soft_mode_pre_checkin(self):
        self.booking.checked_in_at = None
        self.booking.save()
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug="test-hotel",
            token_str=self.guest_token_raw,
            required_scopes=["CHAT"],
            action_required=False,
        )
        self.assertFalse(actions["can_chat"])
        self.assertIn("Check-in", reason)

    def test_chat_context_soft_mode_post_checkout(self):
        self.booking.checked_out_at = timezone.now()
        self.booking.save()
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug="test-hotel",
            token_str=self.guest_token_raw,
            required_scopes=["CHAT"],
            action_required=False,
        )
        self.assertFalse(actions["can_chat"])
        self.assertIn("checkout", reason)

    def test_chat_context_soft_mode_no_room(self):
        self.booking.assigned_room = None
        self.booking.save()
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug="test-hotel",
            token_str=self.guest_token_raw,
            required_scopes=["CHAT"],
            action_required=False,
        )
        self.assertFalse(actions["can_chat"])
        self.assertIn("Room assignment", reason)
        self.assertIsNone(conversation)

    def test_invalid_token_raises(self):
        with self.assertRaises(InvalidTokenError):
            resolve_guest_chat_context(
                hotel_slug="test-hotel",
                token_str="not-a-real-token",
                action_required=True,
            )


class ResolveChatContextManagementTokenTest(GuestAccessBaseTestCase):
    """resolve_guest_chat_context with BookingManagementToken — the core fix."""

    def test_chat_context_with_management_token(self):
        """The fundamental fix: management token now works for chat."""
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug="test-hotel",
            token_str=self.mgmt_token_raw,
            required_scopes=["CHAT"],
            action_required=True,
        )
        self.assertEqual(booking.id, self.booking.id)
        self.assertEqual(room.id, self.room.id)
        self.assertIsNotNone(conversation)
        self.assertTrue(actions["can_chat"])

    def test_chat_messages_with_management_token_soft(self):
        """Management token works for message retrieval (soft mode)."""
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug="test-hotel",
            token_str=self.mgmt_token_raw,
            required_scopes=["CHAT"],
            action_required=False,
        )
        self.assertEqual(booking.id, self.booking.id)
        self.assertTrue(actions["can_chat"])


# ===================================================================
# Phase 4: Room reuse isolation test
# ===================================================================

class RoomReuseIsolationTest(GuestAccessBaseTestCase):
    """Ensure a different booking in the same room does not authenticate."""

    def test_different_booking_same_room(self):
        """Token for booking A must not authenticate booking B even if same room."""
        booking_b = RoomBooking.objects.create(
            booking_id="BK-TESTHTL-2026-0002",
            confirmation_number="CONF-002",
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=(timezone.now() + timedelta(days=5)).date(),
            check_out=(timezone.now() + timedelta(days=8)).date(),
            primary_first_name="Bob",
            primary_last_name="Smith",
            primary_email="bob@example.com",
            adults=1,
            total_amount=200,
            status="CONFIRMED",
            assigned_room=self.room,  # same room as booking A
            checked_in_at=timezone.now(),
        )
        # Token for booking_b
        other_raw = "other-booking-token"
        GuestBookingToken.objects.create(
            token_hash=_hash(other_raw),
            booking=booking_b,
            hotel=self.hotel,
            status="ACTIVE",
            scopes=["STATUS_READ", "CHAT"],
            expires_at=timezone.now() + timedelta(days=30),
        )

        # Using booking A's token must return booking A, not B
        ctx = resolve_guest_access(self.guest_token_raw, "test-hotel")
        self.assertEqual(ctx.booking.id, self.booking.id)

        # Using booking B's token must return booking B
        ctx_b = resolve_guest_access(other_raw, "test-hotel")
        self.assertEqual(ctx_b.booking.id, booking_b.id)


# ===================================================================
# Phase 5: Backward-compatibility checks
# ===================================================================

class BackwardCompatibilityTest(TestCase):
    """Ensure re-exported exception names still work for existing imports."""

    def test_exception_re_exports(self):
        self.assertIs(SvcInvalidTokenError, InvalidTokenError)
        self.assertIs(SvcNoRoomAssignedError, NoRoomAssignedError)
        self.assertIs(SvcMissingScopeError, MissingScopeError)
        # NotInHouseError should be the base of NotCheckedInError
        self.assertTrue(issubclass(NotCheckedInError, SvcNotInHouseError))
        self.assertTrue(issubclass(AlreadyCheckedOutError, SvcNotInHouseError))

    def test_hash_token_still_available(self):
        self.assertEqual(hash_token("test"), _hash("test"))
