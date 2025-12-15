from django.test import TestCase
from django.urls import reverse, resolve
import re
import os


class GuestZoneNormalizationTests(TestCase):
    """
    Phase 4B regression tests - ensures guest zone maintains hotel_slug normalization
    Reference: PHASE_4B_GUEST_ZONE_HOTEL_SLUG_NORMALIZATION.md
    """
    
    def test_no_slug_patterns_in_guest_urls(self):
        """Verify zero <slug: patterns exist in guest_urls.py"""
        guest_urls_path = os.path.join(os.path.dirname(__file__), '..', 'guest_urls.py')
        with open(guest_urls_path, 'r') as f:
            content = f.read()
        
        # Must have zero <slug: patterns
        slug_patterns = re.findall(r'<slug:', content)
        self.assertEqual(len(slug_patterns), 0, 
                        f"Found forbidden <slug: patterns in guest_urls.py: {slug_patterns}")
        
        # Must have <str:hotel_slug> patterns
        str_hotel_slug_patterns = re.findall(r'<str:hotel_slug>', content)
        self.assertGreater(len(str_hotel_slug_patterns), 0, 
                          "No <str:hotel_slug> patterns found in guest_urls.py")

    def test_guest_url_resolution(self):
        """Verify key guest endpoints resolve correctly with hotel_slug kwarg"""
        test_hotel_slug = 'test-hotel'
        
        # Test key guest endpoints can reverse/resolve
        key_endpoints = [
            'guest-home',
            'guest-rooms', 
            'check-availability',
            'pricing-quote',
            'create-booking'
        ]
        
        for url_name in key_endpoints:
            with self.subTest(url_name=url_name):
                # Test reverse lookup with hotel_slug
                url = reverse(url_name, kwargs={'hotel_slug': test_hotel_slug})
                self.assertIn(test_hotel_slug, url)
                
                # Test resolve lookup
                resolved = resolve(url)
                self.assertEqual(resolved.url_name, url_name)

    def test_no_kwargs_slug_dependency(self):
        """Verify no guest zone views depend on kwargs['slug']"""
        guest_urls_path = os.path.join(os.path.dirname(__file__), '..', 'guest_urls.py')
        with open(guest_urls_path, 'r') as f:
            content = f.read()
        
        # Check for forbidden kwargs["slug"] or kwargs['slug'] usage
        forbidden_patterns = [
            r'kwargs\[.slug.\]',
            r'kwargs\["slug"\]',
            r"kwargs\['slug'\]"
        ]
        
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content)
            self.assertEqual(len(matches), 0, 
                            f"Found forbidden pattern {pattern} in guest_urls.py: {matches}")

# Create your tests here.
