"""
Test URL Configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.urls import get_resolver

print("\n" + "="*70)
print("CHECKING URL CONFIGURATION")
print("="*70)

# Get the URL resolver
resolver = get_resolver()

# Get all URL patterns
patterns = resolver.url_patterns

print(f"\nTotal URL patterns: {len(patterns)}")

# Look for entertainment URLs
entertainment_found = False
for pattern in patterns:
    pattern_str = str(pattern.pattern)
    if 'entertainment' in pattern_str:
        entertainment_found = True
        print(f"\n✅ Entertainment URL found: {pattern_str}")
        
        # Try to get nested patterns
        if hasattr(pattern, 'url_patterns'):
            print(f"   Nested patterns: {len(pattern.url_patterns)}")
            for nested in pattern.url_patterns[:10]:
                print(f"     - {nested.pattern}")

if not entertainment_found:
    print("\n❌ Entertainment URLs NOT found in URL configuration!")
    print("\nAll app URLs:")
    for pattern in patterns:
        pattern_str = str(pattern.pattern)
        if 'api/' in pattern_str:
            print(f"  - {pattern_str}")
