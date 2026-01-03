#!/usr/bin/env python
"""
Analyze the log patterns to understand token usage
"""

import re

# Log entries from the user's message
log_data = """
2026-01-03T10:01:59.535194+00:00 app[web.1]: [2026-01-03 10:01:59,535] WARNING django.request Unauthorized: /api/guest/hotel/hotel-killarney/chat/context
2026-01-03T10:01:59.535447+00:00 app[web.1]: 10.1.27.19 - - [03/Jan/2026:10:01:59 +0000] "GET /api/guest/hotel/hotel-killarney/chat/context?token=e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0 HTTP/1.1" 401 58
2026-01-03T10:02:05.671153+00:00 app[web.1]: Unauthorized: /api/guest/hotel/hotel-killarney/chat/context
2026-01-03T10:02:05.671468+00:00 app[web.1]: 10.1.27.19 - - [03/Jan/2026:10:02:05 +0000] "GET /api/guest/hotel/hotel-killarney/chat/context?token=e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0 HTTP/1.1" 401 58
2026-01-03T10:02:05.674476+00:00 app[web.1]: Not Found: /api/guest/hotel/hotel-killarney/room-bookings/BK-2026-0001/
2026-01-03T10:02:05.674765+00:00 app[web.1]: 10.1.28.11 - - [03/Jan/2026:10:02:05 +0000] "GET /api/guest/hotel/hotel-killarney/room-bookings/BK-2026-0001/?token=e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0 HTTP/1.1" 404 7474
2026-01-03T10:03:17.578198+00:00 app[web.1]: Unauthorized: /api/guest/hotel/hotel-killarney/chat/context
2026-01-03T10:03:17.578591+00:00 app[web.1]: 10.1.22.179 - - [03/Jan/2026:10:03:17 +0000] "GET /api/guest/hotel/hotel-killarney/chat/context?token=e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0 HTTP/1.1" 401 58
2026-01-03T10:03:17.579926+00:00 app[web.1]: Not Found: /api/guest/hotel/hotel-killarney/room-bookings/BK-2026-0001/
2026-01-03T10:03:17.580237+00:00 app[web.1]: 10.1.27.32 - - [03/Jan/2026:10:03:17 +0000] "GET /api/guest/hotel/hotel-killarney/room-bookings/BK-2026-0001/?token=e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0 HTTP/1.1" 404 7474
"""

def analyze_token_usage():
    print("🔍 Analyzing token usage from logs...")
    print("=" * 60)
    
    # Extract all tokens from logs
    token_pattern = r'token=([A-Za-z0-9_-]+)'
    tokens = re.findall(token_pattern, log_data)
    
    print(f"📋 Unique tokens found: {len(set(tokens))}")
    for token in set(tokens):
        print(f"   Token: {token}")
    
    # Extract endpoints being called
    endpoint_pattern = r'"GET ([^"]+)"'
    endpoints = re.findall(endpoint_pattern, log_data)
    
    print(f"\n📋 Endpoints being called:")
    unique_endpoints = set()
    for endpoint in endpoints:
        if 'token=' in endpoint:
            # Clean up the endpoint
            clean_endpoint = endpoint.split('?')[0]
            unique_endpoints.add(clean_endpoint)
            print(f"   {clean_endpoint}")
    
    print(f"\n📋 Summary:")
    print(f"   - Frontend is using 1 token: e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0")
    print(f"   - For 2 different endpoints:")
    print(f"     1. /api/guest/hotel/hotel-killarney/chat/context (401 Unauthorized)")
    print(f"     2. /api/guest/hotel/hotel-killarney/room-bookings/BK-2026-0001/ (404 Not Found)")
    
    print(f"\n❓ Questions:")
    print(f"   1. Where did the frontend get this token?")
    print(f"   2. Why doesn't it exist in our database?")
    print(f"   3. Is this token from a different environment/database?")
    print(f"   4. Was the database reset but frontend still has old token?")

if __name__ == "__main__":
    analyze_token_usage()