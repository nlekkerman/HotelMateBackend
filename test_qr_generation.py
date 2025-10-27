#!/usr/bin/env python3
"""
Test QR code generation for tournaments
"""
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from entertainment.models import MemoryGameTournament
from datetime import datetime


def test_qr_generation():
    """Test QR code generation for existing tournaments"""
    try:
        tournaments = MemoryGameTournament.objects.filter(
            start_date__date__gte=datetime(2025, 10, 27).date(),
            start_date__date__lte=datetime(2025, 11, 2).date()
        ).order_by('start_date')[:3]  # Test first 3
        
        print("QR Code Generation Test")
        print("=" * 40)
        
        for tournament in tournaments:
            print(f"Tournament: {tournament.name}")
            print(f"  Current QR: {tournament.qr_code_url or 'None'}")
            
            # Generate QR code
            success = tournament.generate_qr_code()
            
            if success:
                hotel_slug = tournament.hotel.slug
                play_url = f"https://hotelsmates.com/tournaments/{hotel_slug}/{tournament.slug}/play/"
                print(f"  ✓ New QR: {tournament.qr_code_url}")
                print(f"  ✓ Play URL: {play_url}")
            else:
                print(f"  ✗ Failed to generate QR")
            print()
        
        print("QR Code generation test complete!")
        
    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    test_qr_generation()