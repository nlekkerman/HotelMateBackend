import django
django.setup()
from django.urls import resolve
from django.urls.exceptions import Resolver404

for url in ['/api/hotel/staff/rooms/', '/api/hotel/staff/room-types/']:
    try:
        m = resolve(url)
        print(f'FAIL: {url} resolved to {m}')
    except Resolver404:
        print(f'OK 404: {url}')
