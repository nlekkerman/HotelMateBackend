#!/usr/bin/env python3
"""
Generate daily tournaments for Killarney Hotel from Oct 27 to Nov 2, 2025
Each day will have a Kids Memory Tournament from 12 PM to 7 PM
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


def create_daily_tournaments():
    """Create daily tournaments from Oct 27 to Nov 2, 2025"""
    try:
        # Get Killarney Hotel (ID 2)
        hotel = Hotel.objects.get(id=2)
        print(f"🏨 Creating tournaments for: {hotel.name}")
        print(f"   Hotel slug: {hotel.slug}")
        
        # Define date range: Oct 27 to Nov 2, 2025
        start_date = datetime(2025, 10, 27)
        end_date = datetime(2025, 11, 2)
        
        current_date = start_date
        tournaments_created = 0
        
        while current_date <= end_date:
            # Format date for tournament name
            date_str = current_date.strftime("%B %d, %Y")
            day_name = current_date.strftime("%A")
            
            tournament_name = f"Kids Memory Challenge - {day_name}"
            tournament_slug = slugify(f"kids-memory-{current_date.strftime('%Y-%m-%d')}")
            
            # Set tournament times (12 PM to 7 PM)
            tournament_start = current_date.replace(hour=12, minute=0, second=0)
            tournament_end = current_date.replace(hour=19, minute=0, second=0)
            
            # Check if tournament already exists
            existing = MemoryGameTournament.objects.filter(
                hotel=hotel,
                slug=tournament_slug
            ).first()
            
            if existing:
                print(f"   ⏭️  Tournament already exists for {date_str}")
                current_date += timedelta(days=1)
                continue
            
            # Create tournament
            tournament = MemoryGameTournament.objects.create(
                name=tournament_name,
                slug=tournament_slug,
                description=f"Daily kids memory tournament for {date_str}. "
                           f"3x4 grid (6 pairs) - Play anonymously!",
                hotel=hotel,
                start_date=tournament_start,
                end_date=tournament_end,
                registration_deadline=tournament_start,  # Same as start time
                status='upcoming' if current_date.date() > datetime.now().date() 
                       else 'active',
                max_participants=999,  # No limit as requested
                min_age=5,
                max_age=99,  # Open to all ages
                first_prize="Hotel Game Room Pass",
                second_prize="Pool Day Pass",
                third_prize="Ice Cream Voucher",
                rules="1. Enter your name and room number\n"
                      "2. Match all 6 pairs of cards (3x4 grid)\n"
                      "3. Fastest time wins!\n"
                      "4. Play as many times as you want"
            )
            
            print(f"   ✅ Created: {tournament_name}")
            print(f"      Date: {date_str}")
            print(f"      Time: 12:00 PM - 7:00 PM")
            print(f"      Slug: {tournament_slug}")
            
            # Generate QR code
            print(f"      🔄 Generating QR code...")
            success = tournament.generate_qr_code()
            
            if success:
                print(f"      ✅ QR code generated: {tournament.qr_code_url}")
                print(f"      🔗 Tournament URL: https://hotelsmates.com/tournaments/{hotel.slug}/{tournament_slug}/play/")
            else:
                print(f"      ❌ Failed to generate QR code")
            
            tournaments_created += 1
            print()
            
            # Move to next day
            current_date += timedelta(days=1)
        
        print(f"🎉 Summary:")
        print(f"   ✅ Tournaments created: {tournaments_created}")
        print(f"   🏨 Hotel: {hotel.name}")
        print(f"   📅 Date range: Oct 27 - Nov 2, 2025")
        print(f"   ⏰ Daily time: 12:00 PM - 7:00 PM")
        print(f"   🎮 Game: Memory Match (6x4 grid)")
        print(f"   👥 Participants: Unlimited")
        
    except Hotel.DoesNotExist:
        print("❌ Killarney Hotel (ID: 2) not found")
    except Exception as e:
        print(f"❌ Error creating tournaments: {e}")


def show_tournament_urls():
    """Show all tournament URLs for easy reference"""
    try:
        hotel = Hotel.objects.get(id=2)
        tournaments = MemoryGameTournament.objects.filter(
            hotel=hotel,
            start_date__date__gte=datetime(2025, 10, 27).date(),
            start_date__date__lte=datetime(2025, 11, 2).date()
        ).order_by('start_date')
        
        print("\n📋 Tournament URLs Reference:")
        print("=" * 80)
        
        for tournament in tournaments:
            date_str = tournament.start_date.strftime("%A, %B %d, %Y")
            url = f"https://hotelsmates.com/tournaments/{hotel.slug}/{tournament.slug}/play/"
            
            print(f"📅 {date_str}")
            print(f"   🎮 {tournament.name}")
            print(f"   🔗 {url}")
            if tournament.qr_code_url:
                print(f"   📱 QR: {tournament.qr_code_url}")
            print()
            
    except Exception as e:
        print(f"❌ Error showing URLs: {e}")


if __name__ == "__main__":
    print("🎮 Daily Tournament Generator")
    print("=" * 50)
    print("Creating daily tournaments for Oct 27 - Nov 2, 2025")
    print()
    
    create_daily_tournaments()
    show_tournament_urls()