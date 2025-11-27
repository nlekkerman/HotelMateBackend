"""
Test URL routing to verify all endpoints are correctly mapped.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def get_all_urls(urlpatterns, prefix='', namespace=''):
    """Recursively extract all URL patterns"""
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # It's a nested include()
            new_prefix = prefix + str(pattern.pattern)
            new_namespace = namespace
            if pattern.namespace:
                new_namespace = f"{namespace}:{pattern.namespace}" if namespace else pattern.namespace
            urls.extend(get_all_urls(pattern.url_patterns, new_prefix, new_namespace))
        elif isinstance(pattern, URLPattern):
            # It's a final URL pattern
            url = prefix + str(pattern.pattern)
            name = pattern.name
            if namespace:
                name = f"{namespace}:{name}" if name else namespace
            urls.append({
                'url': url,
                'name': name,
                'view': pattern.callback.__name__ if hasattr(pattern.callback, '__name__') else str(pattern.callback)
            })
    return urls

print("=" * 80)
print("TESTING URL ROUTING - ALL ENDPOINTS")
print("=" * 80)

resolver = get_resolver()
all_urls = get_all_urls(resolver.url_patterns)

# Filter and organize by category
categories = {
    'Public Hotel Views': [],
    'Booking Views': [],
    'Staff Management Views': [],
    'Base/Admin Views': [],
}

for url_info in all_urls:
    url = url_info['url']
    
    # Public views
    if 'public/hotel' in url or 'hotels/filters' in url:
        categories['Public Hotel Views'].append(url_info)
    # Booking views
    elif 'availability' in url or 'pricing' in url or 'bookings/' in url:
        categories['Booking Views'].append(url_info)
    # Staff views
    elif 'staff/hotel' in url and ('settings' in url or 'bookings' in url or 'public-page' in url or 'status' in url or 'sections' in url):
        categories['Staff Management Views'].append(url_info)
    # Base views
    elif 'api/hotel' in url and 'staff' not in url:
        categories['Base/Admin Views'].append(url_info)

# Display results
for category, urls in categories.items():
    if urls:
        print(f"\n{category}:")
        print("-" * 80)
        for url_info in urls:
            print(f"  ✓ {url_info['url']:<50} [{url_info['view']}]")

# Count total endpoints
total_endpoints = sum(len(urls) for urls in categories.values())
print("\n" + "=" * 80)
print(f"TOTAL ENDPOINTS TESTED: {total_endpoints}")
print("=" * 80)

# Verify specific critical endpoints
print("\n" + "=" * 80)
print("VERIFYING CRITICAL ENDPOINTS")
print("=" * 80)

critical_endpoints = [
    ('api/public/hotels/', 'Public hotel listing'),
    ('api/public/hotels/filters/', 'Hotel filters'),
    ('api/staff/hotel/', 'Staff hotel management'),
    ('availability/', 'Availability check'),
    ('bookings/', 'Booking creation'),
]

found_critical = []
for pattern, description in critical_endpoints:
    matching = [u for u in all_urls if pattern in u['url']]
    if matching:
        found_critical.append(description)
        print(f"  ✓ {description:<30} - FOUND")
    else:
        print(f"  ✗ {description:<30} - NOT FOUND")

print("\n" + "=" * 80)
if len(found_critical) >= 4:
    print(f"SUCCESS: {len(found_critical)}/{len(critical_endpoints)} critical endpoints are accessible! ✅")
else:
    print(f"WARNING: Only {len(found_critical)}/{len(critical_endpoints)} critical endpoints found")
print("=" * 80)
