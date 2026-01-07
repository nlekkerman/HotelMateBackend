#!/usr/bin/env python3
"""
Debug Pusher connectivity and send test messages
Run this from your Django management command or shell
"""

from django.core.management.base import BaseCommand
from pusher import Pusher
from django.conf import settings
import json

class Command(BaseCommand):
    help = 'Debug Pusher and send test messages'

    def add_arguments(self, parser):
        parser.add_argument('--booking-id', type=str, help='Booking ID to test (e.g., BK-2026-0001)')
        parser.add_argument('--hotel-slug', type=str, default='hotel-killarney', help='Hotel slug')
        parser.add_argument('--test-event', action='store_true', help='Send a test event')

    def handle(self, *args, **options):
        booking_id = options.get('booking_id', 'BK-2026-0001')
        hotel_slug = options.get('hotel_slug', 'hotel-killarney')
        
        # Initialize Pusher (adjust based on your settings)
        pusher_client = Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True
        )
        
        self.stdout.write('🔍 Testing Pusher Configuration...')
        self.stdout.write(f'App ID: {settings.PUSHER_APP_ID}')
        self.stdout.write(f'Key: {settings.PUSHER_KEY}')
        self.stdout.write(f'Cluster: {settings.PUSHER_CLUSTER}')
        
        # Test channel name (based on your logs)
        guest_channel = f'private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}'
        self.stdout.write(f'📡 Testing channel: {guest_channel}')
        
        if options.get('test_event'):
            # Send test event
            test_data = {
                'type': 'test_message',
                'message': 'This is a test message from debug command',
                'timestamp': '2026-01-07T11:30:00Z',
                'sender': 'debug_script'
            }
            
            try:
                result = pusher_client.trigger(guest_channel, 'realtime_event', test_data)
                self.stdout.write(self.style.SUCCESS(f'✅ Test event sent successfully: {result}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to send test event: {e}'))
        
        # Test channel info
        try:
            channel_info = pusher_client.channel_info(guest_channel)
            self.stdout.write(f'📊 Channel info: {channel_info}')
        except Exception as e:
            self.stdout.write(f'⚠️  Could not get channel info: {e}')
        
        self.stdout.write('🔍 Debug complete!')