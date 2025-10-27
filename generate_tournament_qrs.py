#!/usr/bin/env python3
"""
Generate QR codes for HotelMate Memory Game Tournaments
Run this script to generate QR codes for all active tournaments
"""
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from entertainment.models import MemoryGameTournament
from hotel.models import Hotel


def generate_qrs_for_hotel(hotel_id=None, hotel_slug=None):
    """Generate QR codes for tournaments in a specific hotel"""
    try:
        if hotel_id:
            hotel = Hotel.objects.get(id=hotel_id)
        elif hotel_slug:
            hotel = Hotel.objects.get(slug=hotel_slug)
        else:
            raise ValueError("Either hotel_id or hotel_slug must be provided")
        
        tournaments = MemoryGameTournament.objects.filter(
            hotel=hotel,
            status__in=['upcoming', 'active']
        ).order_by('-created_at')
        
        print(f"🏨 Processing tournaments for: {hotel.name}")
        print(f"📊 Found {tournaments.count()} tournaments to process")
        
        success_count = 0
        error_count = 0
        
        for tournament in tournaments:
            try:
                # Check if QR code already exists
                if tournament.qr_code_url:
                    print(f"⏭️  Skipping {tournament.name} (QR exists)")
                    continue
                
                print(f"🔄 Generating QR code for: {tournament.name}")
                success = tournament.generate_qr_code()
                
                if success:
                    print(f"✅ Generated QR code for: {tournament.name}")
                    print(f"   URL: {tournament.qr_code_url}")
                    success_count += 1
                else:
                    print(f"❌ Failed QR generation: {tournament.name}")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Error generating QR code for {tournament.name}: {e}")
                error_count += 1
        
        print(f"\n📈 Summary for {hotel.name}:")
        print(f"   ✅ Successfully generated: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        return success_count, error_count
        
    except Hotel.DoesNotExist:
        print(f"❌ Hotel not found with ID: {hotel_id} or slug: {hotel_slug}")
        return 0, 1
    except Exception as e:
        print(f"❌ Error processing hotel: {e}")
        return 0, 1


def generate_qrs_for_all_hotels():
    """Generate QR codes for tournaments in all hotels"""
    hotels = Hotel.objects.all().order_by('name')
    total_success = 0
    total_errors = 0
    
    print(f"🌍 Processing tournaments for all hotels ({hotels.count()} hotels)")
    print("=" * 60)
    
    for hotel in hotels:
        success, errors = generate_qrs_for_hotel(hotel_id=hotel.id)
        total_success += success
        total_errors += errors
        print("-" * 40)
    
    print("\n🎯 FINAL SUMMARY:")
    print(f"   ✅ Total QR codes generated: {total_success}")
    print(f"   ❌ Total errors: {total_errors}")
    print(f"   🏨 Hotels processed: {hotels.count()}")


def list_tournaments():
    """List all tournaments and their QR code status"""
    tournaments = MemoryGameTournament.objects.all().order_by(
        'hotel__name', '-created_at'
    )
    
    print("📋 Tournament QR Code Status Report")
    print("=" * 80)
    
    current_hotel = None
    for tournament in tournaments:
        if current_hotel != tournament.hotel.name:
            current_hotel = tournament.hotel.name
            print(f"\n🏨 {current_hotel}")
            print("-" * 60)
        
        qr_status = "✅ Generated" if tournament.qr_code_url else "❌ Missing"
        status_emoji = {
            'upcoming': '⏳',
            'active': '🔥',
            'completed': '✅',
            'cancelled': '❌'
        }.get(tournament.status, '❓')
        
        print(f"   {status_emoji} {tournament.name}")
        print(f"      Status: {tournament.status} | QR Code: {qr_status}")
        print(f"      Dates: {tournament.start_date.strftime('%m/%d/%Y')} - {tournament.end_date.strftime('%m/%d/%Y')}")
        if tournament.qr_code_url:
            print(f"      QR URL: {tournament.qr_code_url}")
        print()


def regenerate_tournament_qr(tournament_id):
    """Regenerate QR code for a specific tournament"""
    try:
        tournament = MemoryGameTournament.objects.get(id=tournament_id)
        print(f"🔄 Regenerating QR code for: {tournament.name}")
        
        success = tournament.generate_qr_code()
        
        if success:
            print(f"✅ Successfully regenerated QR code")
            print(f"   URL: {tournament.qr_code_url}")
            print(f"   Tournament URL: https://hotelsmates.com/tournaments/{tournament.hotel.slug}/{tournament.slug}/register/")
        else:
            print(f"❌ Failed to regenerate QR code")
            
    except MemoryGameTournament.DoesNotExist:
        print(f"❌ Tournament with ID {tournament_id} not found")
    except Exception as e:
        print(f"❌ Error regenerating QR code: {e}")


def main():
    """Main function with menu options"""
    print("🎮 HotelMate Tournament QR Code Generator")
    print("=========================================")
    print("1. Generate QR codes for all tournaments")
    print("2. Generate QR codes for specific hotel (by ID)")
    print("3. Generate QR codes for specific hotel (by slug)")
    print("4. List all tournaments and QR status")
    print("5. Regenerate QR code for specific tournament")
    print("6. Exit")
    
    choice = input("\nSelect an option (1-6): ").strip()
    
    if choice == '1':
        generate_qrs_for_all_hotels()
    elif choice == '2':
        hotel_id = input("Enter hotel ID: ").strip()
        try:
            generate_qrs_for_hotel(hotel_id=int(hotel_id))
        except ValueError:
            print("❌ Invalid hotel ID")
    elif choice == '3':
        hotel_slug = input("Enter hotel slug: ").strip()
        generate_qrs_for_hotel(hotel_slug=hotel_slug)
    elif choice == '4':
        list_tournaments()
    elif choice == '5':
        tournament_id = input("Enter tournament ID: ").strip()
        try:
            regenerate_tournament_qr(int(tournament_id))
        except ValueError:
            print("❌ Invalid tournament ID")
    elif choice == '6':
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid option")


if __name__ == "__main__":
    main()