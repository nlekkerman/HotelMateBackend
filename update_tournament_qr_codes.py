#!/usr/bin/env python3
"""
Update QR codes for all tournaments to use correct /play/ URLs
"""
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from entertainment.models import MemoryGameTournament
from datetime import datetime


def update_tournament_qr_codes():
    """Update QR codes for all tournaments to ensure they use /play/ URLs"""
    try:
        tournaments = MemoryGameTournament.objects.filter(
            start_date__date__gte=datetime(2025, 10, 27).date(),
            start_date__date__lte=datetime(2025, 11, 2).date()
        ).order_by('start_date')
        
        print("🔄 Updating Tournament QR Codes")
        print("=" * 50)
        
        updated_count = 0
        
        for tournament in tournaments:
            print(f"📅 {tournament.start_date.strftime('%A, %B %d, %Y')}")
            print(f"   🎮 {tournament.name}")
            
            # Show current QR URL
            if tournament.qr_code_url:
                print(f"   📱 Current QR: {tournament.qr_code_url}")
            else:
                print(f"   📱 No QR code found")
            
            # Generate new QR code
            print(f"   🔄 Regenerating QR code...")
            success = tournament.generate_qr_code()
            
            if success:
                # Show the URL that the QR code points to
                hotel_slug = tournament.hotel.slug
                play_url = f"https://hotelsmates.com/tournaments/{hotel_slug}/{tournament.slug}/play/"
                
                print(f"   ✅ QR code updated: {tournament.qr_code_url}")
                print(f"   🔗 Points to: {play_url}")
                updated_count += 1
            else:
                print(f"   ❌ Failed to generate QR code")
            
            print()
        
        print(f"🎉 QR Code Update Summary:")
        print(f"   ✅ Tournaments updated: {updated_count}")
        print(f"   🔗 All QR codes now point to /play/ URLs")
        
    except Exception as e:
        print(f"❌ Error updating QR codes: {e}")


if __name__ == "__main__":
    update_tournament_qr_codes()