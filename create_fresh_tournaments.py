#!/usr/bin/env python3
"""
Create fresh tournaments for Oct 27 - Nov 2, 2025
Delete old tournaments and create new ones with updated QR codes pointing to dashboard
"""
import os
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from entertainment.models import MemoryGameTournament
from hotel.models import Hotel
from django.utils import timezone
from django.utils.text import slugify


def clean_and_create_tournaments():
    """Delete old tournaments and create fresh ones"""
    try:
        # Get Killarney Hotel (ID 2)
        hotel = Hotel.objects.get(id=2)
        print(f"🏨 Hotel: {hotel.name} ({hotel.slug})")
        
        # Delete ALL existing tournaments for this hotel
        old_count = MemoryGameTournament.objects.filter(hotel=hotel).count()
        MemoryGameTournament.objects.filter(hotel=hotel).delete()
        print(f"🗑️  Deleted {old_count} old tournaments")
        
        # Define date range: Oct 27 to Nov 2, 2025
        start_date = datetime(2025, 10, 27)
        end_date = datetime(2025, 11, 2)
        
        current_date = start_date
        tournaments_created = 0
        
        while current_date <= end_date:
            # Format date for tournament name
            date_str = current_date.strftime("%B %d, %Y")
            day_name = current_date.strftime("%A")
            
            tournament_name = f"Memory Match Daily - {day_name}"
            tournament_slug = slugify(f"memory-daily-{current_date.strftime('%Y-%m-%d')}")
            
            # Set tournament times (12 PM to 7 PM)
            tournament_start = current_date.replace(hour=12, minute=0, second=0)
            tournament_end = current_date.replace(hour=19, minute=0, second=0)
            
            # Determine status based on current date
            now = datetime.now()
            if current_date.date() < now.date():
                status = 'completed'
            elif current_date.date() == now.date():
                status = 'active'
            else:
                status = 'upcoming'
            
            # Create tournament
            tournament = MemoryGameTournament.objects.create(
                name=tournament_name,
                slug=tournament_slug,
                description=f"Daily Memory Match for {date_str}. "
                           f"3x4 grid (6 pairs) - Scan QR to play!",
                hotel=hotel,
                start_date=tournament_start,
                end_date=tournament_end,
                registration_deadline=tournament_start,
                status=status,
                max_participants=999,  # Unlimited
                min_age=5,
                max_age=99,
                first_prize="Hotel Game Room Pass",
                second_prize="Pool Day Pass", 
                third_prize="Ice Cream Voucher",
                rules="1. Scan QR code to access game dashboard\n"
                      "2. Choose Practice or Tournament mode\n"
                      "3. Match all 6 pairs (3x4 grid)\n"
                      "4. Fastest time and fewest moves win!"
            )
            
            print(f"✅ Created: {tournament_name}")
            print(f"   Date: {date_str}")
            print(f"   Status: {status}")
            print(f"   Slug: {tournament_slug}")
            
            # Generate QR code (points to dashboard now)
            print(f"   🔄 Generating QR code...")
            success = tournament.generate_qr_code()
            
            if success:
                dashboard_url = f"https://hotelsmates.com/games/memory-match/?hotel={hotel.slug}"
                print(f"   ✅ QR generated: {tournament.qr_code_url}")
                print(f"   🔗 Dashboard URL: {dashboard_url}")
            else:
                print(f"   ❌ Failed to generate QR code")
            
            tournaments_created += 1
            print()
            
            # Move to next day
            current_date += timedelta(days=1)
        
        print(f"🎉 Tournament Creation Summary:")
        print(f"   🗑️  Old tournaments deleted: {old_count}")
        print(f"   ✅ New tournaments created: {tournaments_created}")
        print(f"   🏨 Hotel: {hotel.name}")
        print(f"   📅 Date range: Oct 27 - Nov 2, 2025")
        print(f"   🎮 Game: Memory Match (3x4 grid)")
        print(f"   🔗 All QR codes point to: /games/memory-match/?hotel={hotel.slug}")
        
    except Hotel.DoesNotExist:
        print("❌ Killarney Hotel (ID: 2) not found")
    except Exception as e:
        print(f"❌ Error: {e}")


def show_new_tournaments():
    """Show all new tournaments"""
    try:
        hotel = Hotel.objects.get(id=2)
        tournaments = MemoryGameTournament.objects.filter(
            hotel=hotel
        ).order_by('start_date')
        
        print("\n📋 New Tournament List:")
        print("=" * 80)
        
        for tournament in tournaments:
            date_str = tournament.start_date.strftime("%A, %B %d, %Y")
            dashboard_url = f"https://hotelsmates.com/games/memory-match/?hotel={hotel.slug}"
            
            print(f"📅 {date_str}")
            print(f"   🎮 {tournament.name} ({tournament.status})")
            print(f"   🔗 Dashboard: {dashboard_url}")
            if tournament.qr_code_url:
                print(f"   📱 QR: {tournament.qr_code_url}")
            print()
            
    except Exception as e:
        print(f"❌ Error showing tournaments: {e}")


if __name__ == "__main__":
    print("🎮 Fresh Tournament Creator")
    print("=" * 50)
    print("Creating new tournaments for Oct 27 - Nov 2, 2025")
    print("All QR codes will point to the game dashboard")
    print()
    
    clean_and_create_tournaments()
    show_new_tournaments()