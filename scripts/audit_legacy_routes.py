#!/usr/bin/env python
"""
Legacy Routes Audit Script
Tests URL resolution for legacy and canonical patterns.
Run from project root: python scripts/audit_legacy_routes.py
"""

import os
import sys
import django
from urllib.parse import urlparse
from django.urls import resolve, reverse, NoReverseMatch
from django.urls.exceptions import Resolver404

# Setup Django environment
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

class LegacyRouteAuditor:
    def __init__(self):
        self.test_results = []
        self.hotel_slug = "demo-hotel"  # Use a test slug
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
    
    def run_audit(self):
        """Run comprehensive URL resolution audit"""
        print("🔍 LEGACY ROUTES AUDIT - Runtime Verification")
        print("=" * 60)
        
        # Test legacy patterns that should return NO MATCH (404)
        print("\n🚫 Testing Legacy Patterns (Expected: NO MATCH)")
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
        print(f"\n✅ Testing Canonical Patterns (Expected: RESOLVES)")
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
    
    def print_results(self):
        """Print formatted audit results"""
        print("\n📊 AUDIT RESULTS")
        print("=" * 60)
        
        legacy_failed = 0
        canonical_failed = 0
        
        for result in self.test_results:
            status = result['status']
            url = result['url']
            expected = result['expected']
            actual = result['actual']
            details = result['details']
            
            print(f"{status} {url}")
            print(f"   Expected: {expected} | Actual: {actual}")
            if result['status'] == '⚠️':
                print(f"   Details: {details}")
                if expected == "NO MATCH":
                    legacy_failed += 1
                else:
                    canonical_failed += 1
            print()
        
        # Summary
        print("\n🎯 SUMMARY")
        print("=" * 60)
        total_legacy = sum(1 for r in self.test_results if r['expected'] == 'NO MATCH')
        total_canonical = sum(1 for r in self.test_results if r['expected'] == 'RESOLVES')
        
        legacy_success = total_legacy - legacy_failed
        canonical_success = total_canonical - canonical_failed
        
        print(f"Legacy Routes (should 404): {legacy_success}/{total_legacy} ✅")
        print(f"Canonical Routes (should resolve): {canonical_success}/{total_canonical} ✅")
        
        if legacy_failed == 0 and canonical_failed == 0:
            print("\n🎉 AUDIT PASSED: All legacy routes properly disabled, canonical routes work!")
            return True
        else:
            print(f"\n⚠️ AUDIT FAILED: {legacy_failed} legacy routes still active, {canonical_failed} canonical routes broken")
            return False

if __name__ == "__main__":
    auditor = LegacyRouteAuditor()
    auditor.run_audit()
    success = auditor.print_results()
    sys.exit(0 if success else 1)