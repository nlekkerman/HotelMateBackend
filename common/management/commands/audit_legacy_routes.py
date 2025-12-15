"""
Django Management Command: Legacy Routes Audit
Tests URL resolution for legacy and canonical patterns.
Usage: python manage.py audit_legacy_routes
"""

from django.core.management.base import BaseCommand
from django.urls import resolve
from django.urls.exceptions import Resolver404


class Command(BaseCommand):
    help = 'Audits legacy routes to ensure they return 404 and canonical routes work'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []
        self.hotel_slug = "demo-hotel"
        self.booking_id = "test-booking-123"

    def test_url_resolution(self, url_path, expected_result="NO MATCH"):
        """Test if a URL path resolves or returns 404"""
        try:
            resolved = resolve(url_path)
            result = "RESOLVES"
            view_name = f"{resolved.view_name}" if hasattr(resolved, 'view_name') else str(resolved.func)
            details = f"View: {view_name}, Args: {resolved.args}, Kwargs: {resolved.kwargs}"
        except Resolver404:
            result = "NO MATCH"
            details = "404 - URL pattern not found"
        except Exception as e:
            result = "ERROR"
            details = f"Exception: {str(e)}"
        
        self.test_results.append({
            'url': url_path,
            'expected': expected_result,
            'actual': result,
            'details': details,
            'status': '✅' if result == expected_result else '⚠️'
        })
        
        return result

    def handle(self, *args, **options):
        self.stdout.write("🔍 LEGACY ROUTES AUDIT - Runtime Verification")
        self.stdout.write("=" * 60)
        
        # Test legacy patterns that should return NO MATCH (404)
        self.stdout.write("\n🚫 Testing Legacy Patterns (Expected: NO MATCH)")
        legacy_tests = [
            f"/api/hotel/",
            f"/api/hotel/{self.hotel_slug}/",
            f"/api/hotel/{self.hotel_slug}/page/",
            f"/api/hotel/{self.hotel_slug}/availability/",
            f"/api/hotel/{self.hotel_slug}/pricing/quote/",
            f"/api/hotel/{self.hotel_slug}/bookings/",
            f"/api/hotel/{self.hotel_slug}/bookings/{self.booking_id}/payment/session/",
            f"/api/hotel/{self.hotel_slug}/bookings/{self.booking_id}/payment/verify/",
            f"/api/hotel/bookings/stripe-webhook/",
            f"/api/staff/hotel/{self.hotel_slug}/bookings/",
            f"/api/staff/hotel/{self.hotel_slug}/bookings/{self.booking_id}/assign-room/",
            f"/api/staff/hotel/{self.hotel_slug}/bookings/{self.booking_id}/checkout/",
            f"/api/staff/hotel/{self.hotel_slug}/bookings/{self.booking_id}/party/",
        ]
        
        for url in legacy_tests:
            self.test_url_resolution(url, expected_result="NO MATCH")
        
        # Test canonical patterns that should RESOLVE
        self.stdout.write(f"\n✅ Testing Canonical Patterns (Expected: RESOLVES)")
        canonical_tests = [
            f"/api/public/hotel/{self.hotel_slug}/page/",
            f"/api/public/hotel/{self.hotel_slug}/availability/", 
            f"/api/public/hotel/{self.hotel_slug}/pricing/quote/",
            f"/api/public/hotel/{self.hotel_slug}/bookings/",
            f"/api/public/hotel/{self.hotel_slug}/bookings/{self.booking_id}/payment/session/",
            f"/api/public/hotel/{self.hotel_slug}/bookings/{self.booking_id}/payment/verify/",
            f"/api/public/bookings/stripe-webhook/",
            f"/api/staff/hotel/{self.hotel_slug}/room-bookings/",
            f"/api/staff/hotel/{self.hotel_slug}/room-bookings/{self.booking_id}/assign-room/",
            f"/api/staff/hotel/{self.hotel_slug}/room-bookings/{self.booking_id}/checkout/",
            f"/api/staff/hotel/{self.hotel_slug}/service-bookings/",
            f"/api/guest/hotels/{self.hotel_slug}/",
        ]
        
        for url in canonical_tests:
            self.test_url_resolution(url, expected_result="RESOLVES")

        # Print results
        self.print_results()

    def print_results(self):
        """Print formatted audit results"""
        self.stdout.write("\n📊 AUDIT RESULTS")
        self.stdout.write("=" * 60)
        
        legacy_failed = 0
        canonical_failed = 0
        
        for result in self.test_results:
            status = result['status']
            url = result['url']
            expected = result['expected']
            actual = result['actual']
            details = result['details']
            
            self.stdout.write(f"{status} {url}")
            self.stdout.write(f"   Expected: {expected} | Actual: {actual}")
            if result['status'] == '⚠️':
                self.stdout.write(f"   Details: {details}")
                if expected == "NO MATCH":
                    legacy_failed += 1
                else:
                    canonical_failed += 1
        
        # Summary
        self.stdout.write("\n🎯 SUMMARY")
        self.stdout.write("=" * 60)
        total_legacy = sum(1 for r in self.test_results if r['expected'] == 'NO MATCH')
        total_canonical = sum(1 for r in self.test_results if r['expected'] == 'RESOLVES')
        
        legacy_success = total_legacy - legacy_failed
        canonical_success = total_canonical - canonical_failed
        
        self.stdout.write(f"Legacy Routes (should 404): {legacy_success}/{total_legacy} ✅")
        self.stdout.write(f"Canonical Routes (should resolve): {canonical_success}/{total_canonical} ✅")
        
        if legacy_failed == 0 and canonical_failed == 0:
            self.stdout.write(
                self.style.SUCCESS("\n🎉 AUDIT PASSED: All legacy routes properly disabled, canonical routes work!")
            )
            return True
        else:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️ AUDIT FAILED: {legacy_failed} legacy routes still active, {canonical_failed} canonical routes broken")
            )
            return False