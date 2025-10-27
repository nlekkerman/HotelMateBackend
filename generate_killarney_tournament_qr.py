#!/usr/bin/env python3
"""
Quick script to generate QR code for Killarney Hotel tournaments
Usage: python generate_killarney_tournament_qr.py
"""
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from entertainment.models import MemoryGameTournament
from hotel.models import Hotel


def generate_killarney_tournament_qr():
    """Generate QR codes for Killarney Hotel tournaments"""
    try:
        # Get Killarney Hotel (ID 2 as mentioned in previous context)
        hotel = Hotel.objects.get(id=2)
        print(f"🏨 Processing tournaments for: {hotel.name}")
        
        # Get active/upcoming tournaments
        tournaments = MemoryGameTournament.objects.filter(
            hotel=hotel,
            status__in=['upcoming', 'active']
        )
        
        if not tournaments.exists():
            print("❌ No active tournaments found for Killarney Hotel")
            print("💡 Create a tournament first using the admin interface")
            return
        
        print(f"📊 Found {tournaments.count()} tournaments")
        
        for tournament in tournaments:
            print(f"\n🎮 Processing: {tournament.name}")
            print(f"   Status: {tournament.status}")
            print(f"   Difficulty: {tournament.difficulty}")
            
            # Generate QR code
            if tournament.qr_code_url:
                print("   ⏭️  QR code already exists!")
                print(f"   🔗 URL: {tournament.qr_code_url}")
            else:
                print("   🔄 Generating new QR code...")
                success = tournament.generate_qr_code()
                
                if success:
                    print("   ✅ QR code generated successfully!")
                    print(f"   🔗 URL: {tournament.qr_code_url}")
                else:
                    print("   ❌ Failed to generate QR code")
            
            # Show the tournament URL that the QR code points to
            tournament_url = (
                f"https://hotelsmates.com/tournaments/"
                f"{hotel.slug}/{tournament.slug}/register/"
            )
            print(f"   📱 Tournament URL: {tournament_url}")
        
        print("\n🎉 Processing complete!")
        
    except Hotel.DoesNotExist:
        print("❌ Killarney Hotel (ID: 2) not found")
        print("💡 Make sure the hotel exists in the database")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    generate_killarney_tournament_qr()